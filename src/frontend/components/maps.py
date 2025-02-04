# src/frontend/components/maps.py
import googlemaps
from googlemaps import convert

import streamlit as st
import folium
from folium import plugins
from streamlit_folium import folium_static
import pandas as pd
import requests
from datetime import datetime
import polyline
import os
import json


def get_coordinates(address, api_key):
    """Convert address to latitude and longitude using Google Geocoding API."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'results' not in data or not data['results']:
            st.error(f"No se encontraron coordenadas para la dirección: {address}")
            return None, None

        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']

    except requests.exceptions.RequestException as e:
        st.error(f"Error en la solicitud de geocodificación: {e}")
        return None, None

def get_route_from_google(pickup_address, dropoff_address, api_key):
    """
    Get route information from Google Routes API.
    """
    # Convert addresses to coordinates
    pickup_lat, pickup_lon = get_coordinates(pickup_address, api_key)
    dropoff_lat, dropoff_lon = get_coordinates(dropoff_address, api_key)

    if None in (pickup_lat, pickup_lon, dropoff_lat, dropoff_lon):
        return None, None, None
       
    # Define the API endpoint and headers
    base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
    }
    
    # Define the request body
    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": pickup_lat,
                    "longitude": pickup_lon
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": dropoff_lat,
                    "longitude": dropoff_lon
                }
            }
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False,
        "languageCode": "en-US",
        "units": "IMPERIAL"
    }
    
    # Make the API request
    try:
        response = requests.post(base_url, headers=headers, json=body)
        response.raise_for_status()
        route_data = response.json()

        distance_meters = route_data['routes'][0]['distanceMeters']
        distance_km = round(distance_meters / 1000, 2)

        return route_data, (pickup_lat, pickup_lon), (dropoff_lat, dropoff_lon), distance_km

    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        raise Exception(f"Error calling Google Routes API: {error_message}")
    
def create_route_map(pickup_address, dropoff_address, api_key):
    """
    Creates a map showing the route between pickup and dropoff locations
    """
    try:
        # Obtener la ruta usando la función existente
        route_data = get_route_from_google(pickup_address, dropoff_address, api_key)
        
        if not route_data or 'routes' not in route_data:
            st.error("No se pudo obtener la ruta")
            return None, None, None
            
        route = route_data['routes'][0]
        
        # Obtener coordenadas de inicio y fin
        pickup_lat, pickup_lon = get_coordinates(pickup_address, api_key)
        dropoff_lat, dropoff_lon = get_coordinates(dropoff_address, api_key)
        
        # Crear mapa
        center_lat = (pickup_lat + dropoff_lat) / 2
        center_lng = (pickup_lon + dropoff_lon) / 2
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=13,
            tiles="OpenStreetMap"
        )
        
        # Añadir marcadores
        folium.Marker(
            [pickup_lat, pickup_lon],
            popup=pickup_address,
            icon=folium.Icon(color='green', icon='info-sign'),
        ).add_to(m)
        
        folium.Marker(
            [dropoff_lat, dropoff_lon],
            popup=dropoff_address,
            icon=folium.Icon(color='red', icon='info-sign'),
        ).add_to(m)
        
        # Decodificar y añadir la polyline de la ruta
        if 'polyline' in route:
            points = polyline.decode(route['polyline']['encodedPolyline'])
            folium.PolyLine(
                points,
                weight=3,
                color='blue',
                opacity=0.8
            ).add_to(m)
        
        # Calcular duración y distancia
        duration = route['duration'] / 60  # Remove 's' from duration string
        distance = float(route['distanceMeters']) / 1000  # Convert to km
        
        # Mostrar el mapa
        folium_static(m)
        
        return m, duration, distance
            
    except Exception as e:
        st.error(f"Error creating route map: {str(e)}")
        return None, None, None
    
def decode_polyline(polyline_str):
    """Decode a Google Maps polyline into a list of latitude/longitude pairs."""
    import polyline
    return polyline.decode(polyline_str)

def init_google_maps():
    """
    Initialize Google Maps settings
    """
    # Get API key from environment variable or Streamlit secrets
    try:
        api_key = os.getenv('GOOGLE_MAPS_API_KEY') or st.secrets["GOOGLE_MAPS_API_KEY"]
        if not api_key:
            raise ValueError("API key no encontrada")
        return api_key
    except Exception as e:
        st.error(f"Error al obtener API key: {e}")
        return None
    
def create_pickup_dropoff_map(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon):
    """
    Create a map with pickup and dropoff markers and a line connecting them
    """
    try:
        # Calcular el centro del mapa
        center_lat = (pickup_lat + dropoff_lat) / 2
        center_lon = (pickup_lon + dropoff_lon) / 2
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # A;ade el marcador de pickup (verde)
        folium.Marker(
            [pickup_lat, pickup_lon],
            popup='Pick up point',
            icon=folium.Icon(color='green', icon='flag')
        ).add_to(m)
        
        # A;ade el marcador de dropoff (rojo)
        folium.Marker(
            [dropoff_lat, dropoff_lon],
            popup='Destination point',
            icon=folium.Icon(color='red', icon='flag')
        ).add_to(m)
        
        points = [
            [pickup_lat, pickup_lon],
            [dropoff_lat, dropoff_lon]
        ]
        
        folium.PolyLine(
            points,
            weight=3,
            color='blue',
            opacity=0.8
        ).add_to(m)
        
        return folium_static(m)
    
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
        return None




def create_heatmap(df, latitude_col='pickup_latitude', longitude_col='pickup_longitude'):
    """
    Create a heat map based on point density
    """
    try:
        # Crear mapa base centrado en NYC
        m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)
        
        # Preparar datos para el heatmap
        # Usamos solo las primeras 1000 filas para mejor rendimiento
        sample_size = min(1000, len(df))
        df_sample = df.sample(n=sample_size)
        
        # Crear lista de puntos para el heatmap
        heat_data = [
            [row[latitude_col], row[longitude_col]]
            for idx, row in df_sample.iterrows()
        ]
        
        plugins.HeatMap(heat_data).add_to(m)
        
        return folium_static(m)
    
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
        return None

def create_zone_map(df):
    """
    Create a map with circles representing different areas and their statistics
    """
    try:
        # Crear mapa base
        m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)
        
        # Agrupa datos por zonas (redondeando coordenadas para crear zonas)
        df['lat_zone'] = df['pickup_latitude'].round(3)
        df['lon_zone'] = df['pickup_longitude'].round(3)
        
        zone_stats = df.groupby(['lat_zone', 'lon_zone']).agg({
            'fare_amount': ['mean', 'count']
        }).reset_index()
        
        for _, row in zone_stats.iterrows():
            # El radio del círculo es proporcional al número de viajes?
            radius = row[('fare_amount', 'count')] / 10  # TBD --> Ajustar segun datos reales
            
            folium.CircleMarker(
                location=[row['lat_zone'], row['lon_zone']],
                radius=min(radius, 20),  # Limitar el tama;o max
                popup=f"""
                    <b>Area statistics:</b><br>
                    Number of trips: {row[('fare_amount', 'count')]}<br>
                    Average fare: ${row[('fare_amount', 'mean')]:.2f}
                """,
                color='blue',
                fill=True,
                fill_color='blue'
            ).add_to(m)
        
        # Mostrar el mapa en Streamlit
        return folium_static(m)
    
    except Exception as e:
        st.error(f"Error creating zone map: {str(e)}")
        return None

def display_route_details(distance_km, duration_min, fare_usd):
    """
    Displays route details in a nice format
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Distance",
            value=f"{distance_km:.1f} km"
        )
    
    with col2:
        st.metric(
            label="Estimated Duration",
            value=f"{int(duration_min)} min"
        )
    
    with col3:
        st.metric(
            label="Estimated Rate",
            value=f"${fare_usd:.2f}"
        )

