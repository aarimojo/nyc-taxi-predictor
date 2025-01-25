import folium
import polyline
from streamlit_folium import folium_static
import streamlit as st
#route_map.py
def plot_route(api_response):
    try:
        # Decode the overview_polyline points from the response
        route_polyline = api_response['routes'][0]['overview_polyline']['points']
        decoded_polyline = polyline.decode(route_polyline)
        
        # The start location (first point of the decoded polyline)
        start_lat, start_lng = decoded_polyline[0]
        
        # Create the map centered on the start point
        m = folium.Map(location=[start_lat, start_lng], zoom_start=13)

        # Plot the route polyline
        folium.PolyLine(locations=decoded_polyline, color='blue', weight=4).add_to(m)

        # Optional: Add markers for the start and end locations
        end_lat, end_lng = decoded_polyline[-1]  # Use the last point for the end location
        folium.Marker([start_lat, start_lng], popup="Start").add_to(m)
        folium.Marker([end_lat, end_lng], popup="End").add_to(m)

        # Display the map in Streamlit
        st.write("## Route Map")
        folium_static(m)

    except KeyError as e:
        st.write(f"Error: Missing key in the response data: {e}")
    except Exception as e:
        st.write(f"An error occurred: {e}")