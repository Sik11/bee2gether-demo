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
    try:
        logging.info('HTTP request to get event attendees')

        # Query all events in the EventsContainer
        events_query = "SELECT c.id, c.attendees FROM c"
        events_data = list(EventsContainerProxy.query_items(
            query=events_query,
            enable_cross_partition_query=True
        ))

        # Create a list to store event information
        result_list = []
        logging.info(len(events_data))
        # Iterate through events and extract information
        for event_data in events_data:
            event_id = event_data.get('id')
            attendees = event_data.get('attendees', [])

            # Append event information to the result list
            result_list.append({
                "eventId": event_id,
                "attendees": attendees
            })
        
        # if no events were found, then return a status error message indicating this user is not attending any events
        if not result_list:
            return HttpResponse(json.dumps({"result": False, "msg": "No events found"}), status_code=404, mimetype="application/json")

        return HttpResponse(json.dumps({"result": True, "eventAttendees": result_list}), status_code=200, mimetype="application/json")

    except CosmosHttpResponseError as cosmoserr:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmoserr)}), status_code=500, mimetype="application/json")
    except Exception as e:
        return HttpResponse(json.dumps({"result": False, "msg": "System error: " + str(e)}), status_code=500, mimetype="application/json")