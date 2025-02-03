from joblib import load
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from schema import TripData, TripPrediction
import json
import redis
import sys
import signal
import time
import os

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True

class Predictor:
    def __init__(self, local: bool = False, 
                 redis_host: str = os.getenv('REDIS_HOST', 'localhost'), 
                 redis_port: int = int(os.getenv('REDIS_PORT', 6379))):
        """Initialize predictor with validated data."""
        # Load taxi zone lookup data
        self.taxi_zones = pd.read_csv("./taxi_zones.csv")
        self.local = local
        
        # Load models
        self.fare_pipeline = load("xgb_model_fare_amount.pkl")
        self.duration_pipeline = load("xgb_model_trip_duration.pkl")

        # Initialize Redis connection
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = None

        if not self.local:
            print("initialized Predictor")

    def _connect_redis(self, max_retries: int = 5, retry_delay: int = 5):
        """Establish Redis connection with retry logic."""
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=0,
                    socket_timeout=5,
                    decode_responses=True  # Automatically decode responses to str
                )
                # Test the connection
                self.redis_client.ping()
                print(f"Successfully connected to Redis at {self.redis_host}:{self.redis_port}")
                return
            except redis.ConnectionError as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Could not connect to Redis after {max_retries} attempts: {str(e)}")
                print(f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    def start_listening(self):
        """Start listening for prediction requests on Redis."""        
        self._connect_redis()
        print("Starting to listen for prediction requests...")
        # Subscribe to the prediction request channel
        killer = GracefulKiller()
        
        # Listen for messages
        while not killer.kill_now:
            try:
                # This is more reliable across Redis versions and network conditions
                message = self.redis_client.brpop('prediction_requests', timeout=1)
                
                if message is None:
                    continue  # Timeout, check if we should exit
                
                _, data = message  # brpop returns (key, value)
                
                try:
                    # Parse the message data
                    data = json.loads(data)
                    request_id = data.pop('request_id', None)
                    
                    if self.local:
                        print(f"Received request {request_id}: {data}")
                    
                    # Convert string datetime to datetime object
                    if 'tpep_pickup_datetime' in data:
                        data['tpep_pickup_datetime'] = datetime.fromisoformat(data['tpep_pickup_datetime'])
                    
                    # Make prediction
                    prediction = self.predict(data)
                    
                    # Prepare response
                    response = {
                        'request_id': request_id,
                        'trip_duration': prediction.trip_duration,
                        'fare_amount': prediction.fare_amount,
                        'tolls_amount': prediction.tolls_amount,
                        'congestion_surcharge': prediction.congestion_surcharge,
                        'total_amount': prediction.total_amount
                    }
                    
                    # Push response to a list instead of using pub/sub
                    self.redis_client.lpush('prediction_responses', json.dumps(response))
                    
                    if self.local:
                        print(f"Sent response for request {request_id}")
                
                except Exception as e:
                    error_response = {
                        'request_id': request_id,
                        'error': str(e)
                    }
                    self.redis_client.lpush('prediction_responses', json.dumps(error_response))
                    if self.local:
                        print(f"Error processing request {request_id}: {str(e)}")
                        
            except redis.RedisError as e:
                print(f"Redis error: {str(e)}")
                # Try to reconnect
                try:
                    self._connect_redis()
                except Exception as e:
                    print(f"Failed to reconnect to Redis: {str(e)}")
                    if killer.kill_now:
                        break
                    time.sleep(5)  # Wait before retrying
                    
        print("Shutting down gracefully...")
        self.redis_client.close()
    

    def _enrich_location_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add borough, service zone, and zone information based on location IDs."""
        # Get pickup location info
        pu_info = self.taxi_zones[self.taxi_zones['LocationID'] == data['PULocationID']].iloc[0]
        do_info = self.taxi_zones[self.taxi_zones['LocationID'] == data['DOLocationID']].iloc[0]
        
        enriched_data = {
            **data,  # Original data
            'Borough_pu': pu_info['Borough'],
            'Borough_do': do_info['Borough'],
            'service_zone_pu': pu_info['service_zone'],
            'service_zone_do': do_info['service_zone'],
            'Zone_pu': pu_info['Zone'],
            'Zone_do': do_info['Zone']
        }
        
        if self.local:
            print("enriched data: ", enriched_data)
        
        return enriched_data
    
    def predict(self, data: Dict[str, Any]) -> TripPrediction:
        """Make predictions and return validated TripPrediction."""
        enriched_data = self._enrich_location_data(data)
        
        # Validate enriched data using Pydantic model
        validated_data = TripData(**enriched_data)

        if self.local:
            print("validated data: ", validated_data)
        
        # Convert validated data to DataFrame using the model's dump method
        df_data, features = validated_data.model_dump_features()
        self.df = pd.DataFrame([df_data], columns=features)

        
        if self.local:
            print("predicting on: \n", self.df.iloc[0])
            
        fare = float(self.fare_pipeline.predict(self.df)[0])
        duration = float(self.duration_pipeline.predict(self.df)[0])
        tolls_amount = 0
        congestion_surcharge = 0
        total = fare + tolls_amount + congestion_surcharge
        
        return TripPrediction(
            fare_amount=fare,
            trip_duration=duration,
            tolls_amount=tolls_amount,
            congestion_surcharge=congestion_surcharge,
            total_amount=total
        )


def main(local: bool = False):
    try:
        predictor = Predictor(local=local)
        predictor.start_listening()
    except Exception as e:
        print(f"Error in main: {str(e)}")
        sys.exit(1)

def test_predictor():
    sample_data = {
        "PULocationID": 132,  # JFK Airport
        "DOLocationID": 236,  # Upper East Side North
        "store_and_fwd_flag": "N",
        "trip_distance": 3.66,
        "tpep_pickup_datetime": datetime.now()
    }
    other_sample_data = {
        "PULocationID": 132,
        "DOLocationID": 211,
        "store_and_fwd_flag": "N",
        "trip_distance": 10.66,
        "tpep_pickup_datetime": datetime.now()
    }
    predictor = Predictor(local=True)
    prediction = predictor.predict(other_sample_data)
    print("prediction: ", prediction.model_dump())
    print(f"Prediction: {prediction}")
    print(f"Trip Duration: {prediction.trip_duration:.2f} minutes")
    print(f"Fare Amount: ${prediction.fare_amount:.2f}")
    print(f"Tolls Amount: ${prediction.tolls_amount:.2f}")

if __name__ == "__main__":
    main()
