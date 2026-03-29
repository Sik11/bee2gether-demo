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
    logging.info('HTTP request to get all events and filter them based on coordinates')

    try:
        # Retrieve map area coordinates from the request body
        body = req.get_json()
        logging.info('Request body: %s', body)  

        bottom_left_long = float(body.get('bottomLeftLong'))
        bottom_left_lat = float(body.get('bottomLeftLat'))
        upper_right_long = float(body.get('upperRightLong'))
        upper_right_lat = float(body.get('upperRightLat'))

        # Query the EventsContainer for all events
        all_events = list(EventsContainerProxy.query_items(
            query="SELECT * FROM c",
            enable_cross_partition_query=True
        ))

        # Filter events based on coordinates
        filtered_events = [
            event for event in all_events
            if bottom_left_long <= event['long'] <= upper_right_long and
               bottom_left_lat <= event['lat'] <= upper_right_lat
        ]

        return HttpResponse(json.dumps({"result": True, "events": filtered_events}), status_code=200, mimetype="application/json")

    except CosmosHttpResponseError as cosmoserr:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmoserr)}), status_code=500, mimetype="application/json")
    except ValueError:
        return HttpResponse(json.dumps({"result": False, "msg": "Invalid coordinate format"}), status_code=500, mimetype="application/json")
    except KeyError:
        return HttpResponse(json.dumps({"result": False, "msg": "Missing coordinate data"}), status_code=500, mimetype="application/json")
