import unittest
import requests
import json
from azure.cosmos import CosmosClient

class TestCreateEventFunction(unittest.TestCase):
    CREATE_EVENT_URL = "http://localhost:8000/createEvent"
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
    "name":"southamponEvent6",
    "time":"14 23 01 24",
    "long": -1.404351,
    "lat": 50.909698,
    "description":"really cool event",
    "tag(s)":["cool","late"],
    "userId":"f4bdcb63-2445-471f-bf35-e5ccd96daad3"
    }
    eventId=0

    def setUp(self) -> None:
        # Create a test user before running the tests
        requests.put(self.SETUP_USER_URL, data=json.dumps(self.test_user))

    def test_create_event_success(self):
        # Test successful event creation
        response = requests.put(self.CREATE_EVENT_URL, data=json.dumps(self.test_event))
        respjson = response.json()
        self.assertEqual(respjson["result"], True)
        self.assertEqual(respjson["msg"], "Event created successfully")
        self.eventId = respjson["eventId"]

    def test_create_event_duplicate(self):
        # Test creating an event with a duplicate name
        response=requests.put(self.CREATE_EVENT_URL, data=json.dumps(self.test_event))  # Create event first time
        respjson = response.json()
        self.eventId = respjson["eventId"]
        response = requests.put(self.CREATE_EVENT_URL, data=json.dumps(self.test_event))  # Attempt to create duplicate event
        respjson = response.json()
        self.assertEqual(respjson["result"], False)
        self.assertEqual(respjson["msg"], "Event name already exists")

def tearDown(self) -> None:
    # Assuming you know the IDs of the documents to delete

    self.EventsContainerProxy.delete_item(item="document_id_here", partition_key="partition_key_value")



if __name__ == '__main__':
    unittest.main()
