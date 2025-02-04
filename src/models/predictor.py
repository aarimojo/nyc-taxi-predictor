from typing import Tuple, Dict, Any
import numpy as np
import joblib
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2
import pandas as pd

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
    """
    Taxi trip prediction models.
    """
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
       
