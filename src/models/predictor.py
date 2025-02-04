from typing import Tuple, Dict, Any
import numpy as np
import joblib
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2
import pandas as pd

"""
Taxi trip prediction models.
"""
class DummyTaxiPredictor:
    def __init__(self):
        # Simula la carga de un modelo (no se necesita archivo .pkl)
        pass

    def predict_duration(self, input_data: Dict[str, Any]) -> float:
        # Devuelve un valor fijo o aleatorio para probar
        return np.random.uniform(10.0, 30.0)  # Ejemplo: entre 10 y 30 minutos

    def predict_fare(self, input_data: Dict[str, Any]) -> float:
        # Devuelve un valor fijo o aleatorio para probar
        return np.random.uniform(15.0, 50.0)  # Ejemplo: entre $15 y $50
    

class TaxiPredictor:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.duration_model = self._load_model("duration_model.pkl")
        self.fare_model = self._load_model("fare_model.pkl")

    def _load_model(self, model_name: str):
        """Load a serialized model from a file."""
        model_path = Path(__file__).parent / model_name
        if not model_path.exists():
            raise FileNotFoundError(f"Model file {model_name} not found.")
        return joblib.load(model_path)    
    
 
    def _preprocess_features(self, input_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepara las features para el modelo"""
        return pd.DataFrame([{
            'passenger_count': input_data['passenger_count'],
            'trip_distance': input_data['trip_distance'],
            'pickup_latitude': input_data['pickup_latitude'],
            'pickup_longitude': input_data['pickup_longitude'],
            'dropoff_latitude': input_data['dropoff_latitude'],
            'dropoff_longitude': input_data['dropoff_longitude']
        }])

    def predict_duration(self, input_data: Dict[str, Any]) -> float:
        processed_features = self._preprocess_features(input_data)
        return self.duration_model.predict(processed_features)[0]

    def predict_fare(self, input_data: Dict[str, Any]) -> float:
        processed_features = self._preprocess_features(input_data)
        return self.fare_model.predict(processed_features)[0]
       
    # def _preprocess_features(
    #     self,
    #     pickup_latitude: float,
    #     pickup_longitude: float,
    #     dropoff_latitude: float,
    #     dropoff_longitude: float,
    #     passengers: int,
    #     trip_distance: float
    # ) -> np.ndarray:
    #     """Preprocess the input features for prediction."""
    #     # Calculate additional features
    #     distance = self._calculate_distance(
    #         pickup_latitude, pickup_longitude, 
    #         dropoff_latitude, dropoff_longitude, trip_distance
    #     )
        
    #     features = np.array([
    #         pickup_latitude,
    #         pickup_longitude,
    #         dropoff_latitude,
    #         dropoff_longitude,
    #         passengers,
    #         trip_distance,
    #         distance
    #     ]).reshape(1, -1)
        
    #     return features
    
    # def _calculate_distance(
    #     self,
    #     pickup_lat: float,
    #     pickup_lon: float,
    #     dropoff_lat: float,
    #     dropoff_lon: float
    # ) -> float:
    #     """Calculate the haversine distance between two points."""
    #     # aca debemos ver que tecnica utilizamos para calcular la distancia 
    #     # Radius of the Earth in kilometers
    #     R = 6371.0

    #     # Convert latitude and longitude from degrees to radians
    #     lat1, lon1 = radians(pickup_lat), radians(pickup_lon)
    #     lat2, lon2 = radians(dropoff_lat), radians(dropoff_lon)

    #     # Difference in coordinates
    #     dlat = lat2 - lat1
    #     dlon = lon2 - lon1

    #     # Haversine formula
    #     a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    #     c = 2 * atan2(sqrt(a), sqrt(1 - a))

    #     # Distance in kilometers
    #     distance = R * c
    #     return distance
    

    # def predict(
    #     self,
    #     pickup_latitude: float,
    #     pickup_longitude: float,
    #     dropoff_latitude: float,
    #     dropoff_longitude: float,
    #     trip_distance: float,
    #     passengers: int
    # ) -> Tuple[float, float]:
    #     """Predict trip duration and fare."""
    #     try: 
    #         features = self._preprocess_features(
    #             pickup_latitude,
    #             pickup_longitude,
    #             dropoff_latitude,
    #             dropoff_longitude,
    #             trip_distance,
    #             passengers
    #         )
            
    #         duration = self.duration_model.predict(features)[0]
    #         fare = self.fare_model.predict(features)[0]
            
    #         return duration, fare
    #     except Exception as e:
    #         raise RuntimeError(f"Prediction failed: {e}")
