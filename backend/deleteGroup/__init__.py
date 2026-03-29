import logging
import os
import json
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos import CosmosClient
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies outside of the main function if possible
# to take advantage of connection reuse
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
GroupsContainerProxy = BeeDBProxy.get_container_client(os.environ['GroupsContainer'])
UsersToGroupsContainerProxy = BeeDBProxy.get_container_client(os.environ["UsersToGroupsContainer"])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to delete group')

    group_input = req.get_json()
    logging.info(group_input)
    
    try:
        # Query for the group with the given group ID
        group_query = list(GroupsContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": group_input["groupId"]}],
            enable_cross_partition_query=True
        ))

        # if the group ID cannot be found in the JSON file, return a status error code of 400
        if not group_query:
            return HttpResponse(json.dumps({"result": False, "msg": "Group not found"}), status_code=400, mimetype="application/json")

        group_data = group_query[0]

        # Delete the group from the groups container
        GroupsContainerProxy.delete_item(item=group_data)

        # Remove the group from the usersToGroups container
        UsersToGroupsContainerProxy.delete_item(item={"userId": group_input["userId"], "groupId": [group_data.get("id")]})

        return HttpResponse(json.dumps({"result": True, "msg": "Group deleted successfully", "groupId": group_data.get("id")}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")