import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
from frontend.components.maps import get_route_from_google
from utils.logger import Logger

API_URL = "http://127.0.0.1:8000/api/v1/predict"  # cambiar si el backend esta en otro host

logger = Logger.setup()

st.title("NYC Taxi Fare Predictor")

# Inputs del usuario
pickup_latitude = st.number_input("Pickup Latitude", value=40.730610, format="%.6f")
pickup_longitude = st.number_input("Pickup Longitude", value=-73.935242, format="%.6f")
dropoff_latitude = st.number_input("Dropoff Latitude", value=40.750610, format="%.6f")
dropoff_longitude = st.number_input("Dropoff Longitude", value=-73.955242, format="%.6f")
passengers = st.slider("Passengers", 1, 6, 1)



if st.button("Predict Fare & Duration"):
    pickup_coords = f"{pickup_latitude},{pickup_longitude}"
    dropoff_coords = f"{dropoff_latitude},{dropoff_longitude}"
    try:
        _, _, _, trip_distance = get_route_from_google(
        pickup_coords, 
        dropoff_coords, 
        GOOGLE_MAPS_API_KEY
        )

        data = {
            "pickup_latitude": pickup_latitude,
            "pickup_longitude": pickup_longitude,
            "dropoff_latitude": dropoff_latitude,
            "dropoff_longitude": dropoff_longitude,
            "passenger_count": passengers,
            "trip_distance": trip_distance
        }

        response = requests.post(API_URL, json=data)

        if response.status_code == 200:
            result = response.json()
            st.success(f"Predicted Duration: {result['duration']} minutes")
            st.success(f"Predicted Fare: ${result['fare']}")

            # Crear mapa con Folium
            map = folium.Map(location=[pickup_latitude, pickup_longitude], zoom_start=12)

            # Agregar marcadores de pickup y dropoff
            folium.Marker([pickup_latitude, pickup_longitude], tooltip="Pickup", icon=folium.Icon(color="blue")).add_to(map)
            folium.Marker([dropoff_latitude, dropoff_longitude], tooltip="Dropoff", icon=folium.Icon(color="red")).add_to(map)

            folium_static(map)  # Mostrar el mapa en Streamlit

        else:
            st.error("Error en la predicción. Inténtalo nuevamente.")
    except Exception as e:
        st.error(f"Error calculando la ruta: {str(e)}")       
