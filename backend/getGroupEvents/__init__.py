import logging
import os
import json
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
GroupsContainerProxy = BeeDBProxy.get_container_client(os.environ['GroupsContainer'])
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])  # Assuming this is your Events container name

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP trigger function processed a request to get all events for a group.')

    input_data = req.get_json()
    logging.info(input_data)

    # Check if groupId is provided
    if "groupId" not in input_data:
        return HttpResponse(json.dumps({"result": False, "msg": "GroupId is required"}), status_code=400, mimetype="application/json")

    group_id = input_data["groupId"]

    try:
        # Query to get the group by groupId
        group_query = list(GroupsContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": group_id}],
            enable_cross_partition_query=True
        ))

        # if no group was found, return a status error message of 404
        if not group_query:
            return HttpResponse(json.dumps({"result": False, "msg": "Group not found"}), status_code=404, mimetype="application/json")

        # Assuming the group's events are stored in a field named 'events'
        group_event_ids = group_query[0].get("events", [])
        group_events = []

        # Retrieve each event's details from the Events container
        for event_id in group_event_ids:
            event_query = list(EventsContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": event_id}],
                enable_cross_partition_query=True
            ))
            if event_query:
                group_events.append(event_query[0])  # Assuming each ID corresponds to a unique event

        return HttpResponse(json.dumps({"result": True, "msg": "Events retrieved successfully", "events": group_events}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        logging.error('Cosmos DB error: %s', str(cosmos_err))
        return HttpResponse(json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")
