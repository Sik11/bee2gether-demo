from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
import os
import json
import logging
from azure.functions import HttpRequest, HttpResponse

# Initialize Cosmos DB client and proxies outside of the main function if possible
# to take advantage of connection reuse
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
BeeDBProxy = MyCosmos.get_database_client(os.environ['DatabaseName'])
UsersContainerProxy = BeeDBProxy.get_container_client(os.environ['UsersContainer'])

def main(req: HttpRequest) -> HttpResponse:
    logging.info('HTTP Request to add user')

    input = req.get_json()
    logging.info(input)

    # Username and password validation
    if ((len(input["username"]) > 14) or (len(input["username"]) < 4)):
        return HttpResponse(json.dumps({"result": False, "msg": "Username less than 4 characters or more than 14 characters"}), status_code=400, mimetype="application/json")
    elif ((len(input["password"]) > 20) or (len(input["password"]) < 10)):
        return HttpResponse(json.dumps({"result": False, "msg": "Password less than 10 characters or more than 20 characters"}),status_code=400, mimetype="application/json")

    # initialise the users' attending events and the groups they are members of to zero
    input["eventsAttending"]=[]
    input["groupsMember"]=[]

    try:
        # Check if the username already exists
        temp = list(UsersContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.username = @username",
            parameters=[{"name": "@username", "value": input["username"]}],
            enable_cross_partition_query=True
        ))
        
        if len(temp) > 0:
            return HttpResponse(json.dumps({"result": False, "msg": "Username already exists"}), status_code=400, mimetype="application/json")
        
        # Create the user item and retrieve the result
        user_item_response = UsersContainerProxy.create_item(input, enable_automatic_id_generation=True)
        
        # Extract the ID from the created item response
        user_id = user_item_response.get('id')
        
        return HttpResponse(json.dumps({"result": True, "msg": "OK", "userId": user_id}), status_code=200, mimetype="application/json")
    except CosmosHttpResponseError as cosmoserr:
        return HttpResponse(json.dumps({"result": False, "msg": str(cosmoserr)}), status_code=500, mimetype="application/json")
