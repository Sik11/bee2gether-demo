import os
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient, exceptions

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Retrieve the file and eventId from the request body
        file = req.files.get('file')
        eventId = req.form.get('eventId')
        
        # if neither of these exists, return a error status message of 400
        if not file or not eventId:
            return func.HttpResponse(({"result": False, "msg": "File and eventId must be provided"}), status_code=400, mimetype="application/json")

        # Define connection and container details for Blob Storage
        connect_str = os.environ.get("AZURE_BLOB_CONNECTION_STRING", "deprecated")
        container_name = "bee2getherblob"
        blob_name = file.filename

        # Create a blob client and upload the file
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(file, blob_type="BlockBlob")
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"

        # Cosmos DB setup
        cosmos_connect_str = os.environ['AzureCosmosDBConnectionString']
        database_name = os.environ['DatabaseName']
        container_name = os.environ['EventsContainer']
        groups_container_name = os.environ['GroupsContainer']

        # Initialize Cosmos DB client and container proxy
        cosmos_connect_str = os.environ['AzureCosmosDBConnectionString']
        database_name = os.environ['DatabaseName']
        events_container_name = os.environ['EventsContainer']
        groups_container_name = os.environ['GroupsContainer']

        # Initialize Cosmos DB client and container proxies
        cosmos_client = CosmosClient.from_connection_string(cosmos_connect_str)
        database = cosmos_client.get_database_client(database_name)
        events_container = database.get_container_client(events_container_name)
        groups_container = database.get_container_client(groups_container_name)

        # Fetch the event and update its 'eventImg(s)' list
        event = list(events_container.query_items(
            query="SELECT * FROM c WHERE c.id = @eventId",
            parameters=[{"name": "@eventId", "value": eventId}],
            enable_cross_partition_query=True
        ))
        if event:
            event = event[0]
            event.setdefault('eventImg(s)', []).append(blob_url)
            events_container.upsert_item(event)
        else:
            return func.HttpResponse(f"Event with ID {eventId} not found", status_code=404)

        # Find and update groups that contain this event
        groups_with_event = list(groups_container.query_items(
            query="SELECT * FROM c WHERE ARRAY_CONTAINS(c.events, {'id': @eventId}, true)",
            parameters=[{"name": "@eventId", "value": eventId}],
            enable_cross_partition_query=True
        ))

        for group in groups_with_event:
            updated_events = []
            for event_in_group in group.get("events", []):
                if event_in_group.get("id") == eventId:
                    event_in_group['eventImg(s)'] = event['eventImg(s)']
                updated_events.append(event_in_group)
            group["events"] = updated_events
            groups_container.replace_item(item=group["id"], body=group)

        return func.HttpResponse(f"The file {file.filename} uploaded successfully. URL: {blob_url}")

    except Exception as ex:
        logging.error(ex)
        return func.HttpResponse(f"Error occurred: {str(ex)}", status_code=500)
