import streamlit as st

def set_page_config():
    """Initial page setup"""
    st.set_page_config(
        page_title="NYC Taxi Predictor (Demo)",
        page_icon="🚕",
        layout="wide",
        initial_sidebar_state="expanded"
    )

import pandas as pd
from pathlib import Path
import sys
import numpy as np
from datetime import datetime, timedelta
from route_map import plot_route 
from components.charts import plot_fare_distribution, create_metrics_dashboard, plot_trips_by_hour
from components.maps import create_pickup_dropoff_map, create_route_map, init_google_maps, create_heatmap

def generate_sample_data(n_samples=1000):
    """Generate sample data for demonstration"""
    np.random.seed(42)
    
    dates = [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(n_samples)]
    
    return pd.DataFrame({
        'pickup_datetime': dates,
        'pickup_latitude': np.random.normal(40.7128, 0.1, n_samples),
        'pickup_longitude': np.random.normal(-74.0060, 0.1, n_samples),
        'dropoff_latitude': np.random.normal(40.7128, 0.1, n_samples),
        'dropoff_longitude': np.random.normal(-74.0060, 0.1, n_samples),
        'fare_amount': np.random.uniform(10, 100, n_samples),
        'trip_distance': np.random.uniform(1, 20, n_samples),
        'trip_duration': np.random.uniform(5, 60, n_samples),
        'passenger_count': np.random.randint(1, 7, n_samples)
    })


def main():
    set_page_config()
    
    st.title("🚕 NYC Taxi Predictor")
    st.markdown("### Interface Demo")
    
    # Initialize Google Maps API
    api_key = init_google_maps()
    
    # datos de ejemplo
    df = generate_sample_data()

    if 'pickup_address' not in st.session_state:
        st.session_state.pickup_address = "Times Square, NY"
    if 'dropoff_address' not in st.session_state:
        st.session_state.dropoff_address = "Central Park, NY"

    tab1, tab2, tab3 = st.tabs(["Prediction","Data Analysis", "Statistics"])
    
    with tab1:
        st.header("Rate and Duration Prediction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Prediction form
            st.subheader("Trip Details")
            pickup_address = st.text_input(
                "Pickup Address", 
                value=st.session_state.pickup_address,
                key="pickup_input",
                on_change=update_pickup_address
            )
            
            dropoff_address = st.text_input(
                "Destination Address", 
                value=st.session_state.dropoff_address,
                key="dropoff_input", 
                on_change=update_dropoff_address
            )

            pickup_time = st.time_input("Pickup Time")
            pickup_date = st.date_input("Pickup Date")

            passengers = st.number_input("Number of Passengers", 1, 6, 1)

        if st.button("Calculate Prediction", type="primary"):
            if api_key:
                # Get route information and display map
                with col2:
                    st.subheader("Travel Route")
                    map_view, duration, distance = create_route_map(
                        pickup_address=pickup_address,
                        dropoff_address=dropoff_address,
                        api_key=api_key
                    )
                
                if duration and distance:
                    # Simulate the prediction using the real route data
                    col_pred1, col_pred2 = st.columns(2)
                    
                    with col_pred1: 
                        # Calculate estimated rate based on distance
                        estimated_rate = distance * 2.5  # Example rate calculation
                        st.metric("Estimated Rate", f"${estimated_rate:.2f}")
                        st.metric("Distance", f"{distance:.1f} km")
                    with col_pred2:
                        st.metric("Estimated Duration", f"{duration:.0f} min")
                        # Calculate arrival time
                        arrival_time = (datetime.combine(pickup_date, pickup_time) + 
                                      timedelta(minutes=duration)).strftime("%I:%M %p")
                        st.metric("Estimated Arrival", arrival_time)
            else:
                st.error("Please configure the Google Maps API key to use this feature")
        else:
            # Show default map view when no calculation is requested
            with col2:
                st.subheader("Travel Route")
                if api_key:
                    # Show initial route with default addresses
                    create_route_map(
                        pickup_address="Times Square, NY",
                        dropoff_address="Central Park, NY",
                        api_key=api_key
                    )
                else:
                    st.warning("Google Maps API key not configured. Showing static map.")
                    # Fallback to static map
                    create_pickup_dropoff_map(
                        40.7580, -73.9855,  # Times Square
                        40.7829, -73.9654   # Central Park
                    )
    
    with tab2:
        st.header("Data Analysis")
        
        # Métricas generales
        create_metrics_dashboard(df)
        
        # Visualizaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Tariff Distribution")
            plot_fare_distribution(df)
        
        with col2:
            st.subheader("Trips per Hour")
            plot_trips_by_hour(df)
        
        # Heatmap
        st.subheader("Popular Areas")
        create_heatmap(df)
    
    with tab3:
        st.header("Real-Time Statistics")
        
        # Métricas simuladas en tiempo real
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Active Travel",
                "127",
                "+5"
            )
        with col2:
            st.metric(
                "Average Wait Time",
                "4.5 min",
                "-0.5 min"
            )
        with col3:
            st.metric(
                "Average Rate (last hour)",
                "$28.50",
                "+$2.10"
            )
        with col4:
            st.metric(
                "Customer Satisfaction",
                "4.8/5",
                "+0.1"
            )
        
        # grafico de tendencias simuladas
        st.line_chart(
            pd.DataFrame(
                np.random.randn(24, 3).cumsum(0),
                columns=['Rates', 'Travel', 'Waiting Time']
            )
        )

def update_pickup_address():
    """Update pickup address in session state"""
    st.session_state.pickup_address = st.session_state.pickup_input

def update_dropoff_address():
    """Update dropoff address in session state"""
    st.session_state.dropoff_address = st.session_state.dropoff_input   
    
    # Footer
    st.markdown("---")
    st.markdown("📊 This is a demo with simulated data")

if __name__ == "__main__":
    main()
