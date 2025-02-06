import json
import uuid
from datetime import datetime
import logging
from typing import Dict, Any
import time
from fastapi import HTTPException
from redis_conn import redis_conn
from logger import Logger

logger = Logger.get_logger('PredictionClient')

class PredictionClient:
    def __init__(self):
        self.redis_client = redis_conn.client

    def get_prediction(self, data: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Send prediction request to model service and wait for response."""
        # Add request ID and convert datetime
        request_id = str(uuid.uuid4())
        data['request_id'] = request_id
        
        if isinstance(data.get('tpep_pickup_datetime'), datetime):
            data['tpep_pickup_datetime'] = data['tpep_pickup_datetime'].isoformat()

        logger.info(f"Sending prediction request {request_id}")
        logger.debug(f"Request data: {data}")

        # Send request to model service
        try:
            self.redis_client.lpush('prediction_requests', json.dumps(data))
            logger.info(f"Prediction request {request_id} sent successfully")
        except Exception as e:
            logger.error(f"Failed to send prediction request: {str(e)}")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")

        # Wait for response with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.redis_client.brpop('prediction_responses', timeout=1)
                if response is None:
                    continue

                _, response_data = response
                response_dict = json.loads(response_data)

                if response_dict.get('request_id') == request_id:
                    if 'error' in response_dict:
                        logger.error(f"Prediction request {request_id} failed: {response_dict['error']}")
                        raise HTTPException(status_code=500, detail=response_dict['error'])
                    
                    logger.info(f"Received prediction response for request {request_id}")
                    logger.debug(f"Response data: {response_dict}")
                    return response_dict

            except Exception as e:
                logger.error(f"Error while waiting for response: {str(e)}")
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")

        logger.error(f"Prediction request {request_id} timed out after {timeout} seconds")
        raise HTTPException(status_code=408, detail="Prediction request timed out")