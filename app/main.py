from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, services, logs
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="KeepAlive API")

# Read CORS origins from .env (comma-separated)
cors_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080")
origins = [o.strip() for o in cors_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(logs.router)

@app.get("/")
def read_root():
    return {"message": "KeepAlive API is running"}
