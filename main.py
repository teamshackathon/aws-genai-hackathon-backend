from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.api import api_router
import os

if os.getenv("OPENAPI_URL"):
    openapi_url = os.getenv("OPENAPI_URL")

app = FastAPI(
    title="BAE-RECIPE API",
    version="1.0.0",
    openapi_url=openapi_url+"/openapi.json" if os.getenv("OPENAPI_URL") else "/openapi.json",
)

origins = []

if os.getenv("ALLOWED_ORIGINS"):
    origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     # List of allowed origins
    allow_credentials=True,    # Allow cookies
    allow_methods=["*"],       # Allow all methods
    allow_headers=["*"],       # Allow all headers
)

app.include_router(api_router, prefix="/api/v1")