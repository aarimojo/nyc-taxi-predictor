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
            geojson_path = Path(__file__).parent.parent / 'data' / 'nycneighborhoods_converted.geo.json'
            self.zones_gdf = gpd.read_file(str(geojson_path))
            
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
                    zone_name = zone['zone_name']
                    borough = zone['borough']
                    location_id = zone['zone_id']
                    service_zone = zone['service_zone']
                    logger.info(f"Zone: {zone}")                  
                    return {
                        'location_id': int(location_id),
                        'borough': borough,
                        'zone': zone_name,
                        'service_zone': service_zone
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
    
    def is_below_60th_street_manhattan(self, location_id: int) -> bool:
        """Check if location is in Manhattan below 60th Street."""
        # Get zone info for the location
        logger.info(f"Checking if location ID {location_id} is below 60th street in Manhattan")
        # List of zones below 60th street in Manhattan
        below_60th_location_ids = [
            12,   # Battery Park
            13,   # Battery Park City
            45,   # Chinatown
            48,   # Clinton East
            50,   # Clinton West
            68,   # East Chelsea
            79,   # East Village
            87,   # Financial District North
            88,   # Financial District South
            90,   # Flatiron
            100,  # Garment District
            107,  # Gramercy
            113,  # Greenwich Village North
            114,  # Greenwich Village South
            125,  # Hudson Sq
            137,  # Kips Bay
            144,  # Little Italy/NoLiTa (SoHo-TriBeCa-Civic Center-Little Italy)
            148,  # Lower East Side
            161,  # Midtown Center
            162,  # Midtown East
            163,  # Midtown North
            164,  # Midtown South
            170,  # Murray Hill
            186,  # Penn Station/Madison Sq West
            209,  # Seaport
            211,  # SoHo (another SoHo-TriBeCa-Civic Center-Little Italy entry)
            224,  # Stuy Town/Peter Cooper Village
            229,  # Sutton Place/Turtle Bay North
            230,  # Times Sq/Theatre District
            231,  # TriBeCa (another SoHo-TriBeCa-Civic Center-Little Italy entry)
            232,  # Two Bridges/Seward Park
            234,  # Union Sq
            246,  # West Chelsea/Hudson Yards
            249   # West Village
        ]

        return location_id in below_60th_location_ids