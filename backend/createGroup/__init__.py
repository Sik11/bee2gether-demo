from azure.cosmos import CosmosClient
import os
import json
import logging
from azure.functions import HttpRequest, HttpResponse
from azure.cosmos.exceptions import CosmosHttpResponseError

# Initialize Cosmos DB client and proxies outside of the main function if possible
# to take advantage of connection reuse
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
GroupsContainerProxy = BeeDBProxy.get_container_client(os.environ['GroupsContainer'])
UsersToGroupsContainerProxy = BeeDBProxy.get_container_client(os.environ["UsersToGroupsContainer"])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to create group')

    group_input = req.get_json()
    logging.info(group_input)
    
    try:
        # Check if a group with the same name already exists
        existing_group = list(GroupsContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.name = @name",
            parameters=[{"name": "@name", "value": group_input["name"]}],
            enable_cross_partition_query=True
        ))
        
        if len(existing_group) > 0:
            return HttpResponse(json.dumps({"result": False, "msg": "Group name already exists"}), status_code=400, mimetype="application/json")
        
        # set the group's event number to 0
        group_input["events"]=[]
        
        # Create the group item and retrieve the result
        group_item_response = GroupsContainerProxy.create_item(group_input,enable_automatic_id_generation=True)

        group_id = group_item_response.get('id')

        # Add user to the usersToGroups container
        user_to_group_item = {
            "userId": group_input["userId"],
            "groupId": [group_id]
        }
        UsersToGroupsContainerProxy.create_item(user_to_group_item,enable_automatic_id_generation=True)

        # Extract the ID from the created item response

        
        return HttpResponse(json.dumps({"result": True, "msg": "Group created successfully", "groupId": group_id}), status_code=200,mimetype="application/json")
    except CosmosHttpResponseError as cosmoserr:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmoserr)}), status_code=500, mimetype="application/json")
