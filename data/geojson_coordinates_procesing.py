import geopandas as gpd
from shapely.geometry import Point
#from geopy.distance import geodesic

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
            return zone
    
    return "Zona no encontrada"

if __name__ == "__main__":
    print("init")
    # Coordenadas de ejemplo
    lat = 40.6350  # Latitud de Borough Park
    lon = -73.9921  # Longitud de Borough Park

    # Ruta al archivo GeoJSON
    geojson_path = ("./NTA.geo.json")

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
    # distance_miles = calculate_distance_in_miles((start_lat, start_lon), (end_lat, end_lon))

    # Mostrar resultados
    print(f"Zona de origen: {start_zone}")
    print(f"Zona de destino: {end_zone}")
    # print(f"Distancia en millas: {distance_miles:.2f}")