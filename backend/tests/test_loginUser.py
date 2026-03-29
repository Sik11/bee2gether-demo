import unittest
import requests
import json
import logging
import os
from azure.cosmos import CosmosClient 

class TestAddPlayerFunction(unittest.TestCase):
    PUBLIC_URL = "http://localhost:8000/loginUser"
    TEST_URL = PUBLIC_URL

    SETUP_URL="http://localhost:8000/createUser"
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
    player_1 = {"username":"testuser1","password":"testpassword1"}
    json_player_1 = json.dumps(player_1)

    #invalid players

    def setUp(self) -> None:
        response = requests.put(self.SETUP_URL,data=self.json_player_1)

    def test_success_login(self):
        loginSuccess={"username":"testuser1","password":"testpassword1"}
        json_loginSuccess = json.dumps(loginSuccess)
        response = requests.post(self.TEST_URL,data=json_loginSuccess)
        respjson = response.json()
        print(respjson)
        self.assertEqual(respjson["result"],True)
        self.assertEqual(respjson["msg"],"OK")

    def test_fail_login_password(self):
        loginFail={"username":"testuser1","password":"testpassword2"}
        json_loginFail = json.dumps(loginFail)
        response = requests.post(self.TEST_URL,data=json_loginFail)
        respjson = response.json()
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Username or password incorrect")
    
    def test_fail_login_username(self):
        loginFail={"username":"testuser2","password":"testpassword1"}
        json_loginFail = json.dumps(loginFail)
        response = requests.post(self.TEST_URL,data=json_loginFail)
        respjson = response.json()
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Username or password incorrect")

    def test_fail_login_username_password(self):
        loginFail={"username":"testuser2","password":"testpassword2"}
        json_loginFail = json.dumps(loginFail)
        response = requests.post(self.TEST_URL,data=json_loginFail)
        respjson = response.json()
        self.assertEqual(respjson["result"],False)
        self.assertEqual(respjson["msg"],"Username or password incorrect")

    def tearDown(self) -> None:
       for doc in self.UsersContainerProxy.read_all_items():
          self.UsersContainerProxy.delete_item(item=doc,partition_key=doc['id'])
