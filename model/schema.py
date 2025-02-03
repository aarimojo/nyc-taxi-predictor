from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class ServiceZone(str, Enum):
    EWR = "EWR"
    BORO = "Boro Zone"
    YELLOW = "Yellow Zone"
    AIRPORTS = "Airports"
    UNKNOWN = "Unknown"
    NA = "N/A"

class Borough(str, Enum):
    MANHATTAN = "Manhattan"
    BROOKLYN = "Brooklyn"
    QUEENS = "Queens"
    BRONX = "Bronx"
    STATEN_ISLAND = "Staten Island"
    EWR = "EWR"
    UNKNOWN = "Unknown"
    NA = "N/A"

class TimeOfDay(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"

class TripData(BaseModel):
    # Required input fields (only what we receive)
    PULocationID: int = Field(ge=1, le=265, description="Pickup location ID from taxi zones")
    DOLocationID: int = Field(ge=1, le=265, description="Dropoff location ID from taxi zones")
    store_and_fwd_flag: str = Field(pattern="^[YN]$", description="Store and forward flag (Y/N)")
    trip_distance: float = Field(ge=0, lt=100, description="Trip distance in miles")
    tpep_pickup_datetime: datetime = Field(description="Pickup datetime")
    
    # Derived fields (will be populated from validators)
    Borough_pu: Borough = Field(default=None, description="Pickup borough")
    Borough_do: Borough = Field(default=None, description="Dropoff borough")
    service_zone_pu: ServiceZone = Field(default=None, description="Pickup service zone")
    service_zone_do: ServiceZone = Field(default=None, description="Dropoff service zone")
    day_of_week_pu: int = Field(default=None, description="Pickup day of week (0=Monday, 6=Sunday)")
    hour_of_day_pu: int = Field(default=None, description="Pickup hour of day (24-hour format)")
    time_of_day_pu: TimeOfDay = Field(default=None, description="Pickup time of day category")
    Zone_pu: str = Field(default=None, description="Pickup zone name")
    Zone_do: str = Field(default=None, description="Dropoff zone name")

    @model_validator(mode='after')
    def set_time_based_fields(self) -> 'TripData':
        """Set the time-based fields based on pickup datetime."""
        hour = self.tpep_pickup_datetime.hour
        self.hour_of_day_pu = hour
        self.day_of_week_pu = self.tpep_pickup_datetime.weekday()
        
        # Set time of day
        self.time_of_day_pu = (
            TimeOfDay.MORNING if 6 <= hour < 12
            else TimeOfDay.AFTERNOON if 12 <= hour < 18
            else TimeOfDay.EVENING if 18 <= hour < 21
            else TimeOfDay.NIGHT
        )
        return self

    def model_dump_features(self) -> dict:
        """Return features in the exact order required by the model."""
        categorical_features = [
            'Zone_pu',   # Zone name from taxi_zones.csv
            'Zone_do'    # Zone name from taxi_zones.csv
        ]
        
        numerical_features = [
            'trip_distance',
            'day_of_week_pu',
            'hour_of_day_pu'
        ]
        
        one_hot_features = [
            'store_and_fwd_flag',
            'Borough_pu',
            'service_zone_pu',
            'Borough_do',
            'service_zone_do',
            'time_of_day_pu'
        ]
        
        all_features = categorical_features + numerical_features + one_hot_features
        
        # Create dictionary with string values for enums
        feature_dict = {}
        for feature in all_features:
            if feature == 'Zone_pu':
                # Need to get Zone name from taxi_zones.csv using PULocationID
                feature_dict[feature] = self.Zone_pu
            elif feature == 'Zone_do':
                # Need to get Zone name from taxi_zones.csv using DOLocationID
                feature_dict[feature] = self.Zone_do
            else:
                value = getattr(self, feature)
                # Convert enum to string value if it's an enum
                if isinstance(value, Enum):
                    feature_dict[feature] = value.value
                else:
                    feature_dict[feature] = value
                
        return feature_dict, all_features

    @field_validator('Borough_pu', 'Borough_do')
    def validate_borough(cls, v, info):
        field_name = info.field_name
        location_id = info.data.get('PULocationID' if field_name == 'Borough_pu' else 'DOLocationID')
        if location_id == 264:
            return Borough.UNKNOWN
        if location_id == 265:
            return Borough.NA
        return v

    @field_validator('service_zone_pu', 'service_zone_do')
    def validate_service_zone(cls, v, info):
        field_name = info.field_name
        location_id = info.data.get('PULocationID' if field_name == 'service_zone_pu' else 'DOLocationID')
        if location_id in [264, 265]:
            return ServiceZone.NA
        return v

class TripPrediction(BaseModel):
    trip_duration: float = Field(ge=0, description="Predicted trip duration in minutes")
    fare_amount: float = Field(ge=0, description="Predicted fare amount in USD")
    tolls_amount: float = Field(ge=0, description="Predicted tolls amount in USD")
    congestion_surcharge: float = Field(ge=0, description="Predicted congestion surcharge in USD")
    total_amount: float = Field(ge=0, description="Predicted total amount in USD")

    def model_dump(self) -> dict:
        """Return a dictionary representation of the model."""
        return {
            "trip_duration": self.trip_duration,
            "fare_amount": self.fare_amount,
            "tolls_amount": self.tolls_amount,
            "congestion_surcharge": self.congestion_surcharge,
            "total_amount": self.total_amount
        }
