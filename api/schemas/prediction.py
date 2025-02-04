from pydantic import BaseModel, Field
from datetime import datetime
from typing import Tuple

class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class TripRequest(BaseModel):
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float
    dropoff_longitude: float
    passenger_count: int = Field(..., gt=0, le=6)
    trip_distance: float

class TripPrediction(BaseModel): 
    duration: float
    fare: float