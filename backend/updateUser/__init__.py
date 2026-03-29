from azure.cosmos import CosmosClient
import os
from azure.cosmos.exceptions import CosmosHttpResponseError
import json
import logging
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies outside of the main function if possible
# to take advantage of connection reuse
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
UsersContainerProxy = BeeDBProxy.get_container_client(os.environ['UsersContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to update user')

    input_data = req.get_json()
    logging.info(input_data)

    # Ensure the username is in request. Will need to also check if the update field is in the request
    if "username" not in input_data:
        return HttpResponse(json.dumps({"result": False, "msg": "Username is required"}), status_code=400, mimetype="application/json")

    # search for the user in the users cosmosDB
    try:
        user_query = list(UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.username = @username",
            parameters=[{"name": "@username", "value": input_data["username"]}],
            enable_cross_partition_query=True
        ))

        # if user is not found, return an appropriate error message
        if not user_query:
            return HttpResponse(json.dumps({"result": False, "msg": "User not found"}), status_code=400, mimetype="application/json")

        # What exactly are we updating the user with when we call this function?
        existing_user_data = user_query[0]
        existing_user_data.update(input_data)
        UsersContainerProxy.replace_item(item=existing_user_data)

        return HttpResponse(json.dumps({"result": True, "msg": "User updated successfully", "userId": input_data["userId"]}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")