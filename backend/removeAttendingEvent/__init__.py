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

    try:
        # Determine if querying by userId or username
        if "userId" in input_data:
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": input_data["userId"]}]
        elif "username" in input_data:
            query = "SELECT * FROM c WHERE c.username = @username"
            parameters = [{"name": "@username", "value": input_data["username"]}]
        # if neither is present, return a status error message of 400
        else:
            return HttpResponse(body=json.dumps({"result": False, "msg": "UserId or Username is required"}), status_code=400, mimetype="application/json")

        # search for player in user cosmosDB
        actualPlayerQuery = UsersContainerProxy.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        )

        actualPlayer = list(actualPlayerQuery)

        # if player exists, remove the specified attending event
        if actualPlayer:
            playerData = actualPlayer[0]

            # Remove the event from the list of eventsAttending if it exists
            eventIDRemove = input_data["eventId"]
            playerData["eventsAttending"] = [eventID for eventID in playerData.get("eventsAttending", []) if eventID != eventIDRemove]

            # Update the user document in Cosmos DB
            try:
                updated_item_response = UsersContainerProxy.upsert_item(playerData)
                logging.info("User document updated successfully.")
            except CosmosHttpResponseError as e:
                logging.error('Error updating user document: %s', str(e))
                return HttpResponse(json.dumps({"result": False, "msg": "Error updating user document: " + str(e)}), status_code=500, mimetype="application/json")

            # Search for the event document
            event_query = EventsContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": input_data["eventId"]}],
                enable_cross_partition_query=True
            )
            event_data = list(event_query)
            
            # Check if the event exists
            if event_data:
                event_data = event_data[0]

                # Check if the user is in the attendees list
                if "attendees" in event_data:
                    user_to_remove = {"userId": input_data.get("userId")}
                    event_data["attendees"] = [attendee for attendee in event_data.get("attendees", []) if attendee["userId"] != user_to_remove["userId"]]

                    # Update the event document in Cosmos DB
                    try:
                        EventsContainerProxy.upsert_item(event_data)
                        logging.info("Event document updated successfully.")
                    except CosmosHttpResponseError as e:
                        logging.error('Error updating event document: %s', str(e))
                        return HttpResponse(json.dumps({"result": False, "msg": "Error updating event document: " + str(e)}), status_code=500, mimetype="application/json")

                return HttpResponse(body=json.dumps({"result": True, "msg": "OK", "userId": playerData.get("id"), "eventId": eventIDRemove}), status_code=200, mimetype="application/json")
            else:
                logging.info("Event not found.")
                return HttpResponse(body=json.dumps({"result": False, "msg": "Event not found."}), status_code=400, mimetype="application/json")
        else:
            logging.info("User not found.")
            return HttpResponse(body=json.dumps({"result": False, "msg": "User not found."}), status_code=400, mimetype="application/json")
    except CosmosHttpResponseError as cosmoserr:
        # If a Cosmos DB error occurs, log it and return an appropriate message
        logging.error('Cosmos DB error: %s', str(cosmoserr))
        return HttpResponse(body=json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmoserr)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(body=json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")