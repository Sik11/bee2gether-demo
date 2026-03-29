from azure.cosmos import CosmosClient 
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
import os
import json
import logging

# Initialize Cosmos DB client and proxies
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
UsersContainerProxy = BeeDBProxy.get_container_client(os.environ['UsersContainer'])
GroupsContainerProxy = BeeDBProxy.get_container_client(os.environ['GroupsContainer'])  # Assuming this is your groups container

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP trigger function processed a request for getting all groups a member belongs to.')

    input_data = req.get_json()
    logging.info(input_data)

    query_field = None
    query_value = None

    # store the userID or username, depending on what parameter was used to search for
    if "userId" in input_data:
        query_field = "id"
        query_value = input_data["userId"]
    elif "username" in input_data:
        query_field = "username"
        query_value = input_data["username"]
    # if neither was available, return a status error code of 400
    else:
        return HttpResponse(body=json.dumps({"result": False, "msg": "Username or UserId is required"}), status_code=400, mimetype="application/json")

    # search for the user in the users cosmosDB
    try:
        userQuery = UsersContainerProxy.query_items(
            query=f"SELECT * FROM c WHERE c.{query_field} = @{query_field}",
            parameters=[{"name": f"@{query_field}", "value": query_value}],
            enable_cross_partition_query=True
        )
        user = list(userQuery)

        if user:
            user_data = user[0]

            logging.info("User data retrieved successfully.")

            # Retrieve the list of group IDs the user is a member of
            memberGroupsIds = user_data.get("groupsMember", [])

            # Query for each group detail
            memberGroups = []
            for groupId in memberGroupsIds:
                groupQuery = GroupsContainerProxy.query_items(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": groupId}],
                    enable_cross_partition_query=True
                )
                group = list(groupQuery)

                # if found, add the group to the total groups the user is a member of
                if group:
                    memberGroups.append(group[0])

            return HttpResponse(body=json.dumps({"result": True, "msg": "OK", "userId": user_data.get("id"), "memberGroups": memberGroups}), status_code=200, mimetype="application/json")
        else:
            logging.info("User not found.")
            return HttpResponse(body=json.dumps({"result": False, "msg": "User not found."}), status_code=400, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        logging.error('Cosmos DB error: %s', str(cosmos_err))
        return HttpResponse(body=json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(body=json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")
