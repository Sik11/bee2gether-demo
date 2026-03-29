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
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    input_data = req.get_json()
    logging.info(input_data)

    query_field = None
    query_value = None

    # if user has entered userID as event organiser use that
    if "userId" in input_data:
        query_field = "id"
        query_value = input_data["userId"]
    # otherwise, use their username
    elif "username" in input_data:
        query_field = "username"
        query_value = input_data["username"]
    # if neither field can be found, return an error code
    else:
        return HttpResponse(body=json.dumps({"result": False, "msg": "Username or UserId is required"}), status_code=400, mimetype="application/json")

    try:
        # Query for the user with the given username or userId
        actualPlayerQuery = UsersContainerProxy.query_items(
            query=f"SELECT * FROM c WHERE c.{query_field} = @{query_field}",
            parameters=[{"name": f"@{query_field}", "value": query_value}],
            enable_cross_partition_query=True
        )

        
        actualPlayer = list(actualPlayerQuery)
        if actualPlayer:
            playerData = actualPlayer[0]
            if "eventId" in input_data:    
                # Check if the event exists
                eventQuery = EventsContainerProxy.query_items(
                    query="SELECT * FROM c WHERE c.id = @eventId",
                    parameters=[{"name": "@eventId", "value": input_data["eventId"]}],
                    enable_cross_partition_query=True
                )
                event = list(eventQuery)

                # if not found, return error status message
                if not event:
                    logging.info("Event not found.")
                    return HttpResponse(body=json.dumps({"result": False, "msg": "Event not found."}), mimetype="application/json")

                #check the eventid isnt already in the list
                logging.info(playerData["eventsAttending"])
                if input_data["eventId"] in playerData["eventsAttending"]:
                    return HttpResponse(json.dumps({"result": False, "msg": "User already attending event"}), mimetype="application/json")
                # Update the user document in Cosmos DB
                try:
                    playerData["eventsAttending"].append(input_data["eventId"])
                    updated_item_response = UsersContainerProxy.upsert_item(playerData)
                    logging.info("User document updated successfully.")
                    #query for the event
                    event_query = EventsContainerProxy.query_items(
                        query="SELECT * FROM c WHERE c.id = @id",
                        parameters=[{"name": "@id", "value": input_data["eventId"]}],
                        enable_cross_partition_query=True
                    )
                    event_data = list(event_query)[0]

                    #for existing events, create attendees column. 
                    if "attendees" not in event_data:
                        event_data["attendees"] = []
                    event_data["attendees"].append({"userId": playerData.get("id"), "username": playerData.get("username")})
                    # Update the event document in Cosmos DB
                    EventsContainerProxy.upsert_item(event_data)
                    logging.info("Event document updated successfully.")
                    
                except CosmosHttpResponseError as e:
                    logging.error('Error updating user document: %s', str(e))
                    return HttpResponse(json.dumps({"result": False, "msg": "Error updating user document: " + str(e)}), mimetype="application/json")

            return HttpResponse(json.dumps({"result": True, "msg": "OK", "userId": playerData.get("id"), "eventId": input_data.get("eventId")}), mimetype="application/json")
        else:
            logging.info("User not found.")
            return HttpResponse(body=json.dumps({"result": False, "msg": "User not found."}), mimetype="application/json")
    except CosmosHttpResponseError as cosmoserr:
        # If a Cosmos DB error occurs, log it and return an appropriate message
        logging.error('Cosmos DB error: %s', str(cosmoserr))
        return HttpResponse(body=json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmoserr)}), mimetype="application/json")

