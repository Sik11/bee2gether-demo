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
GroupsContainerProxy = BeeDBProxy.get_container_client(os.environ['GroupsContainer'])
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP trigger function processed a request to get all events for the groups a user is a member of.')

    input_data = req.get_json()
    logging.info(input_data)

    # Check if userId is provided
    if "userId" not in input_data:
        return HttpResponse(json.dumps({"result": False, "msg": "UserId is required"}), status_code=400, mimetype="application/json")

    user_id = input_data["userId"]

    try:
        # Retrieve the user's data
        user_query = UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": user_id}],
            enable_cross_partition_query=True
        )
        user_data = list(user_query)

        # if the user cannot be found, return a status error code of 404
        if not user_data:
            return HttpResponse(json.dumps({"result": False, "msg": "User not found"}), status_code=404, mimetype="application/json")

        # set the parameters to search for in the groups cosmosDB
        user_data = user_data[0]
        group_ids = user_data.get("groupsMember", [])
        all_group_events = []

        # Retrieve events for each group and fetch their details from the Events container
        for group_id in group_ids:
            group_query = GroupsContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": group_id}],
                enable_cross_partition_query=True
            )
            group_data = list(group_query)

            # within each group the user is a member of, search for the events of that group
            if group_data:
                group_event_ids = group_data[0].get("events", [])
                for event_id in group_event_ids:
                    event_query = EventsContainerProxy.query_items(
                        query="SELECT * FROM c WHERE c.id = @id",
                        parameters=[{"name": "@id", "value": event_id}],
                        enable_cross_partition_query=True
                    )
                    event_data = list(event_query)
                    if event_data:
                        all_group_events.append(event_data[0])  # Add the full event data

        return HttpResponse(json.dumps({"result": True, "msg": "Events retrieved successfully", "events": all_group_events}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        logging.error('Cosmos DB error: %s', str(cosmos_err))
        return HttpResponse(json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")
