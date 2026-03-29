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
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])  # Assuming this is your Events container name

def main(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request for getting all attending events.')

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
        actualPlayerQuery = UsersContainerProxy.query_items(
            query=f"SELECT * FROM c WHERE c.{query_field} = @{query_field}",
            parameters=[{"name": f"@{query_field}", "value": query_value}],
            enable_cross_partition_query=True
        )
        actualPlayer = list(actualPlayerQuery)

        # if a player was found, look for the events the user is attending
        if actualPlayer:
            player_data = actualPlayer[0]
            attending_event_ids = player_data.get("eventsAttending", [])
            attending_events = []

            # Retrieve each event's details from the Events container
            for event_id in attending_event_ids:
                event_query = EventsContainerProxy.query_items(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": event_id}],
                    enable_cross_partition_query=True
                )
                event_data = list(event_query)
                if event_data:
                    attending_events.append(event_data[0])  # Assuming each ID corresponds to a unique event

            return HttpResponse(json.dumps({"result": True, "msg": "OK", "userId": player_data.get("id"), "attendingEvents": attending_events}), status_code=200, mimetype="application/json")
        # if no player was found, return an error status code of 400
        else:
            logging.info("User not found.")
            return HttpResponse(body=json.dumps({"result": False, "msg": "User not found."}), status_code=400, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        # If a Cosmos DB error occurs, log it and return an appropriate message
        logging.error('Cosmos DB error: %s', str(cosmos_err))
        return HttpResponse(body=json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(body=json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")
