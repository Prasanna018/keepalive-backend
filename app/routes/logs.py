from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models import LogResponse
from ..database import logs_collection, services_collection
from ..utils.security import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("", response_model=List[LogResponse])
async def get_all_logs(current_user: dict = Depends(get_current_user), limit: int = 50):
    services = list(services_collection.find({"user_id": current_user["id"]}))
    service_map = {str(s["_id"]): s.get("url") for s in services}
    service_ids = list(service_map.keys())
    if not service_ids:
        return []
    logs = list(logs_collection.find({"service_id": {"$in": service_ids}}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["service_url"] = service_map.get(log["service_id"])
    return logs

@router.get("/{service_id}", response_model=List[LogResponse])
async def get_logs(service_id: str, current_user: dict = Depends(get_current_user), limit: int = 50):
    service = services_collection.find_one({"_id": ObjectId(service_id), "user_id": current_user["id"]})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    logs = list(logs_collection.find({"service_id": service_id}).sort("timestamp", -1).limit(limit))
    for log in logs:
        log["service_url"] = service.get("url")
    return logs
