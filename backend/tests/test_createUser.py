import unittest
import requests
import json
import logging
import os
from azure.cosmos import CosmosClient 

class TestAddPlayerFunction(unittest.TestCase):
    PUBLIC_URL = "http://localhost:8000/createUser"
    TEST_URL = PUBLIC_URL

    # Initialize Cosmos DB client and UsersContainerProxy
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)

    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    BeeDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    UsersContainerProxy = BeeDBProxy.get_container_client(settings['Values']['UsersContainer'])

    # Test data
    player_1 = {"username": "testuser1", "password": "testpassword1"}
    json_player_1 = json.dumps(player_1)
    player_6 = {"username": "testuser6", "password": "testpassword6"}
    json_player_6 = json.dumps(player_6)

    # Invalid players
    player_2_ushort = {"username": "tes", "password": "testpassword2"}
    json_player_2 = json.dumps(player_2_ushort)
    player_3_ulong = {"username": "123456789123456", "password": "testpassword3"}
    json_player_3 = json.dumps(player_3_ulong)
    player_4_pshort = {"username": "testuser4", "password": "testpassw"}
    json_player_4 = json.dumps(player_4_pshort)
    player_5_plong = {"username": "testuser5", "password": "testpasswordtestpassw"}
    json_player_5 = json.dumps(player_5_plong)

    def test_is_valid(self):
        response = requests.put(self.TEST_URL,data=self.json_player_1)
        respjson = response.json()
        print("valid test",respjson)
        self.assertEqual(respjson["result"],True)
        self.assertEqual(respjson["msg"],"OK")

    def test_is_valid_when_people(self):
        response = requests.put(self.TEST_URL,data=self.json_player_1)
        respjson = response.json()
        print("valid test",respjson)
        self.assertEqual(respjson["result"],True)
        self.assertEqual(respjson["msg"],"OK")
        response2 = requests.put(self.TEST_URL,data=self.json_player_6)
        respjson = response2.json()
        print("valid test",respjson)
        self.assertEqual(respjson["result"],True)
        self.assertEqual(respjson["msg"],"OK")

    def test_duplicate_username(self):
        requests.put(self.TEST_URL,data=self.json_player_1)
        response2 = requests.put(self.TEST_URL,data=self.json_player_1)
        respjson = response2.json()
        logging.info(respjson)
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Username already exists")

    def test_is_invalid_username_short(self):
        response = requests.put(self.TEST_URL,data=self.json_player_2)
        respjson = response.json()
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Username less than 4 characters or more than 14 characters")

    def test_is_invalid_username_long(self):
        response = requests.put(self.TEST_URL,data=self.json_player_3)
        respjson = response.json()
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Username less than 4 characters or more than 14 characters")

    def test_is_invalid_password_short(self):
        response = requests.put(self.TEST_URL,data=self.json_player_4)
        respjson = response.json()
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Password less than 10 characters or more than 20 characters")

    def test_is_invalid_password_long(self):
        response = requests.put(self.TEST_URL,data=self.json_player_5)
        respjson = response.json()
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Password less than 10 characters or more than 20 characters")

    def tearDown(self) -> None:
            # Teardown to delete all test users created during the tests
            try:
                for doc in self.UsersContainerProxy.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
                    self.UsersContainerProxy.delete_item(item=doc['id'], partition_key=doc['id'])
            except Exception as e:
                logging.error(f"Error in tearDown: {str(e)}")
