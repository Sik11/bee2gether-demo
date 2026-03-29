import unittest
import requests
import json
from azure.cosmos import CosmosClient
class TestAddAttendingEventFunction(unittest.TestCase):
    ADD_ATTENDING_EVENT_URL = "http://localhost:8000/addAttendingEvent"
    SETUP_EVENT_URL = "http://localhost:8000/createEvent"
    SETUP_USER_URL = "http://localhost:8000/createUser"

        # Initialize Cosmos DB client and containers
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
        requests.put(self.SETUP_EVENT_URL, data=json.dumps(self.test_event))

    def test_add_attending_event_success(self):
        # Test adding an event to a user's attending list successfully
        data = {"username": self.test_user["username"], "eventId": "testEventId"}
        response = requests.put(self.ADD_ATTENDING_EVENT_URL, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], True)

    def test_add_attending_event_no_user(self):
        # Test adding an event to a non-existing user
        data = {"username": "nonExistingUser", "eventId": "testEventId"}
        response = requests.put(self.ADD_ATTENDING_EVENT_URL, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], False)

    def test_add_attending_event_no_event(self):
        # Test adding a non-existing event to a user's attending list
        data = {"username": self.test_user["username"], "eventId": "nonExistingEventId"}
        response = requests.put(self.ADD_ATTENDING_EVENT_URL, data=json.dumps(data))
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], False)

    def tearDown(self) -> None:
        # Delete test user
        user_query = f"SELECT * FROM c WHERE c.username = '{self.test_user['username']}'"
        user_items = list(self.UsersContainerProxy.query_items(query=user_query, enable_cross_partition_query=True))
        if user_items:
            self.UsersContainerProxy.delete_item(item=user_items[0]['id'], partition_key=user_items[0]['id'])

        # Delete test event
        event_query = f"SELECT * FROM c WHERE c.name = '{self.test_event['name']}'"
        event_items = list(self.EventsContainerProxy.query_items(query=event_query, enable_cross_partition_query=True))
        if event_items:
            self.EventsContainerProxy.delete_item(item=event_items[0]['id'], partition_key=event_items[0]['id'])


if __name__ == '__main__':
    unittest.main()
