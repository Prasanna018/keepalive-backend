import os
import time
import requests
from datetime import datetime
from celery import Celery
from .database import services_collection, logs_collection
from .utils.ssrf import is_safe_url
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

REDIS_URI = os.getenv("REDIS_URI", "redis://localhost:6379/0")

import ssl

# Upstash uses rediss:// (TLS). Celery requires explicit ssl_cert_reqs for secure Redis.
SSL_OPTIONS = {"ssl_cert_reqs": ssl.CERT_NONE}

celery = Celery(
    "keepalive_worker",
    broker=REDIS_URI,
    backend=REDIS_URI
)

# Only apply SSL options if using a secure rediss:// connection
if REDIS_URI.startswith("rediss://"):
    celery.conf.broker_use_ssl = SSL_OPTIONS
    celery.conf.redis_backend_use_ssl = SSL_OPTIONS

celery.conf.beat_schedule = {
    "run-scheduler-every-10-minutes": {
        "task": "app.worker.scheduler_task",
        "schedule": 600.0,
    },
}

celery.conf.timezone = "UTC"

def should_run(service):
    now = datetime.utcnow()
    last_run = service.get("last_run")

    if not last_run:
        return True

    diff = (now - last_run).total_seconds() / 60
    return diff >= service.get("interval", 15)

@celery.task(name="app.worker.scheduler_task")
def scheduler_task():
    services = services_collection.find({"is_active": True})
    
    for service in services:
        if should_run(service):
            # Serialize ObjectId to string for Celery
            service_dict = {k: str(v) if isinstance(v, ObjectId) else v for k, v in service.items()}
            ping_service.delay(service_dict)

@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}, name="app.worker.ping_service")
def ping_service(self, service):
    if not is_safe_url(service["url"]):
        return

    start = time.time()
    log = {
        "service_id": service["_id"],
        "timestamp": datetime.utcnow()
    }

    try:
        method = service.get("method", "GET").upper()
        headers = service.get("headers", {})
        
        # Convert list of headers `[{key: "...", value: "..."}]` to dict `{"key": "value"}` if needed
        # Assuming headers are stored as dict or list in MongoDB based on frontend representation
        req_headers = {}
        if isinstance(headers, dict):
            req_headers = headers
        elif isinstance(headers, list):
            req_headers = {h["key"]: h["value"] for h in headers if "key" in h and "value" in h}

        if method == "POST":
            res = requests.post(service["url"], headers=req_headers, timeout=60)
        else:
            res = requests.get(service["url"], headers=req_headers, timeout=60)

        log.update({
            "status": "success",
            "status_code": res.status_code,
            "response_time": int((time.time() - start) * 1000),  # ms
            "message": res.text[:500] if res.text else ""
        })
    except Exception as e:
        log.update({
            "status": "fail",
            "error": str(e),
            "response_time": int((time.time() - start) * 1000)
        })

    logs_collection.insert_one(log)
    services_collection.update_one(
        {"_id": ObjectId(service["_id"])},
        {"$set": {"last_run": datetime.utcnow()}}
    )
