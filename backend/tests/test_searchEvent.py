import unittest
import requests
import json
from azure.cosmos import CosmosClient

class TestSearchEventsFunction(unittest.TestCase):
    SEARCH_EVENTS_URL = "http://localhost:8000/searchEvent"
    CREATE_EVENT_URL = "http://localhost:8000/createEvent"
    SETUP_USER_URL = "http://localhost:8000/createUser"

    test_user = {"username": "testuser", "password": "testpassword"}
    test_events = [
        {"name": "Event1", "details": "Details of Event 1", "userId": "testUserId"},
        {"name": "Event2", "details": "Details of Event 2", "userId": "testUserId"}
    ]
    created_event_ids = []

    def setUp(self) -> None:
        # Create a test user
        requests.put(self.SETUP_USER_URL, json=self.test_user)

        # Create test events
        for event in self.test_events:
            response = requests.put(self.CREATE_EVENT_URL, json=event)
            respjson = response.json()
            if respjson["result"]:
                self.created_event_ids.append(respjson["eventId"])

    def test_search_events_success(self):
        # Test searching events successfully
        response = requests.post(self.SEARCH_EVENTS_URL, json={"name": "Event1"})
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], True)
        self.assertIn("events", respjson)

    def test_event_not_found(self):
        # Test searching for a non-existent event
        response = requests.post(self.SEARCH_EVENTS_URL, json={"name": "NonExistentEvent"})
        self.assertEqual(response.status_code, 400)
        respjson = response.json()
        self.assertEqual(respjson["result"], False)
        self.assertEqual(respjson["msg"], "Event not found")

    def test_missing_event_name(self):
        # Test with missing event name
        response = requests.post(self.SEARCH_EVENTS_URL, json={})
        self.assertEqual(response.status_code, 400)
        respjson = response.json()
        self.assertEqual(respjson["result"], False)
        self.assertEqual(respjson["msg"], "Event name not found")


    def tearDown(self) -> None:
        # Delete test events
        for event in self.test_events:
            self.EventsContainerProxy.delete_item(item=event['name'], partition_key=event['name'])

if __name__ == '__main__':
    unittest.main()
