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

def main(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    input = req.get_json()
    logging.info(input)

    try:
        # Query for the user with the given username
        actualPlayerQuery = UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.username = @username",
            parameters=[{"name": "@username", "value": input["username"]}],
            enable_cross_partition_query=True
        )

        actualPlayer = list(actualPlayerQuery)

        # Check if user exists and password matches
        if (len(actualPlayer) > 0) and (actualPlayer[0]["password"] == input["password"]):
            # Extract the ID from the user details
            user_id = actualPlayer[0].get('id')
            return HttpResponse(body=json.dumps({"result": True, "msg": "OK", "userId": user_id}), status_code=200, mimetype="application/json")
        else:
            # if username or password is incorrect, return appropriate error message with status code
            return HttpResponse(body=json.dumps({"result": False, "msg": "Username or password incorrect"}), status_code=400, mimetype="application/json")

    except CosmosHttpResponseError as cosmoserr:
        # If a Cosmos DB error occurs, log it and return an appropriate message
        logging.error('Cosmos DB error: %s', str(cosmoserr))
        return HttpResponse(body=json.dumps({"result": False, "msg": "Cosmos DB error: " + str(cosmoserr)}), status_code=500, mimetype="application/json")
