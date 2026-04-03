from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from pymongo import MongoClient


def _clean(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    payload = deepcopy(document)
    payload.pop("_id", None)
    return payload


class MemoryRepository:
    def __init__(self) -> None:
        self.users: dict[str, dict[str, Any]] = {}
        self.events: dict[str, dict[str, Any]] = {}
        self.groups: dict[str, dict[str, Any]] = {}

    def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        self.users[user["id"]] = deepcopy(user)
        return _clean(self.users[user["id"]])

    def update_user(self, user: dict[str, Any]) -> dict[str, Any]:
        self.users[user["id"]] = deepcopy(user)
        return _clean(self.users[user["id"]])

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return _clean(self.users.get(user_id))

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        for user in self.users.values():
            if user.get("username") == username:
                return _clean(user)
        return None

    def get_user_by_guest_session(self, guest_session_id: str) -> dict[str, Any] | None:
        for user in self.users.values():
            if user.get("guestSessionId") == guest_session_id:
                return _clean(user)
        return None

    def get_user_fields(self, user_id: str, fields: list[str]) -> dict[str, Any] | None:
        user = self.users.get(user_id)
        if user is None:
            return None
        return {field: deepcopy(user.get(field)) for field in fields}

    def list_users(self) -> list[dict[str, Any]]:
        return [_clean(user) for user in self.users.values()]

    def list_users_by_ids(self, user_ids: list[str]) -> list[dict[str, Any]]:
        return [_clean(self.users[user_id]) for user_id in user_ids if user_id in self.users]

    def list_user_ids_for_group(self, group_id: str) -> list[str]:
        member_ids: list[str] = []
        for user in self.users.values():
            if group_id in user.get("groupsMember", []):
                member_ids.append(str(user["id"]))
        return member_ids

    def clear_all(self) -> None:
        self.users.clear()
        self.events.clear()
        self.groups.clear()

    def create_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.events[event["id"]] = deepcopy(event)
        return _clean(self.events[event["id"]])

    def update_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.events[event["id"]] = deepcopy(event)
        return _clean(self.events[event["id"]])

    def get_event_by_id(self, event_id: str) -> dict[str, Any] | None:
        return _clean(self.events.get(event_id))

    def get_event_by_name(self, name: str) -> dict[str, Any] | None:
        for event in self.events.values():
            if event.get("name") == name:
                return _clean(event)
        return None

    def list_events(self) -> list[dict[str, Any]]:
        return [_clean(event) for event in self.events.values()]

    def list_events_by_ids(self, event_ids: list[str]) -> list[dict[str, Any]]:
        return [_clean(self.events[event_id]) for event_id in event_ids if event_id in self.events]

    def list_events_in_bounds(
        self,
        bottom_left_long: float,
        upper_right_long: float,
        bottom_left_lat: float,
        upper_right_lat: float,
    ) -> list[dict[str, Any]]:
        matches = []
        for event in self.events.values():
            event_long = event.get("long")
            event_lat = event.get("lat")
            if event_long is None or event_lat is None:
                continue
            if bottom_left_long <= float(event_long) <= upper_right_long and bottom_left_lat <= float(event_lat) <= upper_right_lat:
                matches.append(_clean(event))
        return matches

    def search_events_by_name(self, name: str, limit: int = 5) -> list[dict[str, Any]]:
        needle = name.lower()
        matches = [event for event in self.events.values() if needle in event.get("name", "").lower()]
        matches.sort(key=lambda item: item.get("name", "").lower())
        return [_clean(event) for event in matches[:limit]]

    def delete_event(self, event_id: str) -> None:
        self.events.pop(event_id, None)

    def create_group(self, group: dict[str, Any]) -> dict[str, Any]:
        self.groups[group["id"]] = deepcopy(group)
        return _clean(self.groups[group["id"]])

    def update_group(self, group: dict[str, Any]) -> dict[str, Any]:
        self.groups[group["id"]] = deepcopy(group)
        return _clean(self.groups[group["id"]])

    def append_group_message(self, group_id: str, message: dict[str, Any], *, limit: int = 100) -> None:
        group = self.groups.get(group_id)
        if group is None:
            return
        group.setdefault("messages", []).append(deepcopy(message))
        group["messages"] = group["messages"][-limit:]

    def get_group_fields(self, group_id: str, fields: list[str]) -> dict[str, Any] | None:
        group = self.groups.get(group_id)
        if group is None:
            return None
        return {field: deepcopy(group.get(field)) for field in fields}

    def append_user_notification(self, user_id: str, notification: dict[str, Any], *, limit: int = 75) -> None:
        user = self.users.get(user_id)
        if user is None:
            return
        user.setdefault("notifications", [])
        user["notifications"].insert(0, deepcopy(notification))
        user["notifications"] = user["notifications"][:limit]

    def get_group_by_id(self, group_id: str) -> dict[str, Any] | None:
        return _clean(self.groups.get(group_id))

    def get_group_by_name(self, name: str) -> dict[str, Any] | None:
        for group in self.groups.values():
            if group.get("name") == name:
                return _clean(group)
        return None

    def list_groups(self) -> list[dict[str, Any]]:
        groups = [_clean(group) for group in self.groups.values()]
        groups.sort(key=lambda item: item.get("name", "").lower())
        return groups

    def list_groups_by_ids(self, group_ids: list[str]) -> list[dict[str, Any]]:
        groups = [_clean(self.groups[group_id]) for group_id in group_ids if group_id in self.groups]
        groups.sort(key=lambda item: item.get("name", "").lower())
        return groups

    def delete_group(self, group_id: str) -> None:
        self.groups.pop(group_id, None)


class MongoRepository:
    def __init__(self, mongodb_uri: str, database_name: str) -> None:
        self.client = MongoClient(mongodb_uri)
        self.database = self.client[database_name]
        self.users = self.database["users"]
        self.events = self.database["events"]
        self.groups = self.database["groups"]
        self.users.create_index("id", unique=True)
        self.users.create_index("username", unique=True)
        self.users.create_index("guestSessionId", unique=True, sparse=True)
        self.users.create_index("groupsMember")
        self.events.create_index("id", unique=True)
        self.events.create_index("name", unique=True)
        self.events.create_index([("long", 1), ("lat", 1)])
        self.groups.create_index("id", unique=True)
        self.groups.create_index("name", unique=True)

    def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(user)
        payload["_id"] = user["id"]
        self.users.insert_one(payload)
        return _clean(payload)

    def update_user(self, user: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(user)
        payload["_id"] = user["id"]
        self.users.replace_one({"id": user["id"]}, payload, upsert=True)
        return _clean(payload)

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return _clean(self.users.find_one({"id": user_id}))

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        return _clean(self.users.find_one({"username": username}))

    def get_user_by_guest_session(self, guest_session_id: str) -> dict[str, Any] | None:
        return _clean(self.users.find_one({"guestSessionId": guest_session_id}))

    def get_user_fields(self, user_id: str, fields: list[str]) -> dict[str, Any] | None:
        projection = {field: 1 for field in fields}
        projection["_id"] = 0
        return _clean(self.users.find_one({"id": user_id}, projection))

    def list_users(self) -> list[dict[str, Any]]:
        return [_clean(user) for user in self.users.find({})]

    def list_users_by_ids(self, user_ids: list[str]) -> list[dict[str, Any]]:
        if not user_ids:
            return []
        return [_clean(user) for user in self.users.find({"id": {"$in": user_ids}})]

    def list_user_ids_for_group(self, group_id: str) -> list[str]:
        cursor = self.users.find({"groupsMember": group_id}, {"id": 1})
        return [str(user["id"]) for user in cursor if user.get("id")]

    def clear_all(self) -> None:
        self.users.delete_many({})
        self.events.delete_many({})
        self.groups.delete_many({})

    def create_event(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(event)
        payload["_id"] = event["id"]
        self.events.insert_one(payload)
        return _clean(payload)

    def update_event(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(event)
        payload["_id"] = event["id"]
        self.events.replace_one({"id": event["id"]}, payload, upsert=True)
        return _clean(payload)

    def get_event_by_id(self, event_id: str) -> dict[str, Any] | None:
        return _clean(self.events.find_one({"id": event_id}))

    def get_event_by_name(self, name: str) -> dict[str, Any] | None:
        return _clean(self.events.find_one({"name": name}))

    def list_events(self) -> list[dict[str, Any]]:
        return [_clean(event) for event in self.events.find({})]

    def list_events_by_ids(self, event_ids: list[str]) -> list[dict[str, Any]]:
        if not event_ids:
            return []
        return [_clean(event) for event in self.events.find({"id": {"$in": event_ids}})]

    def list_events_in_bounds(
        self,
        bottom_left_long: float,
        upper_right_long: float,
        bottom_left_lat: float,
        upper_right_lat: float,
    ) -> list[dict[str, Any]]:
        query = {
            "long": {"$gte": bottom_left_long, "$lte": upper_right_long},
            "lat": {"$gte": bottom_left_lat, "$lte": upper_right_lat},
        }
        return [_clean(event) for event in self.events.find(query)]

    def search_events_by_name(self, name: str, limit: int = 5) -> list[dict[str, Any]]:
        pattern = re.escape(name)
        cursor = self.events.find({"name": {"$regex": pattern, "$options": "i"}}).limit(limit)
        return [_clean(event) for event in cursor]

    def delete_event(self, event_id: str) -> None:
        self.events.delete_one({"id": event_id})

    def create_group(self, group: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(group)
        payload["_id"] = group["id"]
        self.groups.insert_one(payload)
        return _clean(payload)

    def update_group(self, group: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(group)
        payload["_id"] = group["id"]
        self.groups.replace_one({"id": group["id"]}, payload, upsert=True)
        return _clean(payload)

    def append_group_message(self, group_id: str, message: dict[str, Any], *, limit: int = 100) -> None:
        self.groups.update_one(
            {"id": group_id},
            {"$push": {"messages": {"$each": [deepcopy(message)], "$slice": -limit}}},
        )

    def get_group_fields(self, group_id: str, fields: list[str]) -> dict[str, Any] | None:
        projection = {field: 1 for field in fields}
        projection["_id"] = 0
        return _clean(self.groups.find_one({"id": group_id}, projection))

    def append_user_notification(self, user_id: str, notification: dict[str, Any], *, limit: int = 75) -> None:
        self.users.update_one(
            {"id": user_id},
            {"$push": {"notifications": {"$each": [deepcopy(notification)], "$position": 0, "$slice": limit}}},
        )

    def get_group_by_id(self, group_id: str) -> dict[str, Any] | None:
        return _clean(self.groups.find_one({"id": group_id}))

    def get_group_by_name(self, name: str) -> dict[str, Any] | None:
        return _clean(self.groups.find_one({"name": name}))

    def list_groups(self) -> list[dict[str, Any]]:
        return [_clean(group) for group in self.groups.find({}).sort("name", 1)]

    def list_groups_by_ids(self, group_ids: list[str]) -> list[dict[str, Any]]:
        if not group_ids:
            return []
        return [_clean(group) for group in self.groups.find({"id": {"$in": group_ids}}).sort("name", 1)]

    def delete_group(self, group_id: str) -> None:
        self.groups.delete_one({"id": group_id})
