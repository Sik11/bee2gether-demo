import unittest
import requests
import json
from azure.cosmos import CosmosClient

class TestGetEventInformationFunction(unittest.TestCase):
    GET_EVENT_INFO_URL = "http://localhost:8000/getEventInfo"

    test_event = {
        "id": "0",  
        "name": "Test Event",
        "date": "2024-01-01",
    }
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    BeeDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    GroupsContainerProxy = BeeDBProxy.get_container_client(settings['Values']['GroupsContainer'])
    UsersToGroupsContainerProxy = BeeDBProxy.get_container_client(settings['Values']['UsersToGroupsContainer'])
    EventsContainerProxy = BeeDBProxy.get_container_client(settings['Values']['EventsContainer'])
    def setUp(self):
        # Create a test event in the database

        requests.post("http://localhost:8000/createEvent", json=self.test_event)

    def test_get_event_info_success(self):
        # Test retrieving existing event information
        test_event_id = "existing_event_id"  # Replace with a valid event ID
        response = requests.post(self.GET_EVENT_INFO_URL, json={"eventId": test_event_id})
        self.assertEqual(response.status_code, 200)
        resp_json = response.json()
        self.assertTrue(resp_json["result"])
        self.assertIn("eventInfo", resp_json)
        self.assertEqual(resp_json["eventInfo"]["id"], test_event_id)

    def test_get_event_info_nonexistent_event(self):
        # Test retrieving non-existent event information
        test_event_id = "nonexistent_event_id"  # Use an invalid event ID
        response = requests.post(self.GET_EVENT_INFO_URL, json={"eventId": test_event_id})
        self.assertEqual(response.status_code, 400)
        resp_json = response.json()
        self.assertFalse(resp_json["result"])
        self.assertEqual(resp_json["msg"], "Event not found")

    def test_get_event_info_no_event_id(self):
        # Test retrieving event information without providing an event ID
        response = requests.post(self.GET_EVENT_INFO_URL, json={})
        self.assertEqual(response.status_code, 400)
        resp_json = response.json()
        self.assertFalse(resp_json["result"])
        self.assertEqual(resp_json["msg"], "Event ID is required")

    def tearDownClass(self):
        # Delete the test event from the database
        self.EventsContainerProxy.delete_item(item=self.test_event["id"], partition_key=self.test_event["id"])

if __name__ == '__main__':
    unittest.main()
