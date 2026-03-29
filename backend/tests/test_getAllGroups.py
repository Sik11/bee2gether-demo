import unittest
import requests
import json
from azure.cosmos import CosmosClient

class TestGetAllGroupsFunction(unittest.TestCase):
    GET_ALL_GROUPS_URL = "http://localhost:8000/getAllGroups"

    # Initialize Cosmos DB client and containers
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    BeeDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    GroupsContainerProxy = BeeDBProxy.get_container_client(settings['Values']['GroupsContainer'])

    test_groups = [
        {"name": "testGroup1", "description": "Test group 1"},
        {"name": "testGroup2", "description": "Test group 2"}
    ]

    def setUp(self) -> None:
        # Setup test groups
        for group in self.test_groups:
            self.GroupsContainerProxy.upsert_item(group)

    def test_get_all_groups_success(self):
        # Test retrieving all groups successfully
        response = requests.get(self.GET_ALL_GROUPS_URL)
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], True)
        self.assertIn("groups", respjson)
        self.assertEqual(len(respjson["groups"]), len(self.test_groups))

    def test_no_groups_found(self):
        # Test when no groups are found
        for group in self.test_groups:
            self.GroupsContainerProxy.delete_item(item=group['name'], partition_key=group['name'])
        response = requests.get(self.GET_ALL_GROUPS_URL)
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], True)
        self.assertEqual(respjson["msg"], "No groups found")
        self.assertEqual(len(respjson["groups"]), 0)


    def tearDown(self) -> None:
        # Delete test groups
        for group in self.test_groups:
            self.GroupsContainerProxy.delete_item(item=group['name'], partition_key=group['name'])

if __name__ == '__main__':
    unittest.main()
