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

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to get all groups')

    try:
        # Query to get all groups
        groups_query = list(GroupsContainerProxy.query_items(
            query="SELECT * FROM c",
            enable_cross_partition_query=True
        ))

        # If no groups are found, return an appropriate message
        if not groups_query:
            return HttpResponse(json.dumps({"result": True, "msg": "No groups found", "groups": []}), mimetype="application/json")

        # Return all found groups
        return HttpResponse(json.dumps({"result": True, "msg": "Groups retrieved successfully", "groups": groups_query}), mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        logging.error('Cosmos DB error: %s', str(cosmos_err))
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")
