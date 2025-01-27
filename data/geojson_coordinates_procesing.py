import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import geodesic

def get_zone_from_coordinates(lat, lon, geojson_path):
    """
    Determina la zona de Nueva York basada en coordenadas geográficas.
    
    Args:
        lat (float): Latitud de la ubicación.
        lon (float): Longitud de la ubicación.
        geojson_path (str): Ruta al archivo GeoJSON con las delimitaciones de las zonas.
    
    Returns:
        str: Nombre de la zona correspondiente o un mensaje si no se encuentra.
    """
    # Cargar las zonas desde el archivo GeoJSON
    zones = gpd.read_file(geojson_path)
    
    # Crear un punto a partir de las coordenadas
    point = Point(lon, lat)
    
    # Buscar la zona que contiene el punto
    for _, zone in zones.iterrows():
        if point.within(zone['geometry']):
            return zone['ntaname']  # Aquí usamos 'ntaname' para obtener el nombre de la zona
    
    return "Zona no encontrada"

def calculate_distance_in_miles(start_coords, end_coords):
    """
    Calcula la distancia en millas entre dos coordenadas geográficas.
    
    Args:
        start_coords (tuple): Coordenadas (lat, lon) del punto de origen.
        end_coords (tuple): Coordenadas (lat, lon) del punto de destino.
    
    Returns:
        float: Distancia en millas.
    """
    # Calcular la distancia en kilómetros y convertirla a millas
    distance_km = geodesic(start_coords, end_coords).km
    distance_miles = distance_km * 0.621371  # Convertir kilómetros a millas
    return distance_miles

if __name__ =="main":
    # Coordenadas de ejemplo
    lat = 40.6350  # Latitud de Borough Park
    lon = -73.9921  # Longitud de Borough Park

    # Ruta al archivo GeoJSON
    geojson_path = ("../data/NTA map.geojson")

    # Llamada a la función
    zone_name = get_zone_from_coordinates(lat, lon, geojson_path)
    print(zone_name)  # Debería devolver "Borough Park" si las coordenadas coinciden.
      # Ruta al archivo GeoJSON
    start_lat, start_lon = 40.7128, -74.0060  # Coordenadas del origen
    end_lat, end_lon = 40.7306, -73.9352  # Coordenadas del destino

    # Obtener las zonas de origen y destino
    start_zone = get_zone_from_coordinates(start_lat, start_lon, geojson_path)
    end_zone = get_zone_from_coordinates(end_lat, end_lon, geojson_path)

    # Calcular la distancia en millas
    distance_miles = calculate_distance_in_miles((start_lat, start_lon), (end_lat, end_lon))

    # Mostrar resultados
    print(f"Zona de origen: {start_zone}")
    print(f"Zona de destino: {end_zone}")
    print(f"Distancia en millas: {distance_miles:.2f}")