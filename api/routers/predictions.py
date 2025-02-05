from fastapi import APIRouter, HTTPException, Query
from api.schemas.prediction import TripRequest, TripPrediction
from src.models.predictor import TaxiPredictor
from src.models.predictor import DummyTaxiPredictor  

router = APIRouter()
predictor = TaxiPredictor()


@router.get('/predict')
def predict_trip(
    pickup_latitude: float = Query(..., ge=-90, le=90),
    pickup_longitude: float = Query(..., ge=-180, le=180),
    dropoff_latitude: float = Query(..., ge=-90, le=90),
    dropoff_longitude: float = Query(..., ge=-180, le=180),
    passengers: int = Query(..., ge=1, le=6)
):
    """
    Predict the trip duration and fare amount.
    """
    
    duration, fare = predictor.predict(
        pickup_latitude=pickup_latitude,
        pickup_longitude=pickup_longitude,
        dropoff_latitude=dropoff_latitude,
        dropoff_longitude=dropoff_longitude,
        passengers=passengers
    )
    
    return {
        "duration": float(duration),
        "fare": float(fare)
    }

    
@router.post("/predict")
async def predict(input_data: dict):
    try:
        predictor = TaxiPredictor() 
        duration = predictor.predict_duration(input_data)
        fare = predictor.predict_fare(input_data)
        return {
            "duration": round(duration, 2),
            "fare": round(fare, 2)
        }
    except Exception as e:
        return {"error": str(e)}   