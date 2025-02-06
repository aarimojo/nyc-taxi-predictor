from typing import Tuple, Optional, Dict, Any
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
from pathlib import Path
from logger import Logger

logger = Logger.get_logger('services.zone_mapper')

class ZoneMapper:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._load_data()

    def _load_data(self):
        """Load GeoJSON and taxi zone data."""
        try:
            # Load GeoJSON data
            geojson_path = Path(__file__).parent.parent / 'data' / 'NTA.geo.json'
            self.zones_gdf = gpd.read_file(str(geojson_path))
            
            # Load taxi zones mapping
            zones_path = Path(__file__).parent.parent / 'data' / 'taxi_zones.csv'
            self.taxi_zones = pd.read_csv(str(zones_path))
            
            logger.info("Successfully loaded zone mapping data")
        except Exception as e:
            logger.error(f"Failed to load zone mapping data: {str(e)}")
            raise

    def get_zone_from_coordinates(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get taxi zone information for given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing zone information or None if not found
        """
        try:
            # Create point from coordinates
            point = Point(lon, lat)
            
            # Find the zone containing the point
            for _, zone in self.zones_gdf.iterrows():
                if point.within(zone['geometry']):
                    # Get corresponding taxi zone info
                    zone_name = zone['NTAName']
                    logger.info(f"Zone name: {zone_name}")
                    taxi_zone = self.taxi_zones[
                        self.taxi_zones['Zone'].str.contains(zone_name, case=False, na=False)
                    ].iloc[0]
                    logger.info(f"Taxi zone: {taxi_zone}")                    
                    return {
                        'location_id': int(taxi_zone['LocationID']),
                        'borough': taxi_zone['Borough'],
                        'zone': taxi_zone['Zone'],
                        'service_zone': taxi_zone['service_zone']
                    }
            
            logger.warning(f"No zone found for coordinates: {lat}, {lon}")
            return None

        except Exception as e:
            logger.error(f"Error getting taxi_zone for coordinates {lat}, {lon}: {str(e)}, using default unknown zone 265")
            return {
                    'location_id': 265,
                    'borough': 'Unknown',
                    'zone': 'N/A',
                    'service_zone': 'N/A'
                }

    def get_location_ids(self, pickup_coords: Tuple[float, float], 
                        dropoff_coords: Tuple[float, float]) -> Tuple[Optional[int], Optional[int]]:
        """
        Get pickup and dropoff location IDs for given coordinates.
        
        Args:
            pickup_coords: Tuple of (latitude, longitude) for pickup
            dropoff_coords: Tuple of (latitude, longitude) for dropoff
            
        Returns:
            Tuple of (pickup_location_id, dropoff_location_id)
        """
        pickup_zone = self.get_zone_from_coordinates(pickup_coords[0], pickup_coords[1])
        dropoff_zone = self.get_zone_from_coordinates(dropoff_coords[0], dropoff_coords[1])

        pickup_id = pickup_zone['location_id'] if pickup_zone else 265
        dropoff_id = dropoff_zone['location_id'] if dropoff_zone else 265

        return pickup_id, dropoff_id