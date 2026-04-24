from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from ..models import UserCreate, UserLogin, Token, RefreshTokenRequest
from ..utils.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM
)
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "email": user.email,
        "full_name": user.full_name or "",
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = str(db_user["_id"])
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh(request: RefreshTokenRequest):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")
    
    # Check if user still exists
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    access_token = create_access_token(data={"sub": user_id})
    # We can also rotate the refresh token here if we want, but for now we'll keep the same or issue a new one
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = users_collection.find_one({"_id": ObjectId(current_user["id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "created_at": str(user.get("created_at", "")),
    }
