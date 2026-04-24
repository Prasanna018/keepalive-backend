from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, services, logs

app = FastAPI(title="KeepAlive API")

# Setup CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

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
