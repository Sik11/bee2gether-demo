import unittest
import os
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

os.environ.setdefault("USE_MEMORY_DB", "true")

from backend.main import app, repository
from backend.seed_demo_data import seed_demo_data


class FastApiCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        if hasattr(repository, "clear_all"):
            repository.clear_all()
        else:
            if hasattr(repository, "users"):
                repository.users.clear()
            if hasattr(repository, "events"):
                repository.events.clear()
            if hasattr(repository, "groups"):
                repository.groups.clear()
        self.client = TestClient(app)

    def test_create_user_and_login(self) -> None:
        register_response = self.client.put(
            "/api/createUser",
            json={"username": "testuser", "password": "testpassword1"},
        )
        self.assertEqual(register_response.status_code, 200)
        register_payload = register_response.json()
        self.assertTrue(register_payload["result"])

        login_response = self.client.post(
            "/api/loginUser",
            json={"username": "testuser", "password": "testpassword1"},
        )
        self.assertEqual(login_response.status_code, 200)
        login_payload = login_response.json()
        self.assertTrue(login_payload["result"])
        self.assertEqual(login_payload["msg"], "OK")

    def test_group_and_event_flow(self) -> None:
        user_payload = self.client.put(
            "/api/createUser",
            json={"username": "groupowner", "password": "testpassword2"},
        ).json()
        user_id = user_payload["userId"]

        group_payload = self.client.post(
            "/api/createGroup",
            json={"name": "Weekend Crew", "description": "Friends", "userId": user_id},
        ).json()
        self.assertTrue(group_payload["result"])
        group_id = group_payload["groupId"]

        event_payload = self.client.put(
            "/api/createEvent",
            json={
                "name": "Picnic",
                "time": "2026-04-01",
                "long": -1.4,
                "lat": 50.9,
                "description": "Park meetup",
                "tags": ["outdoors"],
                "userId": user_id,
                "groupId": group_id,
            },
        ).json()
        self.assertTrue(event_payload["result"])

        groups_response = self.client.get("/api/getAllGroups")
        self.assertEqual(groups_response.status_code, 200)
        groups_payload = groups_response.json()
        self.assertEqual(len(groups_payload["groups"]), 1)
        self.assertEqual(len(groups_payload["groups"][0]["events"]), 1)

        map_events = self.client.post(
            "/api/getMapEvents",
            json={
                "bottomLeftLong": -2,
                "bottomLeftLat": 50,
                "upperRightLong": 0,
                "upperRightLat": 52,
            },
        ).json()
        self.assertTrue(map_events["result"])
        self.assertEqual(len(map_events["events"]), 1)
        self.assertEqual(map_events["events"][0]["status"], "upcoming")

    def test_continue_as_guest_returns_stable_browser_scoped_user(self) -> None:
        first = self.client.post(
            "/api/continueAsGuest",
            json={"guestSessionId": "browser-guest-1"},
        )
        self.assertEqual(first.status_code, 200)
        first_payload = first.json()
        self.assertTrue(first_payload["result"])
        self.assertTrue(first_payload["username"].startswith("guest-"))

        repeat = self.client.post(
            "/api/continueAsGuest",
            json={"guestSessionId": "browser-guest-1"},
        ).json()
        self.assertEqual(repeat["userId"], first_payload["userId"])
        self.assertEqual(repeat["username"], first_payload["username"])

        second = self.client.post(
            "/api/continueAsGuest",
            json={"guestSessionId": "browser-guest-2"},
        ).json()
        self.assertNotEqual(second["userId"], first_payload["userId"])
        self.assertNotEqual(second["username"], first_payload["username"])

    def test_expired_events_are_removed_from_discovery_and_storage(self) -> None:
        user_payload = self.client.put(
            "/api/createUser",
            json={"username": "cleanupuser", "password": "testpassword3"},
        ).json()
        user_id = user_payload["userId"]

        expired_date = (datetime.now(timezone.utc) - timedelta(days=10)).date().isoformat()
        fresh_date = (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()

        expired_payload = self.client.put(
            "/api/createEvent",
            json={
                "name": "Expired Picnic",
                "time": expired_date,
                "long": -1.45,
                "lat": 50.91,
                "description": "Old meetup",
                "tags": ["old"],
                "userId": user_id,
            },
        ).json()
        self.assertTrue(expired_payload["result"])

        fresh_payload = self.client.put(
            "/api/createEvent",
            json={
                "name": "Fresh Picnic",
                "time": fresh_date,
                "long": -1.46,
                "lat": 50.92,
                "description": "Upcoming meetup",
                "tags": ["new"],
                "userId": user_id,
            },
        ).json()
        self.assertTrue(fresh_payload["result"])

        map_events = self.client.post(
            "/api/getMapEvents",
            json={
                "bottomLeftLong": -2,
                "bottomLeftLat": 50,
                "upperRightLong": 0,
                "upperRightLat": 52,
            },
        ).json()
        self.assertTrue(map_events["result"])
        self.assertEqual([event["name"] for event in map_events["events"]], ["Fresh Picnic"])

        attending_events = self.client.post(
            "/api/getAttendingEvents",
            json={"userId": user_id},
        ).json()
        self.assertEqual([event["name"] for event in attending_events["attendingEvents"]], ["Fresh Picnic"])

        self.assertIsNone(repository.get_event_by_id(expired_payload["eventId"]))
        self.assertIsNotNone(repository.get_event_by_id(fresh_payload["eventId"]))

    def test_comments_notifications_chat_and_export_flow(self) -> None:
        owner = self.client.put(
            "/api/createUser",
            json={"username": "owneruser", "password": "testpassword4"},
        ).json()
        member = self.client.put(
            "/api/createUser",
            json={"username": "memberuser", "password": "testpassword5"},
        ).json()

        group_payload = self.client.post(
            "/api/createGroup",
            json={"name": "Study Hive", "description": "Friends", "userId": owner["userId"]},
        ).json()
        group_id = group_payload["groupId"]

        join_group = self.client.post(
            "/api/joinGroup",
            json={"userId": member["userId"], "groupId": group_id},
        ).json()
        self.assertTrue(join_group["result"])

        event_payload = self.client.put(
            "/api/createEvent",
            json={
                "name": "Revision Jam",
                "time": "2026-04-05",
                "long": -1.4,
                "lat": 50.9,
                "description": "Bring notes",
                "tags": ["study"],
                "userId": owner["userId"],
                "groupId": group_id,
            },
        ).json()
        event_id = event_payload["eventId"]

        comment_payload = self.client.post(
            "/api/addEventComment",
            json={"eventId": event_id, "userId": member["userId"], "body": "I am in."},
        ).json()
        self.assertTrue(comment_payload["result"])

        comments = self.client.post(
            "/api/getEventComments",
            json={"eventId": event_id},
        ).json()
        self.assertEqual(len(comments["comments"]), 1)

        message_payload = self.client.post(
            "/api/sendGroupChatMessage",
            json={"groupId": group_id, "userId": member["userId"], "body": "See you there"},
        ).json()
        self.assertTrue(message_payload["result"])

        messages = self.client.post(
            "/api/getGroupChatMessages",
            json={"groupId": group_id, "userId": owner["userId"]},
        ).json()
        self.assertEqual(len(messages["messages"]), 1)

        notifications = self.client.post(
            "/api/getNotifications",
            json={"userId": owner["userId"]},
        ).json()
        self.assertGreaterEqual(notifications["unreadCount"], 2)

        export_response = self.client.get("/api/exportEventIcs", params={"eventId": event_id})
        self.assertEqual(export_response.status_code, 200)
        self.assertIn("BEGIN:VCALENDAR", export_response.text)

    def test_seed_demo_data_creates_uk_social_dataset(self) -> None:
        stats = seed_demo_data(
            repository,
            user_count=50,
            event_count=75,
            group_count=12,
            reset=True,
            random_seed=20260331,
        )

        self.assertEqual(stats.users, 50)
        self.assertEqual(stats.events, 75)
        self.assertEqual(stats.groups, 12)
        self.assertGreater(stats.comments, 0)
        self.assertGreater(stats.messages, 0)
        self.assertGreater(stats.notifications, 0)

        users = repository.list_users()
        events = repository.list_events()
        groups = repository.list_groups()
        self.assertEqual(len(users), 50)
        self.assertEqual(len(events), 75)
        self.assertEqual(len(groups), 12)
        self.assertTrue(all(event["lat"] >= 49 for event in events))
        self.assertTrue(all(event["lat"] <= 57 for event in events))
        self.assertTrue(all(event["long"] >= -5 for event in events))
        self.assertTrue(all(event["long"] <= 1 for event in events))
        self.assertTrue(all(event.get("placeName") for event in events))
        self.assertTrue(all(event.get("startTime") for event in events))
        self.assertTrue(all(event.get("endTime") for event in events))


if __name__ == "__main__":
    unittest.main()
