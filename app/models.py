from pydantic import BaseModel, Field, EmailStr, ConfigDict, GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Optional, Dict, Any, Annotated
from datetime import datetime
from bson import ObjectId

class _ObjectIdPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> ObjectId:
            return ObjectId(value)
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance)
            ),
        )

PyObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ServiceBase(BaseModel):
    url: str
    method: str = "GET"
    interval: int = 5
    headers: Optional[Dict[str, str]] = {}
    is_active: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    url: Optional[str] = None
    method: Optional[str] = None
    interval: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None

class ServiceResponse(ServiceBase):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: str
    last_run: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

class LogResponse(BaseModel):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    service_id: str
    service_url: Optional[str] = None
    status: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
