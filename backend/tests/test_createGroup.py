import unittest
import requests
import json
from azure.cosmos import CosmosClient

class TestCreateGroupFunction(unittest.TestCase):
    CREATE_GROUP_URL = "http://localhost:8000/createGroup"
    SETUP_USER_URL = "http://localhost:8000/createUser"

    # Initialize Cosmos DB client and containers
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    BeeDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    GroupsContainerProxy = BeeDBProxy.get_container_client(settings['Values']['GroupsContainer'])
    UsersToGroupsContainerProxy = BeeDBProxy.get_container_client(settings['Values']['UsersToGroupsContainer'])

    test_user = {"username": "testuser", "password": "testpassword"}
    test_group = {"name": "testGroup", "userId": "testUserId"}

    def setUp(self) -> None:
        # Setup a test user
        requests.put(self.SETUP_USER_URL, data=json.dumps(self.test_user))

    def test_create_group_success(self):
        # Test creating a group successfully
        response = requests.post(self.CREATE_GROUP_URL, data=json.dumps(self.test_group))
        self.assertEqual(response.status_code, 200)
        respjson = response.json()
        self.assertEqual(respjson["result"], True)
        self.assertIn("groupId", respjson)

    def test_create_group_duplicate_name(self):
        # Test creating a group with a duplicate name
        requests.post(self.CREATE_GROUP_URL, data=json.dumps(self.test_group))
        response = requests.post(self.CREATE_GROUP_URL, data=json.dumps(self.test_group))
        self.assertEqual(response.status_code, 400)
        respjson = response.json()
        self.assertEqual(respjson["result"], False)

    def tearDown(self) -> None:
        # Delete test user and groups
        user_query = f"SELECT * FROM c WHERE c.username = '{self.test_user['username']}'"
        user_items = list(self.UsersToGroupsContainerProxy.query_items(query=user_query, enable_cross_partition_query=True))
        for user_item in user_items:
            self.UsersToGroupsContainerProxy.delete_item(item=user_item['id'], partition_key=user_item['id'])

        group_query = "SELECT * FROM c WHERE c.name = @name"
        group_items = list(self.GroupsContainerProxy.query_items(query=group_query, parameters=[{"name": "@name", "value": self.test_group["name"]}], enable_cross_partition_query=True))
        for group_item in group_items:
            self.GroupsContainerProxy.delete_item(item=group_item['id'], partition_key=group_item['id'])

if __name__ == '__main__':
    unittest.main()
