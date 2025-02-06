import requests
from datetime import datetime
from typing import Dict, Optional
from utils.config import API_URL
from utils.logger import Logger

logger = Logger.get_logger('utils.api')

def predict_trip(
    pickup_coords: tuple,
    dropoff_coords: tuple,
    trip_distance: float,
    pickup_datetime: Optional[datetime] = None
) -> Dict:
    """
    Call the predictions API endpoint to get trip predictions.
    """
    logger.info("Calling predictions API")
    logger.info(f"Values are {pickup_coords}, {dropoff_coords}, {trip_distance}, {pickup_datetime}")
    
    if pickup_datetime is None:
        pickup_datetime = datetime.now()

    # Prepare request data
    data = {
        "pickup_location": {
            "latitude": pickup_coords['pickup_lat'],
            "longitude": pickup_coords['pickup_lon']
        },
        "dropoff_location": {
            "latitude": dropoff_coords['dropoff_lat'],
            "longitude": dropoff_coords['dropoff_lon']
        },
        "trip_distance": trip_distance,
        "store_and_fwd_flag": "N",
        "tpep_pickup_datetime": pickup_datetime.isoformat()
    }

    logger.debug(f"Request data: {data}")

    try:
        response = requests.post(
            f"{API_URL}/api/v1/predictions",
            json=data
        )
        response.raise_for_status()
        
        prediction = response.json()
        logger.info("Successfully received prediction")
        logger.debug(f"Prediction response: {prediction}")
        
        return prediction

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling predictions API: {str(e)}")
        raise Exception(f"Failed to get prediction: {str(e)}")