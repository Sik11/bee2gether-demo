# Input: 

# A request containing a JSON with event data to update with
# {"name": "event_to_modify" , "time": new_time , "location": new_location, "description" : new_description, "tags" : new_tags, "photos" : new_photos }  


from azure.cosmos import CosmosClient
import os 
from azure.cosmos.exceptions import CosmosHttpResponseError
import json
import logging
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies outside of the main function if possible
# to take advantage of connection reuse
# Proxy object to account, database and containers
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])


def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to update event')

    input_data = req.get_json()
    logging.info(input_data)

    # Ensure the event name is in request
    if "name" not in input_data:
        return HttpResponse(json.dumps({"result": False, "msg": "Event name is required"}), status_code=400, mimetype="application/json")

    # search for the event in the events cosmosDB
    try:
        event_query = list(EventsContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.name = @name",
            parameters=[{"name": "@name", "value": input_data["name"]}],
            enable_cross_partition_query=True
        ))

        # if the event doesn't exists, return appropriate error message
        if not event_query:
            return HttpResponse(json.dumps({"result": False, "msg": "Event not found"}), mimetype="application/json")

        # Assuming event_query[0] contains the event data
        existing_event_data = event_query[0]

        # Update fields if present in input_data
        if "time" in input_data:
            existing_event_data["time"] = input_data["time"]

        if "long" in input_data:
            existing_event_data["long"] = input_data["long"]

        if "lat" in input_data:
            existing_event_data["lat"] = input_data["lat"]

        if "description" in input_data:
            existing_event_data["description"] = input_data["description"]

        if "tags" in input_data:
            existing_event_data["tags"] = input_data["tags"]

        if "ongoing" in input_data:
            existing_event_data["ongoing"] = input_data["ongoing"]

        # Update the event document in Cosmos DB
        try:
            EventsContainerProxy.replace_item(item=existing_event_data["id"], body=existing_event_data)
            logging.info("Event document updated successfully.")
        except CosmosHttpResponseError as e:
            logging.error('Error updating event document: %s', str(e))
            return HttpResponse(json.dumps({"result": False, "msg": "Error updating event document: " + str(e)}), mimetype="application/json")

        return HttpResponse(json.dumps({"result": True, "msg": "Event updated successfully"}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmos_err:
        logging.error('Cosmos DB error: %s', str(cosmos_err))
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmos_err)}), status_code=500, mimetype="application/json")
    except Exception as e:
        logging.error('System error: %s', str(e))
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")
