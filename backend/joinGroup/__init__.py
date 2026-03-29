import logging
import os
import json
from azure.cosmos import CosmosClient 
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
UsersContainerProxy = BeeDBProxy.get_container_client(os.environ['UsersContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP trigger function processed a request for a user to join a group.')

    input_data = req.get_json()
    logging.info(input_data)

    # Check for necessary input fields
    if "userId" not in input_data or "groupId" not in input_data:
        return HttpResponse(json.dumps({"result": False, "msg": "UserId and GroupId are required"}), status_code=400, mimetype="application/json")

    user_id = input_data["userId"]
    group_id = input_data["groupId"]

    try:
        # Retrieve the user's current data
        user_query = UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": user_id}],
            enable_cross_partition_query=True
        )
        user_data = list(user_query)

        # if there does not exists the searched for user in the database, return a status error message of 404
        if not user_data:
            return HttpResponse(json.dumps({"result": False, "msg": "User not found"}), status_code=404, mimetype="application/json")

        user_data = user_data[0]

        # Check if the user is already a member of the group
        if group_id in user_data.get("groupsMember", []):
            return HttpResponse(json.dumps({"result": False, "msg": "User already a member of the group"}), status_code=400, mimetype="application/json")

        # Add group ID to the user's groupsMember list
        user_groups = user_data.get("groupsMember", [])
        user_groups.append(group_id)
        user_data["groupsMember"] = user_groups

        # Update the user document in Cosmos DB
        UsersContainerProxy.replace_item(item=user_data["id"], body=user_data)

        return HttpResponse(json.dumps({"result": True, "msg": "Joined group successfully"}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        logging.error('Cosmos DB error: %s', str(cosmos_err))
        return HttpResponse(json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")
