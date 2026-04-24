from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models import ServiceCreate, ServiceUpdate, ServiceResponse
from ..database import services_collection
from ..utils.security import get_current_user
from ..utils.ssrf import is_safe_url
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/services", tags=["services"])

@router.post("", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, current_user: dict = Depends(get_current_user)):
    if not is_safe_url(service.url):
        raise HTTPException(status_code=400, detail="Invalid or forbidden URL")

    service_dict = service.model_dump()
    service_dict["user_id"] = current_user["id"]
    service_dict["created_at"] = datetime.utcnow()
    service_dict["last_run"] = None

    result = services_collection.insert_one(service_dict)
    service_dict["_id"] = result.inserted_id

    return service_dict

@router.get("", response_model=List[ServiceResponse])
async def get_services(current_user: dict = Depends(get_current_user)):
    services = list(services_collection.find({"user_id": current_user["id"]}))
    return services

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, service: ServiceUpdate, current_user: dict = Depends(get_current_user)):
    if service.url and not is_safe_url(service.url):
        raise HTTPException(status_code=400, detail="Invalid or forbidden URL")

    update_data = {k: v for k, v in service.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = services_collection.update_one(
        {"_id": ObjectId(service_id), "user_id": current_user["id"]},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")

    updated_service = services_collection.find_one({"_id": ObjectId(service_id)})
    return updated_service

@router.delete("/{service_id}")
async def delete_service(service_id: str, current_user: dict = Depends(get_current_user)):
    result = services_collection.delete_one({"_id": ObjectId(service_id), "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"detail": "Service deleted"}

@router.patch("/{service_id}/toggle", response_model=ServiceResponse)
async def toggle_service(service_id: str, current_user: dict = Depends(get_current_user)):
    service = services_collection.find_one({"_id": ObjectId(service_id), "user_id": current_user["id"]})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    new_status = not service.get("is_active", True)
    services_collection.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": {"is_active": new_status}}
    )
    
    service["is_active"] = new_status
    return service
