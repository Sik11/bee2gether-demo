import unittest
import os

from fastapi.testclient import TestClient

os.environ.setdefault("USE_MEMORY_DB", "true")

from backend.main import app, repository


class FastApiCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
