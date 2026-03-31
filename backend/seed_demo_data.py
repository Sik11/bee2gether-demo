from __future__ import annotations

import argparse
import bcrypt
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random
from typing import Any
from uuid import uuid4

from backend.config import get_settings
from backend.repository import MemoryRepository, MongoRepository


DEMO_PASSWORD = "demo1234567"
DEFAULT_RANDOM_SEED = 20260331
DEFAULT_USER_COUNT = 50
DEFAULT_EVENT_COUNT = 75
DEFAULT_GROUP_COUNT = 12


@dataclass(frozen=True)
class SeedStats:
    users: int
    events: int
    groups: int
    comments: int
    messages: int
    notifications: int


UK_PLACES: tuple[dict[str, Any], ...] = (
    {"city": "London", "placeName": "Coal Drops Yard", "placeAddress": "Stable Street, King's Cross, London", "lat": 51.5356, "lng": -0.1254},
    {"city": "London", "placeName": "Southbank Centre", "placeAddress": "Belvedere Road, London", "lat": 51.5068, "lng": -0.1168},
    {"city": "Manchester", "placeName": "Mackie Mayor", "placeAddress": "1 Eagle Street, Manchester", "lat": 53.4855, "lng": -2.2347},
    {"city": "Manchester", "placeName": "HOME Manchester", "placeAddress": "2 Tony Wilson Place, Manchester", "lat": 53.4721, "lng": -2.2515},
    {"city": "Birmingham", "placeName": "Digbeth Dining Club", "placeAddress": "Hurst Street, Birmingham", "lat": 52.4750, "lng": -1.8876},
    {"city": "Birmingham", "placeName": "The Custard Factory", "placeAddress": "Gibb Street, Birmingham", "lat": 52.4758, "lng": -1.8847},
    {"city": "Bristol", "placeName": "Wapping Wharf", "placeAddress": "Gaol Ferry Steps, Bristol", "lat": 51.4488, "lng": -2.5989},
    {"city": "Bristol", "placeName": "Arnolfini", "placeAddress": "16 Narrow Quay, Bristol", "lat": 51.4507, "lng": -2.5981},
    {"city": "Leeds", "placeName": "Belgrave Music Hall", "placeAddress": "1-1A Cross Belgrave Street, Leeds", "lat": 53.8016, "lng": -1.5416},
    {"city": "Liverpool", "placeName": "Baltic Market", "placeAddress": "Stanhope Street, Liverpool", "lat": 53.3934, "lng": -2.9796},
    {"city": "Southampton", "placeName": "Southampton Common", "placeAddress": "The Avenue, Southampton", "lat": 50.9254, "lng": -1.4047},
    {"city": "Southampton", "placeName": "Westquay Esplanade", "placeAddress": "Harbour Parade, Southampton", "lat": 50.9016, "lng": -1.4078},
    {"city": "Portsmouth", "placeName": "Southsea Common", "placeAddress": "Clarence Esplanade, Portsmouth", "lat": 50.7867, "lng": -1.0935},
    {"city": "Edinburgh", "placeName": "The Meadows", "placeAddress": "Melville Drive, Edinburgh", "lat": 55.9400, "lng": -3.1924},
    {"city": "Glasgow", "placeName": "SWG3", "placeAddress": "100 Eastvale Place, Glasgow", "lat": 55.8680, "lng": -4.2928},
    {"city": "Cardiff", "placeName": "Cardiff Bay Barrage", "placeAddress": "Harbour Drive, Cardiff", "lat": 51.4534, "lng": -3.1640},
    {"city": "Nottingham", "placeName": "Sneinton Market", "placeAddress": "Avenue C, Nottingham", "lat": 52.9510, "lng": -1.1388},
    {"city": "Leeds", "placeName": "Hyde Park Book Club", "placeAddress": "27-29 Headingley Lane, Leeds", "lat": 53.8066, "lng": -1.5575},
)

FIRST_NAMES = (
    "Amelia", "Aria", "Ava", "Bella", "Callum", "Chloe", "Daniel", "Ella", "Ethan", "Evie",
    "Freya", "George", "Grace", "Hannah", "Harry", "Harvey", "Ivy", "Jack", "James", "Jasmine",
    "Joshua", "Leo", "Lily", "Logan", "Lucas", "Mason", "Mia", "Noah", "Olivia", "Oscar",
    "Poppy", "Riley", "Rosie", "Ruby", "Sienna", "Sophia", "Theo", "Thomas", "Toby", "Willow",
)
LAST_NAMES = (
    "Ahmed", "Bailey", "Bennett", "Brown", "Campbell", "Carter", "Clarke", "Cooper", "Davies",
    "Edwards", "Evans", "Green", "Hall", "Harris", "Hughes", "Jackson", "Johnson", "Jones",
    "Kelly", "Khan", "Lewis", "Martin", "Mitchell", "Moore", "Morgan", "Murphy", "Patel",
    "Roberts", "Robinson", "Singh", "Smith", "Taylor", "Thomas", "Turner", "Walker", "Ward",
    "Watson", "White", "Williams", "Wilson",
)
GROUP_DEFS = (
    ("Coffee Circuit", "Early starts, flat whites, and new corners of the city."),
    ("After Work Social", "Low-pressure plans for weeknights and spontaneous meetups."),
    ("Study Hive", "Revision, accountability, and library breaks."),
    ("Gig Chasers", "Live music, last-minute tickets, and good venues."),
    ("Matchday Crew", "Football screenings, five-a-side, and post-game food."),
    ("Weekend Walkers", "Scenic routes, podcasts, and fresh air."),
    ("Brunch Board", "Cafe scouting and Sunday table reservations."),
    ("Indie Film Club", "Cinema trips and post-film debates."),
    ("Design and Dev", "Hack nights, portfolio reviews, and creative meetups."),
    ("Running Club", "Beginner-friendly runs and social cool-downs."),
    ("Food Spotters", "Street food, markets, and hidden local favourites."),
    ("Sunset Sessions", "Golden hour hangs, rooftops, and low-key evenings."),
)
EVENT_THEMES = (
    ("Sunset Coffee Walk", ("coffee", "casual", "walk")),
    ("Library Sprint Session", ("study", "quiet", "productivity")),
    ("Rooftop Social", ("nightlife", "social", "city")),
    ("Brunch and Book Swap", ("brunch", "books", "community")),
    ("Five-a-Side Kickabout", ("football", "fitness", "sport")),
    ("Live Jazz Meetup", ("music", "nightlife", "friends")),
    ("Hack and Hang", ("coding", "creative", "networking")),
    ("Cinema and Dessert Run", ("film", "food", "casual")),
    ("Market Lunch Loop", ("food", "weekend", "walk")),
    ("Seafront Run Club", ("fitness", "outdoors", "group")),
    ("Board Games and Bao", ("games", "food", "social")),
    ("Study Break Matcha Stop", ("study", "coffee", "friends")),
)
COMMENT_SNIPPETS = (
    "I can make this one.",
    "Count me in.",
    "This looks ideal after work.",
    "Bringing a couple of friends.",
    "Perfect timing.",
    "I have been wanting to try this spot.",
    "Will there be space for one more?",
    "Looks like a good crowd already.",
    "I will head over straight after class.",
    "This is exactly my kind of plan.",
)
CHAT_SNIPPETS = (
    "Anyone else nearby already?",
    "I can be there in 15.",
    "The new place looks solid.",
    "Dropping the venue pin here.",
    "I am bringing one more person.",
    "Should we lock in a time?",
    "The weather looks good for this.",
    "I can host the table booking.",
    "Good crowd for this one.",
    "Let’s keep this one going next week.",
)


def _random_datetime(rng: Random) -> tuple[datetime, datetime]:
    start_at = datetime.now(timezone.utc) + timedelta(
        days=rng.randint(1, 21),
        hours=rng.choice((9, 11, 13, 15, 18, 19, 20)),
        minutes=rng.choice((0, 15, 30, 45)),
    )
    start_at = start_at.replace(second=0, microsecond=0)
    end_at = start_at + timedelta(hours=rng.choice((1, 2, 2, 3)))
    return start_at, end_at


def _notification(
    *,
    notification_type: str,
    title: str,
    body: str,
    actor_id: str | None = None,
    actor_username: str | None = None,
    event_id: str | None = None,
    group_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "type": notification_type,
        "title": title,
        "body": body,
        "read": False,
        "createdAt": created_at or datetime.now(timezone.utc).isoformat(),
        "actorId": actor_id,
        "actorUsername": actor_username,
        "eventId": event_id,
        "groupId": group_id,
    }


def _build_usernames(count: int, rng: Random) -> list[str]:
    usernames: list[str] = []
    seen: set[str] = set()
    pairings = [(first, last) for first in FIRST_NAMES for last in LAST_NAMES]
    rng.shuffle(pairings)

    for first, last in pairings:
        candidate = f"{first.lower()}.{last.lower()}"
        if candidate in seen:
            continue
        seen.add(candidate)
        usernames.append(candidate)
        if len(usernames) >= count:
            break
    return usernames


def _append_notification(user: dict[str, Any], payload: dict[str, Any]) -> None:
    user.setdefault("notifications", [])
    user["notifications"].insert(0, payload)
    user["notifications"] = user["notifications"][:50]


def seed_demo_data(
    repository: Any,
    *,
    user_count: int = DEFAULT_USER_COUNT,
    event_count: int = DEFAULT_EVENT_COUNT,
    group_count: int = DEFAULT_GROUP_COUNT,
    reset: bool = True,
    seed_if_empty: bool = False,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> SeedStats:
    if seed_if_empty and (
        repository.list_users() or repository.list_events() or repository.list_groups()
    ):
        return SeedStats(
            users=len(repository.list_users()),
            events=len(repository.list_events()),
            groups=len(repository.list_groups()),
            comments=sum(len(event.get("comments", [])) for event in repository.list_events()),
            messages=sum(len(group.get("messages", [])) for group in repository.list_groups()),
            notifications=sum(len(user.get("notifications", [])) for user in repository.list_users()),
        )

    if reset:
        repository.clear_all()

    rng = Random(random_seed)
    password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    users_by_id: dict[str, dict[str, Any]] = {}
    users_by_username: dict[str, dict[str, Any]] = {}
    for username in _build_usernames(user_count, rng):
        user = {
            "id": str(uuid4()),
            "username": username,
            "passwordHash": password_hash,
            "eventsAttending": [],
            "groupsMember": [],
            "savedEvents": [],
            "notifications": [],
            "isGuest": False,
        }
        users_by_id[user["id"]] = user
        users_by_username[username] = user

    all_users = list(users_by_id.values())
    highly_active_ids = {user["id"] for user in all_users[:10]}

    groups: list[dict[str, Any]] = []
    active_groups = list(GROUP_DEFS[:group_count])
    for index, (name, description) in enumerate(active_groups):
        owner = all_users[index % len(all_users)]
        member_sample = rng.sample(all_users, k=min(len(all_users), rng.randint(8, 16)))
        member_ids = {owner["id"], *(member["id"] for member in member_sample)}
        for member_id in member_ids:
            users_by_id[member_id].setdefault("groupsMember", []).append(str(index))

        groups.append(
            {
                "id": str(index),
                "name": name,
                "description": description,
                "userId": owner["id"],
                "events": [],
                "messages": [],
                "memberIds": list(member_ids),
            }
        )

    events: list[dict[str, Any]] = []
    event_names_seen: set[str] = set()
    comment_count = 0
    for index in range(event_count):
        owner = rng.choice(all_users[:20] if index < 30 else all_users)
        linked_group = rng.choice(groups) if rng.random() < 0.45 else None
        venue = rng.choice(UK_PLACES)
        title_seed, base_tags = rng.choice(EVENT_THEMES)
        event_at, end_at = _random_datetime(rng)
        event_name = f"{title_seed} · {venue['city']} #{index + 1}"
        while event_name in event_names_seen:
            event_name = f"{title_seed} · {venue['city']} #{index + 1}-{rng.randint(1, 9)}"
        event_names_seen.add(event_name)

        lat = round(venue["lat"] + rng.uniform(-0.004, 0.004), 6)
        lng = round(venue["lng"] + rng.uniform(-0.004, 0.004), 6)
        tags = list(dict.fromkeys([*base_tags, venue["city"].lower(), rng.choice(("social", "friends", "evening", "weekend"))]))
        event = {
            "id": str(uuid4()),
            "name": event_name,
            "time": event_at.isoformat().replace("+00:00", "Z"),
            "startTime": event_at.isoformat().replace("+00:00", "Z"),
            "endTime": end_at.isoformat().replace("+00:00", "Z"),
            "long": lng,
            "lat": lat,
            "description": f"{title_seed} at {venue['placeName']} in {venue['city']} with a friendly crowd and a clear meet-up point.",
            "tags": tags[:4],
            "eventCreator": owner["username"],
            "userId": owner["id"],
            "username": owner["username"],
            "ongoing": True,
            "placeName": venue["placeName"],
            "placeAddress": venue["placeAddress"],
            "eventImg(s)": [],
            "attendees": [{"userId": owner["id"], "username": owner["username"]}],
            "comments": [],
            "groupName": linked_group["name"] if linked_group else "None",
        }
        if linked_group:
            event["groupId"] = linked_group["id"]

        attendees_pool = (
            [users_by_id[member_id] for member_id in linked_group["memberIds"] if member_id != owner["id"]]
            if linked_group
            else [user for user in all_users if user["id"] != owner["id"]]
        )
        rng.shuffle(attendees_pool)
        target_extra_attendees = rng.randint(2, 9) if owner["id"] in highly_active_ids or index < 40 else rng.randint(0, 4)
        for attendee in attendees_pool[:target_extra_attendees]:
            event["attendees"].append({"userId": attendee["id"], "username": attendee["username"]})

        attendee_ids = {attendee["userId"] for attendee in event["attendees"]}
        for attendee_id in attendee_ids:
            user = users_by_id[attendee_id]
            user.setdefault("eventsAttending", []).append(event["id"])
            if attendee_id != owner["id"]:
                _append_notification(
                    owner,
                    _notification(
                        notification_type="event-join",
                        title="Someone joined your event",
                        body=f"{user['username']} joined {event['name']}.",
                        actor_id=user["id"],
                        actor_username=user["username"],
                        event_id=event["id"],
                        group_id=event.get("groupId"),
                        created_at=(event_at - timedelta(hours=rng.randint(2, 36))).isoformat(),
                    ),
                )

        saved_candidates = [user for user in all_users if user["id"] not in attendee_ids]
        rng.shuffle(saved_candidates)
        for saver in saved_candidates[: rng.randint(2, 6)]:
            saver.setdefault("savedEvents", []).append(event["id"])

        comment_authors = [users_by_id[item["userId"]] for item in event["attendees"]]
        rng.shuffle(comment_authors)
        for author in comment_authors[: rng.randint(0, min(4, len(comment_authors)))]:
            if author["id"] == owner["id"] and rng.random() < 0.75:
                continue
            comment_count += 1
            body = rng.choice(COMMENT_SNIPPETS)
            comment = {
                "id": str(uuid4()),
                "userId": author["id"],
                "username": author["username"],
                "body": body,
                "createdAt": (event_at - timedelta(hours=rng.randint(1, 48))).isoformat(),
            }
            event["comments"].append(comment)
            _append_notification(
                owner,
                _notification(
                    notification_type="event-comment",
                    title="New comment on your event",
                    body=f"{author['username']}: {body[:72]}",
                    actor_id=author["id"],
                    actor_username=author["username"],
                    event_id=event["id"],
                    group_id=event.get("groupId"),
                    created_at=comment["createdAt"],
                ),
            )

        events.append(event)
        if linked_group:
            linked_group["events"].append(event.copy())

    message_count = 0
    for group in groups:
        member_users = [users_by_id[user_id] for user_id in group["memberIds"]]
        for index in range(rng.randint(10, 22)):
            author = rng.choice(member_users)
            body = rng.choice(CHAT_SNIPPETS)
            created_at = (
                datetime.now(timezone.utc) - timedelta(hours=rng.randint(1, 120), minutes=index)
            ).isoformat()
            message_count += 1
            group["messages"].append(
                {
                    "id": str(uuid4()),
                    "userId": author["id"],
                    "username": author["username"],
                    "body": body,
                    "createdAt": created_at,
                }
            )
            for recipient in member_users:
                if recipient["id"] == author["id"] or rng.random() < 0.35:
                    continue
                _append_notification(
                    recipient,
                    _notification(
                        notification_type="group-chat",
                        title=f"New message in {group['name']}",
                        body=f"{author['username']}: {body[:72]}",
                        actor_id=author["id"],
                        actor_username=author["username"],
                        group_id=group["id"],
                        created_at=created_at,
                    ),
                )

    for user in all_users:
        user["eventsAttending"] = list(dict.fromkeys(user.get("eventsAttending", [])))
        user["groupsMember"] = list(dict.fromkeys(user.get("groupsMember", [])))
        user["savedEvents"] = [
            event_id for event_id in dict.fromkeys(user.get("savedEvents", []))
            if event_id not in user["eventsAttending"]
        ][:18]
        user["notifications"] = user.get("notifications", [])[:50]
        repository.create_user(user)

    for group in groups:
        payload = {key: value for key, value in group.items() if key != "memberIds"}
        repository.create_group(payload)

    for event in events:
        repository.create_event(event)

    return SeedStats(
        users=len(all_users),
        events=len(events),
        groups=len(groups),
        comments=comment_count,
        messages=message_count,
        notifications=sum(len(user.get("notifications", [])) for user in all_users),
    )


def _build_repository() -> Any:
    settings = get_settings()
    if settings.use_memory_db:
        return MemoryRepository()
    return MongoRepository(settings.mongodb_uri, settings.database_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Bee2Gether with demo social data.")
    parser.add_argument("--seed-if-empty", action="store_true", help="Only seed when the database is empty.")
    parser.add_argument("--users", type=int, default=DEFAULT_USER_COUNT)
    parser.add_argument("--events", type=int, default=DEFAULT_EVENT_COUNT)
    parser.add_argument("--groups", type=int, default=DEFAULT_GROUP_COUNT)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    args = parser.parse_args()

    repository = _build_repository()
    stats = seed_demo_data(
        repository,
        user_count=args.users,
        event_count=args.events,
        group_count=args.groups,
        reset=not args.seed_if_empty,
        seed_if_empty=args.seed_if_empty,
        random_seed=args.random_seed,
    )
    print(
        f"Seeded Bee2Gether demo data: {stats.users} users, {stats.groups} groups, "
        f"{stats.events} events, {stats.comments} comments, {stats.messages} chat messages, "
        f"{stats.notifications} notifications."
    )
    print(f"Shared login password for seeded users: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
