import sys
import os
from pathlib import Path


root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import predictions
from api.routers.predictions import router as predict_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predict_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to NYC Taxi Predictor API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 

