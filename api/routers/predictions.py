from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
from prediction_client import PredictionClient
from schemas.prediction import TripRequestIncoming, TripPrediction, TripRequestOutgoing
from services.zone_mapper import ZoneMapper
from services.weather_services import WeatherService
from logger import Logger

# Initialize logger
logger = Logger.get_logger('router.predictions')

# Initialize router
router = APIRouter(
    tags=["predictions"],
    responses={404: {"description": "Not found"}},
)

# Initialize prediction client
prediction_client = PredictionClient()
zone_mapper = ZoneMapper()
weather_service = WeatherService()

@router.post("", response_model=TripPrediction)
async def create_prediction(data: TripRequestIncoming):
    """
    Create a new prediction for taxi trip details.
    
    Returns predicted trip duration, fare amount, and other costs.
    """
    logger.info("Prediction endpoint called")
    logger.debug(f"Received request data: {data}")
    
    try:
        pickup_coords = (data.pickup_location.latitude, data.pickup_location.longitude)
        dropoff_coords = (data.dropoff_location.latitude, data.dropoff_location.longitude)

        pu_location_id, do_location_id = zone_mapper.get_location_ids(
            pickup_coords, dropoff_coords
        )

        if not pu_location_id or not do_location_id:
            raise HTTPException(
                status_code=400,
                detail="Could not map coordinates to taxi zones"
            )
        
        weather_data = weather_service.get_weather_data(data.pickup_datetime)
        logger.debug(f"Weather data: {weather_data}")

        model_request = TripRequestOutgoing(
            PULocationID=pu_location_id,
            DOLocationID=do_location_id,
            trip_distance=data.trip_distance,
            pickup_datetime=data.pickup_datetime,
            tavg=weather_data['tavg'],
            tmin=weather_data['tmin'],
            tmax=weather_data['tmax'],
            prcp=weather_data['prcp'],
            snow=weather_data['snow'],
            wdir=weather_data['wdir'],
            wspd=weather_data['wspd'],
            pres=weather_data['pres']
        )

        # Get prediction from model service
        prediction = prediction_client.get_prediction(model_request)
        
        logger.info("Successfully processed prediction request")

        if zone_mapper.is_below_60th_street_manhattan(do_location_id) or \
            zone_mapper.is_below_60th_street_manhattan(pu_location_id):
            prediction['congestion_surcharge'] = prediction.get('congestion_surcharge', 0) + 1.50
            prediction['total_amount'] = prediction.get('total_amount', 0) + 1.50
            logger.info("Added congestion pricing surcharge for below 60th Street Manhattan")
        
        logger.debug(f"Prediction result: {prediction}")

        return TripPrediction(**prediction)

    except HTTPException as e:
        logger.error(f"HTTP error during prediction: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))