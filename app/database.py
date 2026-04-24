import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)
db = client["keepalive_db"]

users_collection = db["users"]
services_collection = db["services"]
logs_collection = db["logs"]
