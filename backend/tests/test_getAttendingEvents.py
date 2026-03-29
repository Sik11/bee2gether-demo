import unittest
import requests
import json
from azure.cosmos import CosmosClient

class TestGetAttendingEventsFunction(unittest.TestCase):
    GET_ATTENDING_EVENTS_URL = "http://localhost:8000/getAttendingEvents"
    SETUP_EVENT_URL = "http://localhost:8000/createEvent"
    SETUP_USER_URL = "http://localhost:8000/createUser"

    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    BeeDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    UsersContainerProxy = BeeDBProxy.get_container_client(settings['Values']['UsersContainer'])
    EventsContainerProxy = BeeDBProxy.get_container_client(settings['Values']['EventsContainer'])

    test_user = {"username": "testuser", "password": "testpassword"}
    test_event = {
        "name": "testEvent",
        "time": "14 23 01 24",
        "long": -1.404351,
        "lat": 50.909698,
        "description": "test event",
        "tag(s)": ["test"],
        "userId": "testUserId"
    }

    def setUp(self) -> None:
        # Setup a test user and event
        requests.put(self.SETUP_USER_URL, data=json.dumps(self.test_user))
        event_response = requests.put(self.SETUP_EVENT_URL, data=json.dumps(self.test_event))
        self.test_event_id = event_response.json().get('eventId')

        # Add the event to the user's attending list
        add_event_data = {"username": self.test_user["username"], "eventId": self.test_event_id}
        requests.put("YourAddEventURL", data=json.dumps(add_event_data))  

    def test_get_attending_events_success(self):
        # Test retrieving attending events for a user
        data = {"username": self.test_user["username"]}
        response = requests.post(self.GET_ATTENDING_EVENTS_URL, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], True)
        self.assertIn(self.test_event_id, [event['id'] for event in respjson.get("attendingEvents", [])])

    def test_get_attending_events_no_user(self):
        # Test retrieving events for a non-existing user
        data = {"username": "nonExistingUser"}
        response = requests.post(self.GET_ATTENDING_EVENTS_URL, data=json.dumps(data))
        self.assertEqual(response.status_code, 400)
        respjson = response.json()
        self.assertEqual(respjson["result"], False)

    def tearDown(self) -> None:
        # Delete test user
        user_query = f"SELECT * FROM c WHERE c.username = '{self.test_user['username']}'"
        user_items = list(self.UsersContainerProxy.query_items(query=user_query, enable_cross_partition_query=True))
        if user_items:
            self.UsersContainerProxy.delete_item(item=user_items[0], partition_key=user_items[0]['id'])

        # Delete test event
        event_query = f"SELECT * FROM c WHERE c.id = '{self.test_event_id}'"
        event_items = list(self.EventsContainerProxy.query_items(query=event_query, enable_cross_partition_query=True))
        if event_items:
            self.EventsContainerProxy.delete_item(item=event_items[0], partition_key=event_items[0]['id'])


if __name__ == '__main__':
    unittest.main()
