import os
import requests
from datetime import datetime
import pandas as pd
from pathlib import Path
from fastapi import HTTPException
from logger import Logger
from typing import Optional
import json

logger = Logger.get_logger('services.weather_services')


class WeatherService:
    def __init__(self):
        self.url = "https://meteostat.p.rapidapi.com/stations/daily"
        self.key = os.getenv("RAPIDAPI_KEY")
        self.host = os.getenv("RAPIDAPI_HOST")
        if not self.key or not self.host:
            raise HTTPException(
                status_code=500,
                detail="Server environment variables not set"
            )
        logger.info(f"Weather service initialized")
        self.cache_dir = Path(str(Path(os.getcwd()) / "data" / "weather_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_weather_data(self, date: datetime) -> dict:
        """Get weather data for a specific date, either from cache, API, or backup."""
        date_str = date.strftime('%Y-%m-%d')
        logger.info(f"Getting weather data for {date_str}")
        cache_file = self.cache_dir / f"weather_{date_str}.json"

        # Try cache first
        if cache_file.exists():
            logger.info(f"Weather data found in cache for {date_str}")
            try:
                df = pd.read_json(cache_file)
                logger.info(f"Weather data loaded from cache for {date_str}")
                return df.to_dict('records')[0]
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
                # Continue to API if cache fails
        
        # Try API next
        try:
            weather_data = self._fetch_weather_data(date_str)
            try:
                pd.DataFrame([weather_data]).to_json(cache_file)
                logger.info(f"Weather data cached for {date_str}")
            except Exception as e:
                logger.error(f"Error writing cache: {e}")
            return weather_data
        except Exception as e:
            logger.warning(f"Failed to get weather data from API: {e}")
            
            # Fall back to backup data using same month/day from 2024
            backup_date = date.replace(year=2024)
            backup_data = self._get_backup_weather_data(backup_date)
            if backup_data:
                logger.info(f"Using backup weather data from 2024 for {date_str}")
                return backup_data
            else:
                raise HTTPException(
                    status_code=502,
                    detail="Could not retrieve weather data from any source"
                )

    def _fetch_weather_data(self, date: str) -> dict:
        """Fetch weather data from the API for a specific date."""
        url = "https://meteostat.p.rapidapi.com/stations/daily"
        params = {
            "station": "KNYC0",  # Central Park Station
            "start": date,
            "end": date,
            "model": "true",
            "tz": "America/New_York"
        }
        headers = {
            "X-RapidAPI-Key": self.key,
            "X-RapidAPI-Host": self.host
        }
        
        logger.info(f"Fetching weather data from {url} with params: {params}")
        logger.info(f"Headers: {headers}")
        try:
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"Response status: {response.status_code}, data: {response.json()}")
            if response.ok and 'data' in response.json():
                weather_data = response.json()['data'][0]
                logger.info(f"Weather data: {weather_data}")
                # Ensure all required fields are present
                required_fields = ['tavg', 'tmin', 'tmax', 'prcp', 'snow', 'wdir', 'wspd', 'pres']
                weather_dict = {}
                for field in required_fields:
                    value = weather_data.get(field)
                    weather_dict[field] = 0 if value is None else value
                return weather_dict
            else:
                logger.error(f"Weather API error: {response.text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Weather API error: {response.text}"
                )
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail=f"Error fetching weather data: {str(e)}"
            )
        
    def _get_backup_weather_data(self, date: datetime) -> Optional[dict]:
        """Get weather data from backup file for the same month/day in 2024."""
        try:
            # Load backup data
            backup_file = Path(str(Path(os.getcwd()) / "cache" / "backup_weather_data.json"))
            logger.info(f"Loading backup weather data from {backup_file}")

            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Find matching date (only compare month and day)
            date_str = date.strftime('%Y-%m-%d')
            for entry in backup_data['data']:
                backup_date = datetime.strptime(entry['date'], '%Y-%m-%d %H:%M:%S')
                if (backup_date.month == date.month and 
                    backup_date.day == date.day):
                    logger.info(f"Found matching backup data for {date_str}")
                    # Ensure all required fields are present
                    required_fields = ['tavg', 'tmin', 'tmax', 'prcp', 'snow', 'wdir', 'wspd', 'pres']
                    weather_dict = {}
                    for field in required_fields:
                        value = entry.get(field)
                        weather_dict[field] = 0 if value is None else value
                    return weather_dict
            
            logger.warning(f"No matching backup data found for {date_str}")
            return None
        except Exception as e:
            logger.error(f"Error reading backup weather data: {e}")
            return None