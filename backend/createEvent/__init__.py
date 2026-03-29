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
    logging.info('HTTP Request to create event')
    event_input = req.get_json()
    logging.info(event_input)
    
    try:
        # Check if an event with the same name already exists
        existing_event = list(EventsContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.name = @name",
            parameters=[{"name": "@name", "value": event_input["name"]}],
            enable_cross_partition_query=True
        ))
        
        if len(existing_event) > 0:
            return HttpResponse(json.dumps({"result": False, "msg": "Event name already exists"}), status_code=400, mimetype="application/json")
        
        # check if user who submitted event exists
        userName = list(UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": event_input["userId"]}],
            enable_cross_partition_query=True
        ))[0].get('username')

        # set parameters of mew event
        event_input["username"] = userName
        event_input["ongoing"] = True
        event_input["eventImg(s)"] = []
        event_input["attendees"] = [{"userId": event_input["userId"], "username": userName}]

        # if the submitted event is for a group, find if the group exists and add it to the event information
        if "groupId" in event_input:
            group_id = event_input["groupId"]
            group_query = list(GroupsContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": group_id}],
                enable_cross_partition_query=True
            ))
            if group_query:
                group_data = group_query[0]
                group_Name = group_data.get("name")
                event_input["groupName"] = group_Name
        # otherwise, if event is not for a group, keep this parameter 'None'
        else:
            event_input["groupName"] = "None"

        # Create the event item
        event_item_response = EventsContainerProxy.create_item(event_input, enable_automatic_id_generation=True)

        # update the group with the event information, if the event belongs to a group
        if "groupId" in event_input:
            group_id = event_input["groupId"]
            group_query = list(GroupsContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": group_id}],
                enable_cross_partition_query=True
            ))
            if group_query:
                group_data = group_query[0]
                group_events = group_data.get("events", [])
                group_events.append(event_item_response)  # Add the event object instead of the ID
                group_data["events"] = group_events
                GroupsContainerProxy.replace_item(item=group_data["id"], body=group_data)

        # Find the user with the given userId and update their eventsAttending attribute
        user = list(UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": event_input["userId"]}],
            enable_cross_partition_query=True
        ))[0]
        events_attending = user.get("eventsAttending", [])
        events_attending.append(event_item_response.get('id'))
        user["eventsAttending"] = events_attending
        UsersContainerProxy.replace_item(item=user["id"], body=user)

        # create a pointer from this user to the event they have created and add it to event CosmosDB
        user_to_event_item = {
            "userId": event_input["userId"],
            "eventId": [event_item_response.get('id')]
        }
        UsersToEventsContainerProxy.create_item(user_to_event_item, enable_automatic_id_generation=True)

        return HttpResponse(json.dumps({"result": True, "msg": "Event created successfully", "eventId": event_item_response.get('id')}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmoserr:
        logging.error('Cosmos DB error: %s', cosmoserr.message)
        return HttpResponse(json.dumps({"result": False, "msg": "Cosmos DB error: " + cosmoserr.message}), status_code=500, mimetype="application/json")
