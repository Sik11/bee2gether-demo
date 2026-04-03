from __future__ import annotations

import asyncio
import base64
from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
import json
import logging
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote, urlparse
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
import requests

from backend.config import get_settings
from backend.repository import MemoryRepository, MongoRepository


settings = get_settings()
repository = (
    MemoryRepository()
    if settings.use_memory_db
    else MongoRepository(settings.mongodb_uri, settings.database_name)
)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
EVENT_RETENTION_DAYS = 7

app = FastAPI(title="Bee2Gether API")
api_router = APIRouter(prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.frontend_origin == "*" else [settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RealtimeManager:
    def __init__(self) -> None:
        self.user_connections: dict[str, set[WebSocket]] = {}
        self.socket_users: dict[WebSocket, str] = {}
        self.channel_connections: dict[str, set[WebSocket]] = {}
        self.socket_channels: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

    async def disconnect(self, websocket: WebSocket) -> None:
        user_id = self.socket_users.pop(websocket, None)
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                self.user_connections.pop(user_id, None)

        for channel in self.socket_channels.pop(websocket, set()):
            listeners = self.channel_connections.get(channel)
            if listeners:
                listeners.discard(websocket)
                if not listeners:
                    self.channel_connections.pop(channel, None)

    async def identify(self, websocket: WebSocket, payload: dict[str, Any]) -> dict[str, Any]:
        user = _lookup_user(payload)
        if user is None:
            raise HTTPException(status_code=400, detail="User not found.")

        previous_user_id = self.socket_users.get(websocket)
        if previous_user_id and previous_user_id in self.user_connections:
            self.user_connections[previous_user_id].discard(websocket)
            if not self.user_connections[previous_user_id]:
                self.user_connections.pop(previous_user_id, None)

        self.socket_users[websocket] = user["id"]
        self.user_connections.setdefault(user["id"], set()).add(websocket)
        return user

    async def subscribe(self, websocket: WebSocket, channel: str) -> None:
        if not channel:
            return
        self.socket_channels.setdefault(websocket, set()).add(channel)
        self.channel_connections.setdefault(channel, set()).add(websocket)

    async def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        listeners = self.channel_connections.get(channel)
        if listeners:
            listeners.discard(websocket)
            if not listeners:
                self.channel_connections.pop(channel, None)
        self.socket_channels.get(websocket, set()).discard(channel)

    async def send(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        try:
            await websocket.send_json(message)
        except Exception:
            await self.disconnect(websocket)

    async def emit_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        for websocket in list(self.user_connections.get(user_id, set())):
            await self.send(websocket, message)

    async def emit_to_channel(self, channel: str, message: dict[str, Any]) -> None:
        for websocket in list(self.channel_connections.get(channel, set())):
            await self.send(websocket, message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        all_sockets = {
            websocket
            for websockets in self.user_connections.values()
            for websocket in websockets
        }
        for websocket in list(all_sockets):
            await self.send(websocket, message)


realtime_manager = RealtimeManager()


def _json_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"result": False, "msg": message}, status_code=status_code)


def _user_response(user: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(user)
    payload.pop("passwordHash", None)
    payload.pop("password", None)
    return payload


def _event_response(event: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(event)
    payload["status"] = _event_status(payload)
    if payload["status"] == "ended":
        payload["ongoing"] = False
    return payload


def _group_response(group: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(group)
    member_ids = payload.get("memberIds")
    if not isinstance(member_ids, list) or not member_ids:
        group_id = str(payload.get("id", ""))
        member_ids = repository.list_user_ids_for_group(group_id) if group_id else []
        payload["memberIds"] = member_ids

    payload["memberCount"] = len(member_ids)
    payload["upcomingEventCount"] = len(payload.get("events", []))
    return payload


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_pagination_value(value: Any, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def _pagination_from_mapping(mapping: Any, *, default_limit: int = 5) -> tuple[int, int]:
    offset = _parse_pagination_value(getattr(mapping, "get", lambda *_: None)("offset"), 0)
    limit = _parse_pagination_value(getattr(mapping, "get", lambda *_: None)("limit"), default_limit, minimum=1, maximum=50)
    return offset, limit


def _slice_items(items: list[Any], offset: int, limit: int) -> tuple[list[Any], int]:
    total = len(items)
    return items[offset: offset + limit], total


def _append_notification(
    user_id: str,
    *,
    notification_type: str,
    title: str,
    body: str,
    actor_id: str | None = None,
    actor_username: str | None = None,
    event_id: str | None = None,
    group_id: str | None = None,
) -> None:
    repository.append_user_notification(
        user_id,
        {
            "id": str(uuid4()),
            "type": notification_type,
            "title": title,
            "body": body,
            "read": False,
            "createdAt": _now_iso(),
            "actorId": actor_id,
            "actorUsername": actor_username,
            "eventId": event_id,
            "groupId": group_id,
        },
    )


def _comment_response(comment: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(comment)


def _message_response(message: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(message)


def _notification_response(notification: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(notification)


async def _emit_notifications_state(user_id: str) -> None:
    user_payload = repository.get_user_fields(user_id, ["notifications"])
    if user_payload is None:
        return
    notifications = [_notification_response(item) for item in user_payload.get("notifications", [])]
    await realtime_manager.emit_to_user(
        user_id,
        {
            "type": "notifications.updated",
            "userId": user_id,
            "notifications": notifications,
            "unreadCount": sum(1 for item in notifications if not item.get("read")),
        },
    )


async def _emit_notifications_state_many(user_ids: list[str]) -> None:
    await asyncio.gather(*(_emit_notifications_state(user_id) for user_id in user_ids))


def _schedule_notifications_refresh(user_ids: list[str] | set[str] | tuple[str, ...]) -> None:
    unique_user_ids = [user_id for user_id in dict.fromkeys(str(user_id) for user_id in user_ids if user_id)]
    if not unique_user_ids:
        return
    asyncio.create_task(_emit_notifications_state_many(unique_user_ids))


def _attendees_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": event["id"],
        "attendees": list(event.get("attendees", [])),
        "attendeeCount": len(event.get("attendees", [])),
    }


async def _emit_event_attendance_update(event: dict[str, Any]) -> None:
    payload = {
        "type": "event.attendance.updated",
        **_attendees_payload(event),
    }
    await realtime_manager.emit_to_channel(f"event:{event['id']}", payload)
    if event.get("userId"):
        await realtime_manager.emit_to_user(event["userId"], payload)


async def _emit_event_comment_created(event: dict[str, Any], comment: dict[str, Any]) -> None:
    payload = {
        "type": "event.comment.created",
        "eventId": event["id"],
        "comment": _comment_response(comment),
    }
    await realtime_manager.emit_to_channel(f"event:{event['id']}", payload)
    if event.get("userId"):
        await realtime_manager.emit_to_user(event["userId"], payload)


async def _emit_event_comment_deleted(event_id: str, comment_id: str, owner_user_id: str | None = None) -> None:
    payload = {
        "type": "event.comment.deleted",
        "eventId": event_id,
        "commentId": comment_id,
    }
    await realtime_manager.emit_to_channel(f"event:{event_id}", payload)
    if owner_user_id:
        await realtime_manager.emit_to_user(owner_user_id, payload)


async def _emit_group_chat_message(group_id: str, message: dict[str, Any]) -> None:
    await realtime_manager.emit_to_channel(
        f"group:{group_id}",
        {
            "type": "group.chat.message.created",
            "groupId": group_id,
            "message": _message_response(message),
        },
    )


async def _emit_group_updated(group: dict[str, Any], *, affected_user_ids: list[str] | None = None) -> None:
    payload = {
        "type": "group.updated",
        "group": _group_response(group),
    }
    await realtime_manager.broadcast(payload)

    membership_payload = {
        "type": "group.membership.updated",
        "group": _group_response(group),
    }
    for user_id in affected_user_ids or []:
        await realtime_manager.emit_to_user(user_id, membership_payload)


@api_router.get("/health")
async def health_check() -> dict[str, Any]:
    return {
        "result": True,
        "status": "ok",
        "database": "memory" if settings.use_memory_db else "mongo",
    }


@api_router.websocket("/realtime")
async def realtime_socket(websocket: WebSocket) -> None:
    await realtime_manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            message_type = str(message.get("type", "")).strip()
            payload = message.get("payload") or {}

            if message_type == "auth.identify":
                try:
                    user = await realtime_manager.identify(websocket, payload)
                except HTTPException as error:
                    await realtime_manager.send(
                        websocket,
                        {"type": "error", "message": str(error.detail), "statusCode": error.status_code},
                    )
                    continue
                await realtime_manager.send(
                    websocket,
                    {
                        "type": "auth.identified",
                        "userId": user["id"],
                        "username": user["username"],
                    },
                )
                continue

            if message_type == "subscribe":
                channel = str(message.get("channel", "")).strip()
                await realtime_manager.subscribe(websocket, channel)
                continue

            if message_type == "unsubscribe":
                channel = str(message.get("channel", "")).strip()
                await realtime_manager.unsubscribe(websocket, channel)
                continue
    except WebSocketDisconnect:
        await realtime_manager.disconnect(websocket)


def _lookup_user(payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("userId"):
        return repository.get_user_by_id(payload["userId"])
    if payload.get("username"):
        return repository.get_user_by_username(payload["username"])
    if payload.get("guestSessionId"):
        return repository.get_user_by_guest_session(str(payload["guestSessionId"]))
    return None


def _lookup_user_id(payload: dict[str, Any]) -> str | None:
    if payload.get("userId"):
        return str(payload["userId"])
    user = _lookup_user(payload)
    if user:
        return str(user["id"])
    return None


def _require_user(payload: dict[str, Any]) -> dict[str, Any]:
    user = _lookup_user(payload)
    if user is None:
        raise HTTPException(status_code=400, detail="User not found.")
    return user


def _require_event(event_id: str) -> dict[str, Any]:
    event = repository.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=400, detail="Event not found")
    return event


def _require_group(group_id: str) -> dict[str, Any]:
    group = repository.get_group_by_id(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


def _guest_username(guest_session_id: str) -> str:
    base = f"guest-{guest_session_id.replace('-', '')[:6].lower() or uuid4().hex[:6]}"
    candidate = base
    suffix = 1
    while True:
        existing = repository.get_user_by_username(candidate)
        if existing is None or existing.get("guestSessionId") == guest_session_id:
            return candidate
        suffix += 1
        candidate = f"{base}-{suffix}"


def _replace_group_event(group_id: str, event: dict[str, Any]) -> None:
    group = repository.get_group_by_id(group_id)
    if group is None:
        return
    group_events = []
    replaced = False
    for existing in group.get("events", []):
        if existing.get("id") == event["id"]:
            group_events.append(_event_response(event))
            replaced = True
        else:
            group_events.append(existing)
    if not replaced:
        group_events.append(_event_response(event))
    group["events"] = group_events
    repository.update_group(group)


def _remove_group_event(group_id: str, event_id: str) -> None:
    group = repository.get_group_by_id(group_id)
    if group is None:
        return
    group["events"] = [event for event in group.get("events", []) if event.get("id") != event_id]
    repository.update_group(group)


def _event_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.max, tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if not raw:
        return None
    try:
        if len(raw) == 10:
            return datetime.combine(date.fromisoformat(raw), time.max, tzinfo=timezone.utc)
        normalised = raw.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalised)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _event_status(event: dict[str, Any], now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    event_at = _event_datetime(event.get("time"))
    if event_at and event_at < now:
        return "ended"
    if event.get("ongoing") is False:
        return "ended"
    return "upcoming"


def _event_is_past_retention(event: dict[str, Any], now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    event_at = _event_datetime(event.get("time"))
    if event_at is None:
        return False
    return event_at < (now - timedelta(days=EVENT_RETENTION_DAYS))


def _delete_supabase_images(image_urls: list[str]) -> None:
    if not settings.supabase_url or not settings.supabase_secret_key or not image_urls:
        return

    bucket_prefix = f"/storage/v1/object/public/{settings.supabase_bucket}/"
    object_paths: list[str] = []
    for image_url in image_urls:
        if not isinstance(image_url, str) or not image_url.startswith(settings.supabase_url):
            continue
        parsed = urlparse(image_url)
        if bucket_prefix not in parsed.path:
            continue
        object_path = parsed.path.split(bucket_prefix, 1)[1]
        if object_path:
            object_paths.append(object_path)

    if not object_paths:
        return

    try:
        requests.delete(
            f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{quote(settings.supabase_bucket, safe='')}",
            headers={
                "Authorization": f"Bearer {settings.supabase_secret_key}",
                "apikey": settings.supabase_secret_key,
                "Content-Type": "application/json",
            },
            json={"prefixes": object_paths},
            timeout=20,
        )
    except requests.RequestException:
        logging.warning("Failed to delete Supabase images for expired event", exc_info=True)


def _delete_event_and_references(event: dict[str, Any]) -> None:
    event_id = str(event["id"])
    repository.delete_event(event_id)

    for user in repository.list_users():
        if event_id in user.get("eventsAttending", []):
            user["eventsAttending"] = [item for item in user.get("eventsAttending", []) if item != event_id]
        if event_id in user.get("savedEvents", []):
            user["savedEvents"] = [item for item in user.get("savedEvents", []) if item != event_id]
        if user.get("notifications"):
            user["notifications"] = [
                item for item in user["notifications"] if item.get("eventId") != event_id
            ]
        repository.update_user(user)

    if event.get("groupId"):
        _remove_group_event(str(event["groupId"]), event_id)

    _delete_supabase_images(list(event.get("eventImg(s)", [])))


def _cleanup_expired_events() -> None:
    now = datetime.now(timezone.utc)
    for event in repository.list_events():
        status = _event_status(event, now)
        if status == "ended" and event.get("ongoing") is not False:
            event["ongoing"] = False
            repository.update_event(event)
            if event.get("groupId"):
                _replace_group_event(event["groupId"], event)
        if _event_is_past_retention(event, now):
            _delete_event_and_references(event)


def _coerce_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=500, detail=f"Invalid {field_name} format") from error


def _sanitize_filename(filename: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name)
    return safe.strip("-") or f"upload-{uuid4().hex}"


def _ics_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _ics_datetime(value: Any) -> str:
    event_at = _event_datetime(value) or datetime.now(timezone.utc)
    return event_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _build_ics_calendar(events_to_export: list[dict[str, Any]]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Bee2Gether//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for event in events_to_export:
        description = event.get("description") or ""
        location = f"{event.get('lat', '')},{event.get('long', '')}"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event['id']}@bee2gether",
                f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{_ics_datetime(event.get('startTime') or event.get('time'))}",
                f"SUMMARY:{_ics_escape(event.get('name', 'Bee2Gether Event'))}",
                f"DESCRIPTION:{_ics_escape(description)}",
                f"LOCATION:{_ics_escape(location)}",
            ]
        )
        if event.get("endTime"):
            lines.append(f"DTEND:{_ics_datetime(event.get('endTime'))}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def _get_frontend_file(relative_path: str) -> Path | None:
    if not FRONTEND_DIST.exists():
        return None
    candidate = (FRONTEND_DIST / relative_path.lstrip("/")).resolve()
    try:
        candidate.relative_to(FRONTEND_DIST.resolve())
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


def _build_inline_image_url(content_type: str, data: bytes) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def _upload_to_supabase(event_id: str, upload: UploadFile, file_bytes: bytes) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    object_name = f"{event_id}/{timestamp}-{uuid4().hex}-{_sanitize_filename(upload.filename or 'image')}"
    upload_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/"
        f"{quote(settings.supabase_bucket, safe='')}/{quote(object_name, safe='/')}"
    )
    response = requests.post(
        upload_url,
        headers={
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "apikey": settings.supabase_secret_key,
            "x-upsert": "true",
            "Content-Type": upload.content_type or "application/octet-stream",
        },
        data=file_bytes,
        timeout=20,
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=500, detail=f"Supabase upload failed: {response.text}")
    return (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
        f"{quote(settings.supabase_bucket, safe='')}/{quote(object_name, safe='/')}"
    )


def _store_image(event_id: str, upload: UploadFile, file_bytes: bytes) -> str:
    if settings.supabase_url and settings.supabase_secret_key:
        return _upload_to_supabase(event_id, upload, file_bytes)
    return _build_inline_image_url(upload.content_type or "application/octet-stream", file_bytes)


@api_router.get("/health")
def healthcheck() -> dict[str, Any]:
    return {
        "result": True,
        "storage": "memory" if settings.use_memory_db else "mongo",
        "imageStorage": "supabase" if settings.supabase_url and settings.supabase_secret_key else "inline",
    }


@app.get("/", include_in_schema=False)
async def serve_frontend_index() -> FileResponse:
    index_file = _get_frontend_file("index.html")
    if index_file is None:
        raise HTTPException(status_code=404, detail="Frontend build not found")
    return FileResponse(index_file)


@api_router.api_route("/createUser", methods=["PUT"])
async def create_user(request: Request) -> JSONResponse:
    payload = await request.json()
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    if len(username) < 4 or len(username) > 14:
        return _json_error("Username less than 4 characters or more than 14 characters", 400)
    if len(password) < 10 or len(password) > 20:
        return _json_error("Password less than 10 characters or more than 20 characters", 400)
    if repository.get_user_by_username(username):
        return _json_error("Username already exists", 400)

    user_id = str(uuid4())
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    repository.create_user(
        {
            "id": user_id,
            "username": username,
            "passwordHash": password_hash,
            "eventsAttending": [],
            "groupsMember": [],
            "savedEvents": [],
            "notifications": [],
        }
    )
    return JSONResponse({"result": True, "msg": "OK", "userId": user_id})


@api_router.api_route("/loginUser", methods=["POST"])
async def login_user(request: Request) -> JSONResponse:
    payload = await request.json()
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    user = repository.get_user_by_username(username)
    if user is None:
        return _json_error("Username or password incorrect", 400)

    password_hash = user.get("passwordHash")
    password_matches = False
    if password_hash:
        password_matches = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    elif user.get("password"):
        password_matches = user["password"] == password
        if password_matches:
            user["passwordHash"] = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user.pop("password", None)
            repository.update_user(user)

    if not password_matches:
        return _json_error("Username or password incorrect", 400)
    return JSONResponse({"result": True, "msg": "OK", "userId": user["id"]})


@api_router.api_route("/continueAsGuest", methods=["POST"])
async def continue_as_guest(request: Request) -> JSONResponse:
    payload = await request.json()
    guest_session_id = str(payload.get("guestSessionId", "")).strip()
    if not guest_session_id:
        return _json_error("guestSessionId is required", 400)

    existing_user = repository.get_user_by_guest_session(guest_session_id)
    if existing_user is not None:
        return JSONResponse(
            {
                "result": True,
                "msg": "OK",
                "userId": existing_user["id"],
                "username": existing_user["username"],
                "isGuest": True,
            }
        )

    user_id = str(uuid4())
    username = _guest_username(guest_session_id)
    repository.create_user(
        {
            "id": user_id,
            "username": username,
            "eventsAttending": [],
            "groupsMember": [],
            "savedEvents": [],
            "notifications": [],
            "isGuest": True,
            "guestSessionId": guest_session_id,
        }
    )
    return JSONResponse({"result": True, "msg": "OK", "userId": user_id, "username": username, "isGuest": True})


@api_router.api_route("/getUserInfo", methods=["POST"])
async def get_user_info(request: Request) -> JSONResponse:
    payload = await request.json()
    username = payload.get("username")
    if not username:
        return _json_error("Username not found", 400)
    user = repository.get_user_by_username(str(username))
    if user is None:
        return _json_error("User not found", 400)
    return JSONResponse({"result": True, "user": _user_response(user)})


@api_router.api_route("/createGroup", methods=["POST"])
async def create_group(request: Request) -> JSONResponse:
    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    description = str(payload.get("description", "")).strip()
    user_id = str(payload.get("userId", "")).strip()

    if not name or not user_id:
        return _json_error("Group name and userId are required", 400)
    if repository.get_group_by_name(name):
        return _json_error("Group name already exists", 400)

    group_id = str(uuid4())
    group = {
        "id": group_id,
        "name": name,
        "description": description,
        "userId": user_id,
        "events": [],
        "messages": [],
    }
    repository.create_group(group)

    creator = repository.get_user_by_id(user_id)
    if creator:
        creator.setdefault("groupsMember", [])
        if group_id not in creator["groupsMember"]:
            creator["groupsMember"].append(group_id)
            repository.update_user(creator)

    await _emit_group_updated(group, affected_user_ids=[user_id])

    return JSONResponse({"result": True, "msg": "Group created successfully", "groupId": group_id})


@api_router.api_route("/getAllGroups", methods=["GET"])
def get_all_groups(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    offset, limit = _pagination_from_mapping(request.query_params)
    groups = [_group_response(group) for group in repository.list_groups()]
    groups, total = _slice_items(groups, offset, limit)
    for group in groups:
        group["events"] = [_event_response(event) for event in group.get("events", [])]
    if not groups:
        return JSONResponse({"result": True, "msg": "No groups found", "groups": [], "total": total, "offset": offset, "limit": limit})
    return JSONResponse({"result": True, "msg": "Groups retrieved successfully", "groups": groups, "total": total, "offset": offset, "limit": limit})


@api_router.api_route("/joinGroup", methods=["POST"])
async def join_group(request: Request) -> JSONResponse:
    payload = await request.json()
    user_id = payload.get("userId")
    group_id = payload.get("groupId")
    if not user_id or not group_id:
        return _json_error("UserId and GroupId are required", 400)

    user = repository.get_user_by_id(str(user_id))
    if user is None:
        return _json_error("User not found", 404)
    group = _require_group(str(group_id))

    user.setdefault("groupsMember", [])
    if group_id in user["groupsMember"]:
        return _json_error("User already a member of the group", 400)
    user["groupsMember"].append(group_id)
    repository.update_user(user)
    owner = repository.get_user_by_id(group["userId"])
    if owner and owner["id"] != user["id"]:
        _append_notification(
            owner["id"],
            notification_type="group-join",
            title="New group member",
            body=f"{user['username']} joined {group['name']}.",
            actor_id=user["id"],
            actor_username=user["username"],
            group_id=str(group_id),
        )
        _schedule_notifications_refresh([owner["id"]])
    await _emit_group_updated(group, affected_user_ids=[user["id"], group["userId"]])
    return JSONResponse({"result": True, "msg": "Joined group successfully"})


@api_router.api_route("/getAllUserGroups", methods=["POST"])
async def get_all_user_groups(request: Request) -> JSONResponse:
    payload = await request.json()
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("Username or UserId is required", 400)

    user_id = _lookup_user_id(payload)
    if user_id is None:
        return _json_error("User not found.", 400)
    user_fields = repository.get_user_fields(user_id, ["groupsMember"]) or {}

    groups = []
    for group in repository.list_groups_by_ids(list(user_fields.get("groupsMember", []))):
        group_payload = _group_response(group)
        group_payload["events"] = [_event_response(event) for event in group_payload.get("events", [])]
        groups.append(group_payload)

    offset, limit = _pagination_from_mapping(payload)
    groups, total = _slice_items(groups, offset, limit)

    return JSONResponse({"result": True, "msg": "OK", "userId": user_id, "memberGroups": groups, "total": total, "offset": offset, "limit": limit})


@api_router.api_route("/createEvent", methods=["PUT"])
async def create_event(request: Request) -> JSONResponse:
    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    user_id = str(payload.get("userId", "")).strip()

    if not name or not user_id:
        return _json_error("Event name and userId are required", 400)
    if repository.get_event_by_name(name):
        return _json_error("Event name already exists", 400)

    user = repository.get_user_by_id(user_id)
    username = user.get("username") if user else payload.get("eventCreator") or payload.get("username") or "Unknown"

    event_id = str(uuid4())
    event = {
        "id": event_id,
        "name": name,
        "time": payload.get("startTime") or payload.get("time"),
        "startTime": payload.get("startTime") or payload.get("time"),
        "endTime": payload.get("endTime"),
        "long": _coerce_float(payload.get("long"), "coordinate"),
        "lat": _coerce_float(payload.get("lat"), "coordinate"),
        "description": payload.get("description", ""),
        "tags": list(payload.get("tags", [])),
        "eventCreator": payload.get("eventCreator", username),
        "userId": user_id,
        "username": username,
        "ongoing": payload.get("ongoing", True),
        "placeName": payload.get("placeName", ""),
        "placeAddress": payload.get("placeAddress", ""),
        "eventImg(s)": [],
        "attendees": [{"userId": user_id, "username": username}],
        "comments": [],
    }

    group_id = payload.get("groupId")
    if group_id:
        group = repository.get_group_by_id(str(group_id))
        if group:
            event["groupId"] = str(group_id)
            event["groupName"] = group.get("name", "None")
        else:
            event["groupName"] = "None"
    else:
        event["groupName"] = "None"

    repository.create_event(event)

    if user:
        user.setdefault("eventsAttending", [])
        if event_id not in user["eventsAttending"]:
            user["eventsAttending"].append(event_id)
            repository.update_user(user)

    if event.get("groupId"):
        _replace_group_event(event["groupId"], event)

    return JSONResponse({"result": True, "msg": "Event created successfully", "eventId": event_id})


@api_router.api_route("/getMapEvents", methods=["POST"])
async def get_map_events(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    try:
        bottom_left_long = _coerce_float(payload.get("bottomLeftLong"), "coordinate")
        bottom_left_lat = _coerce_float(payload.get("bottomLeftLat"), "coordinate")
        upper_right_long = _coerce_float(payload.get("upperRightLong"), "coordinate")
        upper_right_lat = _coerce_float(payload.get("upperRightLat"), "coordinate")
    except HTTPException as error:
        return _json_error(str(error.detail), 500)

    events = []
    for event in repository.list_events_in_bounds(
        bottom_left_long,
        upper_right_long,
        bottom_left_lat,
        upper_right_lat,
    ):
        if _event_status(event) == "ended":
            continue
        events.append(_event_response(event))
    return JSONResponse({"result": True, "events": events})


@api_router.api_route("/searchEvent", methods=["POST"])
async def search_event(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    if not name:
        return _json_error("Event name not found", 400)

    events = repository.search_events_by_name(name, limit=5)
    events = [event for event in events if _event_status(event) != "ended"]
    if not events:
        return _json_error("Event not found", 400)
    return JSONResponse({"result": True, "msg": "Event found", "events": events})


@api_router.api_route("/addAttendingEvent", methods=["PUT"])
async def add_attending_event(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("EventId is required", 400)
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("Username or UserId is required", 400)

    try:
        user = _require_user(payload)
        event = _require_event(str(event_id))
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)

    user.setdefault("eventsAttending", [])
    if event_id in user["eventsAttending"]:
        return _json_error("User already attending event")

    user["eventsAttending"].append(event_id)
    repository.update_user(user)

    event.setdefault("attendees", [])
    if not any(attendee.get("userId") == user["id"] for attendee in event["attendees"]):
        event["attendees"].append({"userId": user["id"], "username": user["username"]})
        repository.update_event(event)
        if event.get("groupId"):
            _replace_group_event(event["groupId"], event)
        if event.get("userId") and event["userId"] != user["id"]:
            _append_notification(
                event["userId"],
                notification_type="event-join",
                title="Someone joined your event",
                body=f"{user['username']} joined {event['name']}.",
                actor_id=user["id"],
                actor_username=user["username"],
                event_id=event_id,
                group_id=event.get("groupId"),
            )
            _schedule_notifications_refresh([event["userId"]])

    await _emit_event_attendance_update(event)

    return JSONResponse({"result": True, "msg": "OK", "userId": user["id"], "eventId": event_id})


@api_router.api_route("/removeAttendingEvent", methods=["DELETE"])
async def remove_attending_event(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("EventId is required", 400)
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("UserId or Username is required", 400)

    try:
        user = _require_user(payload)
        event = _require_event(str(event_id))
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)

    user["eventsAttending"] = [item for item in user.get("eventsAttending", []) if item != event_id]
    repository.update_user(user)

    event["attendees"] = [
        attendee for attendee in event.get("attendees", []) if attendee.get("userId") != user["id"]
    ]
    repository.update_event(event)
    if event.get("groupId"):
        _replace_group_event(event["groupId"], event)

    await _emit_event_attendance_update(event)

    return JSONResponse({"result": True, "msg": "OK", "userId": user["id"], "eventId": event_id})


@api_router.api_route("/getAttendingEvents", methods=["POST"])
async def get_attending_events(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("Username or UserId is required", 400)

    user_id = _lookup_user_id(payload)
    if user_id is None:
        return _json_error("User not found.", 400)
    user_fields = repository.get_user_fields(user_id, ["eventsAttending"]) or {}

    attending_events = [_event_response(event) for event in repository.list_events_by_ids(list(user_fields.get("eventsAttending", [])))]

    offset, limit = _pagination_from_mapping(payload)
    paged_events, total = _slice_items(attending_events, offset, limit)

    return JSONResponse(
        {
            "result": True,
            "msg": "OK",
            "userId": user_id,
            "attendingEvents": paged_events,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    )


@api_router.api_route("/getSavedEvents", methods=["POST"])
async def get_saved_events(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("Username or UserId is required", 400)

    user_id = _lookup_user_id(payload)
    if user_id is None:
        return _json_error("User not found.", 400)
    user_fields = repository.get_user_fields(user_id, ["savedEvents"]) or {}

    saved_events = []
    for event in repository.list_events_by_ids(list(user_fields.get("savedEvents", []))):
        if _event_status(event) != "ended":
            saved_events.append(_event_response(event))

    offset, limit = _pagination_from_mapping(payload)
    paged_events, total = _slice_items(saved_events, offset, limit)

    return JSONResponse(
        {
            "result": True,
            "msg": "OK",
            "userId": user_id,
            "savedEvents": paged_events,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    )


@api_router.api_route("/getPlanningEvents", methods=["POST"])
async def get_planning_events(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("Username or UserId is required", 400)

    user_id = _lookup_user_id(payload)
    if user_id is None:
        return _json_error("User not found.", 400)
    user_fields = repository.get_user_fields(user_id, ["eventsAttending", "savedEvents"]) or {}

    month = str(payload.get("month", "")).strip()
    month_start: datetime | None = None
    month_end: datetime | None = None
    if month:
        try:
            month_start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
            month_end = datetime(month_start.year + (month_start.month // 12), (month_start.month % 12) + 1, 1, tzinfo=timezone.utc)
        except ValueError:
            return _json_error("month must be in YYYY-MM format", 400)

    merged: dict[str, dict[str, Any]] = {}
    for event in repository.list_events_by_ids([*user_fields.get("eventsAttending", []), *user_fields.get("savedEvents", [])]):
        if not event or _event_status(event) == "ended":
            continue
        event_dt = _event_datetime(event.get("startTime") or event.get("time"))
        if month_start and (not event_dt or event_dt < month_start or event_dt >= month_end):
            continue
        merged[event["id"]] = _event_response(event)

    planning_events = sorted(
        merged.values(),
        key=lambda item: (_event_datetime(item.get("startTime") or item.get("time")) or datetime.max.replace(tzinfo=timezone.utc)),
    )
    offset, limit = _pagination_from_mapping(payload, default_limit=5 if not month else 50)
    paged_events, total = _slice_items(planning_events, offset, limit)
    return JSONResponse(
        {
            "result": True,
            "msg": "OK",
            "userId": user_id,
            "events": paged_events,
            "total": total,
            "offset": offset,
            "limit": limit,
            "month": month or None,
        }
    )


@api_router.api_route("/getNotifications", methods=["POST"])
async def get_notifications(request: Request) -> JSONResponse:
    payload = await request.json()
    user_id = _lookup_user_id(payload)
    if user_id is None:
        return _json_error("User not found.", 400)

    user_payload = repository.get_user_fields(user_id, ["notifications"]) or {}
    notifications = [_notification_response(item) for item in user_payload.get("notifications", [])]
    return JSONResponse(
        {
            "result": True,
            "notifications": notifications,
            "unreadCount": sum(1 for item in notifications if not item.get("read")),
        }
    )


@api_router.api_route("/markNotificationsRead", methods=["POST"])
async def mark_notifications_read(request: Request) -> JSONResponse:
    payload = await request.json()
    notification_ids = set(payload.get("notificationIds", []) or [])
    mark_all = bool(payload.get("markAll"))
    try:
        user = _require_user(payload)
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)

    user.setdefault("notifications", [])
    for notification in user["notifications"]:
        if mark_all or notification.get("id") in notification_ids:
            notification["read"] = True
    repository.update_user(user)
    _schedule_notifications_refresh([user["id"]])
    return JSONResponse({"result": True, "msg": "Notifications updated"})


@api_router.api_route("/saveEvent", methods=["POST"])
async def save_event(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("EventId is required", 400)
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("UserId or Username is required", 400)

    try:
        user = _require_user(payload)
        _require_event(str(event_id))
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)

    user.setdefault("savedEvents", [])
    if event_id in user["savedEvents"]:
        return JSONResponse({"result": True, "msg": "Event already saved", "eventId": event_id})

    user["savedEvents"].append(event_id)
    repository.update_user(user)
    return JSONResponse({"result": True, "msg": "Event saved", "eventId": event_id})


@api_router.api_route("/removeSavedEvent", methods=["DELETE"])
async def remove_saved_event(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("EventId is required", 400)
    if not payload.get("userId") and not payload.get("username"):
        return _json_error("UserId or Username is required", 400)

    try:
        user = _require_user(payload)
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)

    user["savedEvents"] = [item for item in user.get("savedEvents", []) if item != event_id]
    repository.update_user(user)
    return JSONResponse({"result": True, "msg": "Saved event removed", "eventId": event_id})


@api_router.api_route("/getEventInfo", methods=["POST"])
async def get_event_info(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("Event ID is required", 400)
    event = repository.get_event_by_id(str(event_id))
    if event is None:
        return _json_error("Event not found", 400)
    return JSONResponse({"result": True, "eventInfo": _event_response(event), "event": _event_response(event)})


@api_router.api_route("/getEventComments", methods=["POST"])
async def get_event_comments(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("Event ID is required", 400)
    event = repository.get_event_by_id(str(event_id))
    if event is None:
        return _json_error("Event not found", 404)
    comments = [_comment_response(item) for item in event.get("comments", [])]
    return JSONResponse({"result": True, "comments": comments})


@api_router.api_route("/addEventComment", methods=["POST"])
async def add_event_comment(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = str(payload.get("eventId", "")).strip()
    body = str(payload.get("body", "")).strip()
    if not event_id or not body:
        return _json_error("Event ID and comment body are required", 400)

    try:
        user = _require_user(payload)
        event = _require_event(event_id)
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)

    comment = {
        "id": str(uuid4()),
        "userId": user["id"],
        "username": user["username"],
        "body": body,
        "createdAt": _now_iso(),
    }
    event.setdefault("comments", []).append(comment)
    repository.update_event(event)
    if event.get("groupId"):
        _replace_group_event(event["groupId"], event)
    if event.get("userId") and event["userId"] != user["id"]:
        _append_notification(
            event["userId"],
            notification_type="event-comment",
            title="New comment on your event",
            body=f"{user['username']}: {body[:72]}",
            actor_id=user["id"],
            actor_username=user["username"],
            event_id=event_id,
            group_id=event.get("groupId"),
        )
        _schedule_notifications_refresh([event["userId"]])
    await _emit_event_comment_created(event, comment)
    return JSONResponse({"result": True, "comment": _comment_response(comment)})


@api_router.api_route("/deleteEventComment", methods=["DELETE"])
async def delete_event_comment(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = str(payload.get("eventId", "")).strip()
    comment_id = str(payload.get("commentId", "")).strip()
    if not event_id or not comment_id:
        return _json_error("Event ID and comment ID are required", 400)
    try:
        user = _require_user(payload)
        event = _require_event(event_id)
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)

    comment = next((item for item in event.get("comments", []) if item.get("id") == comment_id), None)
    if comment is None:
        return _json_error("Comment not found", 404)
    if comment.get("userId") != user["id"] and event.get("userId") != user["id"]:
        return _json_error("Not allowed to delete this comment", 403)

    event["comments"] = [item for item in event.get("comments", []) if item.get("id") != comment_id]
    repository.update_event(event)
    if event.get("groupId"):
        _replace_group_event(event["groupId"], event)
    await _emit_event_comment_deleted(event_id, comment_id, event.get("userId"))
    return JSONResponse({"result": True, "msg": "Comment deleted"})


@api_router.api_route("/getEventImgs", methods=["POST"])
async def get_event_imgs(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("Please pass an eventId in the query string", 400)
    event = repository.get_event_by_id(str(event_id))
    if event is None:
        return _json_error(f"No event found with ID {event_id}", 404)

    image_urls = list(event.get("eventImg(s)", []))
    return JSONResponse(
        {
            "result": True,
            "eventId": event_id,
            "imageUrls": image_urls,
            "imgUrls": image_urls,
        }
    )


@api_router.api_route("/getEventAttendees", methods=["GET"])
def get_event_attendees() -> JSONResponse:
    _cleanup_expired_events()
    event_attendees = [
        {"eventId": event["id"], "attendees": list(event.get("attendees", []))}
        for event in repository.list_events()
    ]
    return JSONResponse({"result": True, "eventAttendees": event_attendees})


@api_router.api_route("/getGroupEvents", methods=["POST"])
async def get_group_events(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    group_id = payload.get("groupId")
    if not group_id:
        return _json_error("GroupId is required", 400)
    group = repository.get_group_by_id(str(group_id))
    if group is None:
        return _json_error("Group not found", 404)
    return JSONResponse(
        {
            "result": True,
            "msg": "Events retrieved successfully",
            "events": [_event_response(event) for event in group.get("events", [])],
        }
    )


@api_router.api_route("/getAllUserGroupEvents", methods=["POST"])
async def get_all_user_group_events(request: Request) -> JSONResponse:
    _cleanup_expired_events()
    payload = await request.json()
    user_id = payload.get("userId")
    if not user_id:
        return _json_error("UserId is required", 400)
    user = repository.get_user_by_id(str(user_id))
    if user is None:
        return _json_error("User not found", 404)

    seen: set[str] = set()
    all_events: list[dict[str, Any]] = []
    for group in repository.list_groups_by_ids(list(user.get("groupsMember", []))):
        for event in group.get("events", []):
            event_id = event.get("id")
            if event_id and event_id not in seen:
                all_events.append(_event_response(event))
                seen.add(event_id)

    return JSONResponse({"result": True, "msg": "Events retrieved successfully", "events": all_events})


@api_router.api_route("/getGroupChatMessages", methods=["POST"])
async def get_group_chat_messages(request: Request) -> JSONResponse:
    payload = await request.json()
    group_id = str(payload.get("groupId", "")).strip()
    if not group_id:
        return _json_error("GroupId is required", 400)
    try:
        user = _require_user(payload)
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)
    group_fields = repository.get_group_fields(group_id, ["userId", "messages"])
    if group_fields is None:
        return _json_error("Group not found", 404)

    if group_id not in user.get("groupsMember", []) and group_fields.get("userId") != user["id"]:
        return _json_error("User is not a member of the group", 403)

    messages = [_message_response(item) for item in group_fields.get("messages", [])]
    return JSONResponse({"result": True, "messages": messages})


@api_router.api_route("/sendGroupChatMessage", methods=["POST"])
async def send_group_chat_message(request: Request) -> JSONResponse:
    payload = await request.json()
    group_id = str(payload.get("groupId", "")).strip()
    body = str(payload.get("body", "")).strip()
    if not group_id or not body:
        return _json_error("GroupId and body are required", 400)
    try:
        user = _require_user(payload)
    except HTTPException as error:
        return _json_error(str(error.detail), error.status_code)
    group_fields = repository.get_group_fields(group_id, ["name", "userId"])
    if group_fields is None:
        return _json_error("Group not found", 404)

    if group_id not in user.get("groupsMember", []) and group_fields.get("userId") != user["id"]:
        return _json_error("User is not a member of the group", 403)

    message = {
        "id": str(uuid4()),
        "userId": user["id"],
        "username": user["username"],
        "body": body,
        "createdAt": _now_iso(),
    }
    repository.append_group_message(group_id, message)

    recipient_ids = [
        recipient_id
        for recipient_id in repository.list_user_ids_for_group(group_id)
        if recipient_id != user["id"]
    ]
    for recipient_id in recipient_ids:
        _append_notification(
            recipient_id,
            notification_type="group-chat",
            title=f"New message in {group_fields['name']}",
            body=f"{user['username']}: {body[:72]}",
            actor_id=user["id"],
            actor_username=user["username"],
            group_id=group_id,
        )
    _schedule_notifications_refresh(recipient_ids)

    await _emit_group_chat_message(group_id, message)

    return JSONResponse({"result": True, "message": _message_response(message)})


@api_router.api_route("/uploadEventImage", methods=["POST"])
async def upload_event_image(file: UploadFile = File(...), eventId: str = Form(...)) -> PlainTextResponse:
    event = repository.get_event_by_id(eventId)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event with ID {eventId} not found")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File and eventId must be provided")

    image_url = _store_image(eventId, file, file_bytes)
    event.setdefault("eventImg(s)", []).append(image_url)
    repository.update_event(event)
    if event.get("groupId"):
        _replace_group_event(event["groupId"], event)

    return PlainTextResponse(f"The file {file.filename} uploaded successfully. URL: {image_url}")


@api_router.api_route("/deleteEvent", methods=["DELETE"])
async def delete_event(request: Request) -> JSONResponse:
    payload = await request.json()
    event_id = payload.get("eventId")
    if not event_id:
        return _json_error("EventId is required", 400)
    event = repository.get_event_by_id(str(event_id))
    if event is None:
        return _json_error("Event not found", 400)

    _delete_event_and_references(event)

    return JSONResponse({"result": True, "msg": "Event removed successfully", "eventId": str(event_id)})


@api_router.api_route("/deleteGroup", methods=["DELETE"])
async def delete_group(request: Request) -> JSONResponse:
    payload = await request.json()
    group_id = payload.get("groupId")
    if not group_id:
        return _json_error("GroupId is required", 400)

    group = repository.get_group_by_id(str(group_id))
    if group is None:
        return _json_error("Group not found", 400)

    repository.delete_group(str(group_id))

    member_ids = repository.list_user_ids_for_group(str(group_id))
    for user in repository.list_users_by_ids(member_ids):
        user["groupsMember"] = [item for item in user.get("groupsMember", []) if item != group_id]
        repository.update_user(user)

    for event in repository.list_events():
        if event.get("groupId") == group_id:
            event.pop("groupId", None)
            event["groupName"] = "None"
            repository.update_event(event)

    return JSONResponse({"result": True, "msg": "Group deleted successfully", "groupId": str(group_id)})


@api_router.api_route("/updateEvent", methods=["POST", "PUT", "PATCH"])
async def update_event(request: Request) -> JSONResponse:
    payload = await request.json()
    event = None
    if payload.get("id"):
        event = repository.get_event_by_id(str(payload["id"]))
    elif payload.get("eventId"):
        event = repository.get_event_by_id(str(payload["eventId"]))
    elif payload.get("name"):
        event = repository.get_event_by_name(str(payload["name"]))

    if event is None:
        return _json_error("Event not found")

    for field in ("time", "startTime", "endTime", "description", "tags", "ongoing", "name", "placeName", "placeAddress"):
        if field in payload:
            event[field] = payload[field]
    if "startTime" in payload:
        event["time"] = payload["startTime"]
    elif "time" in payload and "startTime" not in payload:
        event["startTime"] = payload["time"]
    if "long" in payload:
        event["long"] = _coerce_float(payload["long"], "coordinate")
    if "lat" in payload:
        event["lat"] = _coerce_float(payload["lat"], "coordinate")
    repository.update_event(event)
    if event.get("groupId"):
        _replace_group_event(event["groupId"], event)
    return JSONResponse({"result": True, "msg": "Event updated successfully"})


@api_router.api_route("/updateUser", methods=["POST", "PUT", "PATCH"])
async def update_user(request: Request) -> JSONResponse:
    payload = await request.json()
    user = None
    if payload.get("userId"):
        user = repository.get_user_by_id(str(payload["userId"]))
    elif payload.get("id"):
        user = repository.get_user_by_id(str(payload["id"]))
    elif payload.get("username"):
        user = repository.get_user_by_username(str(payload["username"]))

    if user is None:
        return _json_error("User not found", 400)

    if "password" in payload:
        user["passwordHash"] = bcrypt.hashpw(
            str(payload["password"]).encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
    if "username" in payload:
        desired_username = str(payload["username"]).strip()
        existing = repository.get_user_by_username(desired_username)
        if existing and existing["id"] != user["id"]:
            return _json_error("Username already exists", 400)
        user["username"] = desired_username
    for field in ("eventsAttending", "groupsMember", "savedEvents"):
        if field in payload:
            user[field] = list(payload[field])
    if "notifications" in payload:
        user["notifications"] = list(payload["notifications"])
    repository.update_user(user)
    return JSONResponse({"result": True, "msg": "User updated successfully", "userId": user["id"]})


@api_router.get("/exportEventIcs")
async def export_event_ics(eventId: str) -> Response:
    _cleanup_expired_events()
    event = repository.get_event_by_id(str(eventId))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    calendar = _build_ics_calendar([event])
    filename = f"{_sanitize_filename(event.get('name', 'event'))}.ics"
    return Response(
        content=calendar,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api_router.get("/exportScheduleIcs")
async def export_schedule_ics(userId: str) -> Response:
    _cleanup_expired_events()
    user = repository.get_user_by_id(str(userId))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    exported_events = []
    seen: set[str] = set()
    for event_id in [*user.get("eventsAttending", []), *user.get("savedEvents", [])]:
        if event_id in seen:
            continue
        event = repository.get_event_by_id(event_id)
        if event is None or _event_status(event) == "ended":
            continue
        exported_events.append(event)
        seen.add(event_id)

    calendar = _build_ics_calendar(exported_events)
    filename = f"{_sanitize_filename(user.get('username', 'schedule'))}-schedule.ics"
    return Response(
        content=calendar,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


app.include_router(api_router)


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_path(full_path: str) -> FileResponse:
    requested_file = _get_frontend_file(full_path)
    if requested_file is not None:
        return FileResponse(requested_file)

    index_file = _get_frontend_file("index.html")
    if index_file is not None:
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend build not found")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail)
    return _json_error(message, exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logging.exception("Unhandled server error", exc_info=exc)
    return _json_error(f"System error: {exc}", 500)
