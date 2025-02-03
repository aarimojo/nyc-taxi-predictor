import redis
from logger import Logger
import sys
import os
import time
from typing import Optional

# Configure logging
logger = Logger.get_logger('redis')

class RedisConnection:
    _instance: Optional['RedisConnection'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._connect()

    def _connect(self, max_retries: int = 5, retry_delay: int = 5):
        """Establish Redis connection with retry logic."""
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 6379))

        for attempt in range(max_retries):
            try:
                self._client = redis.Redis(
                    host=host,
                    port=port,
                    db=0,
                    decode_responses=True,
                    socket_timeout=5
                )
                # Test the connection
                self._client.ping()
                logger.info(f"Successfully connected to Redis at {host}:{port}")
                return
            except redis.ConnectionError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Could not connect to Redis after {max_retries} attempts: {str(e)}")
                    raise Exception(f"Could not connect to Redis after {max_retries} attempts: {str(e)}")
                logger.warning(f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._client is None:
            self._connect()
        return self._client

# Global Redis connection instance
redis_conn = RedisConnection()