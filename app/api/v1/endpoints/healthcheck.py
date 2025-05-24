from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter()

@router.get("/readiness", tags=["healthcheck"])
def readiness_check():
    return JSONResponse(content={"status": "ok", "check": "readiness"})

@router.get("/liveness", tags=["healthcheck"])
def liveness_check():
    return JSONResponse(content={"status": "ok", "check": "liveness"})