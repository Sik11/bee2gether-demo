import logging
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to get event images.')

    # Parse 'eventId' from the query parameters
    req_body = req.get_json()
    event_id = req_body.get('eventId')
    if not event_id:
        return func.HttpResponse("Please pass an eventId in the query string", status_code=400)

    try:
        # Cosmos DB setup
        cosmos_connect_str = os.environ['AzureCosmosDBConnectionString']
        database_name = os.environ['DatabaseName']
        container_name = os.environ['EventsContainer']

        # Initialize Cosmos DB client and container proxy
        cosmos_client = CosmosClient.from_connection_string(cosmos_connect_str)
        database = cosmos_client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Query for the event by eventId
        query = "SELECT * FROM c WHERE c.id = @eventId"
        parameters = [{"name": "@eventId", "value": event_id}]
        event_imgs = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        # Check if event was found and has images
        if not event_imgs:
            return func.HttpResponse(f"No event found with ID {event_id}", status_code=404)
        
        logging.info(event_imgs[0])

        # Assuming eventImg(s) is a list of image URLs in the event document
        img_urls = event_imgs[0].get('eventImg(s)', [])

        return func.HttpResponse(json.dumps({"eventId": event_id, "imgUrls": img_urls}), mimetype="application/json")

    except exceptions.CosmosHttpResponseError as e:
        logging.error('Cosmos DB error: %s', e.message)
        return func.HttpResponse(f"Error querying Cosmos DB: {str(e)}", status_code=500)

    except Exception as ex:
        logging.error(ex)
        return func.HttpResponse(f"An error occurred: {str(ex)}", status_code=500)
