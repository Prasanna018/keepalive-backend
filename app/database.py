import os
import dns.resolver
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Force dnspython to use Google/Cloudflare DNS to avoid local router DNS issues (SRV REFUSED)
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI, connect=False)
db = client["keepalive_db"]

users_collection = db["users"]
services_collection = db["services"]
logs_collection = db["logs"]
