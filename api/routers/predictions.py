from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
from prediction_client import PredictionClient
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

@router.post("", response_model=Dict[str, float])
async def create_prediction(data: Dict[str, Any]):
    """
    Create a new prediction for taxi trip details.
    
    Returns predicted trip duration, fare amount, and other costs.
    """
    logger.info("Prediction endpoint called")
    logger.debug(f"Received request data: {data}")
    
    try:
        # Convert string datetime to datetime object if needed
        if isinstance(data.get('tpep_pickup_datetime'), str):
            data['tpep_pickup_datetime'] = datetime.fromisoformat(data['tpep_pickup_datetime'])

        # Get prediction from model service
        prediction = prediction_client.get_prediction(data)
        
        logger.info("Successfully processed prediction request")
        logger.debug(f"Prediction result: {prediction}")

        return {
            "trip_duration": prediction["trip_duration"],
            "fare_amount": prediction["fare_amount"],
            "tolls_amount": prediction["tolls_amount"],
            "congestion_surcharge": prediction["congestion_surcharge"],
            "total_amount": prediction["total_amount"]
        }

    except HTTPException as e:
        logger.error(f"HTTP error during prediction: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))