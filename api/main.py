from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Any
from routers.predictions import router as predictions_router
from redis_conn import redis_conn
from logger import Logger

# Configure logging
logger = Logger.get_logger('main')

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions_router, prefix="/api/v1/predictions")

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to NYC Taxi Predictor API"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    try:
        redis_conn.client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "redis": str(e)}
