import logging
from azure.cosmos.exceptions import CosmosHttpResponseError
import json
import os
from azure.cosmos import CosmosClient
from azure.functions import HttpRequest, HttpResponse

MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
UsersContainerProxy = BeeDBProxy.get_container_client(os.environ['UsersContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to get user information')

    user_input = req.get_json()

    # if the query does not contain the searched username, return an error status message of 400
    if "username" not in user_input:
        return HttpResponse(json.dumps({"result": False, "msg": "Username not found"}), status_code=400, mimetype="application/json")
    
    username = user_input["username"]

    # search for the user in the user cosmosDB
    try:
        query = "SELECT * FROM c WHERE c.username = @username"
        users = list(UsersContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@username", "value": username}],
            enable_cross_partition_query=True
        ))

        # if no user was found, return a status error message to indicate
        if not users:
            return HttpResponse(json.dumps({"result": False, "msg": "User not found"}), status_code=400, mimetype="application/json")
        
        # otherwise, return the information on the user from the database
        userInfo = users[0]
        return HttpResponse(json.dumps({"result": True, "user": userInfo}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmoserr:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmoserr)}), status_code=500,mimetype="application/json")
    except Exception as err:
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(err)}), status_code=500,mimetype="application/json")
