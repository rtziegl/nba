from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import certifi
import requests
# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI")
print(uri)

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())
print(client)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

