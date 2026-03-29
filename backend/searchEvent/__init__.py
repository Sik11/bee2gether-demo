import logging
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
import json
import os
from azure.cosmos import CosmosClient

# setup Cosmos DB credentials
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to search events')

    # get event search term
    event_input = req.get_json()

    # check if event input has name and if not send http response with error CODE
    if "name" not in event_input:
        return HttpResponse(json.dumps({"result": False, "msg": "Event name not found"}), status_code=400, mimetype="application/json")
    eventName = event_input["name"]

    # search for event in cosmosdb
    try:
        query = "SELECT * FROM c WHERE CONTAINS(c.name, @name)"
        events = list(EventsContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@name", "value": eventName}],
            enable_cross_partition_query=True
        ))
        # if there are no events with eventName in cosmosDB, return error
        if len(events) == 0:
            return HttpResponse(json.dumps({"result": False, "msg": "Event not found"}), status_code=400, mimetype="application/json")
        # return max 5 top events that can be foudn in cosmosDB
        elif len(events) <= 5:
            return HttpResponse(json.dumps({"result": True, "msg": "Event found", "events": events}), status_code=200, mimetype="application/json")
        else:
            return HttpResponse(json.dumps({"result": True, "msg": "Event found", "events": events[:5]}), status_code=200, mimetype="application/json")
        
    # if cosmosDB error is returned, return status code 500    
    except CosmosHttpResponseError as cosmoserr:
        logging.error('Cosmos DB error: %s', cosmoserr.message)
        return HttpResponse(json.dumps({"result": False, "msg": "Cosmos DB error: " + cosmoserr.message}), status_code=500, mimetype="application/json")
    except Exception as err:
        logging.error('System Error: %s', err)
        return HttpResponse(json.dumps({"result": False, "msg": "System Error: " + err}), status_code=500, mimetype="application/json")
