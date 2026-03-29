from azure.cosmos import CosmosClient
import os
from azure.cosmos.exceptions import CosmosHttpResponseError
import json
import logging
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
EventsContainerProxy = BeeDBProxy.get_container_client(os.environ['EventsContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP request to get event information')

    try:
        # Get the event ID from the request body
        req_body = req.get_json()
        event_id = req_body.get('eventId')
        if not event_id:
            return HttpResponse(json.dumps({"result": False, "msg": "Event ID is required"}), status_code=400, mimetype="application/json")

        # Query the EventsContainer for the event
        event_query = "SELECT * FROM c WHERE c.id = @eventId"
        parameters = [{"name": "@eventId", "value": event_id}]
        event_data = list(EventsContainerProxy.query_items(
            query=event_query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        # Check if event data is found
        if not event_data:
            return HttpResponse(json.dumps({"result": False, "msg": "Event not found"}), status_code=400, mimetype="application/json")

        # Assuming event_data contains only one item since id is unique
        event_info = event_data[0]

        return HttpResponse(json.dumps({"result": True, "eventInfo": event_info}), status_code=200, mimetype="application/json")

    except CosmosHttpResponseError as cosmoserr:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmoserr)}), status_code=500, mimetype="application/json")
