from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class LocationCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

class TripRequest(BaseModel):
    pickup_location: LocationCoordinates = Field(..., description="Pickup location coordinates")
    dropoff_location: LocationCoordinates = Field(..., description="Dropoff location coordinates")
    # PULocationID: int = Field(..., description="Pickup location ID")
    # DOLocationID: int = Field(..., description="Dropoff location ID")
    trip_distance: float = Field(..., ge=0, lt=100, description="Trip distance in miles")
    # store_and_fwd_flag: str = Field(..., description="Store and forward flag")
    pickup_datetime: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Pickup datetime (defaults to current time if not provided)"
    )

class TripPrediction(BaseModel):
    trip_duration: float = Field(ge=0, description="Predicted trip duration in minutes")
    fare_amount: float = Field(ge=0, description="Predicted fare amount in USD")
    tolls_amount: float = Field(ge=0, description="Predicted tolls amount in USD")
    congestion_surcharge: float = Field(ge=0, description="Predicted congestion surcharge in USD")
    total_amount: float = Field(ge=0, description="Predicted total amount in USD")

    class Config:
        json_schema_extra = {
            "example": {
                "trip_duration": 25.5,
                "fare_amount": 32.50,
                "tolls_amount": 0.0,
                "congestion_surcharge": 2.50,
                "total_amount": 35.00
            }
        }