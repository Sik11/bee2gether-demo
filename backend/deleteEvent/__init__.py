from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
import os
import json
import logging
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])
UsersToEventsContainerProxy = BeeDBProxy.get_container_client(os.environ["UsersToEventsContainer"])
UsersContainerProxy = BeeDBProxy.get_container_client(os.environ["UsersContainer"])
GroupsContainerProxy = BeeDBProxy.get_container_client(os.environ['GroupsContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to remove event')

    event_input = req.get_json()
    logging.info(event_input)

    try:
        # Query for the event with the given event ID and user ID
        event_query = list(EventsContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @eventId",
            parameters=[{"name": "@eventId", "value": event_input["eventId"]}],
            enable_cross_partition_query=True
        ))

        # If event cannot be found, return an error status code of 400
        if not event_query:
            return HttpResponse(json.dumps({"result": False, "msg": "Event not found"}), status_code=400, mimetype="application/json")

        event_data = event_query[0]

        # Delete the event from the EventsContainerProxy
        EventsContainerProxy.delete_item(item=event_data, partition_key=event_data.get("id"))


        # Update the UsersContainerProxy to remove the event from the user's eventsAttending
        user = list(UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": event_input["userId"]}],
            enable_cross_partition_query=True
        ))[0]
        events_attending = user.get("eventsAttending", [])
        events_attending.remove(event_data.get('id'))
        user["eventsAttending"] = events_attending
        UsersContainerProxy.replace_item(item=user["id"], body=user)

        # If the event belongs to a group, update the group's events list
        if "groupId" in event_data:
            group_id = event_data.get("groupId")
            group_query = list(GroupsContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": group_id}],
                enable_cross_partition_query=True
            ))
            if group_query:
                group_data = group_query[0]
                group_events = group_data.get("events", [])
                group_events.remove(event_data.get('id'))
                group_data["events"] = group_events
                GroupsContainerProxy.replace_item(item=group_data["id"], body=group_data)

        return HttpResponse(json.dumps({"result": True, "msg": "Event removed successfully", "eventId": event_data.get("id")}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmos_err)}), status_code=500, mimetype="application/json")
