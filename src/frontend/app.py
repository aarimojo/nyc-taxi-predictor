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
    
    # datos de ejemplo
    df = generate_sample_data()
    
    tab1, tab2, tab3 = st.tabs(["Prediction","Data Analysis", "Statistics"])
    
    with tab1:
        st.header("Rate and Duration Prediction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Prediction form
            st.subheader("Trip Details")
            pickup_address = st.text_input("Pickup Address", "Times Square, NY")
            dropoff_address = st.text_input("Destination Address", "Central Park, NY")

            pickup_time = st.time_input("Pickup Time")
            pickup_date = st.date_input("Pickup Date")

            passengers = st.number_input("Number of Passengers", 1, 6, 1)

        # Initialize Google Maps API
        api_key = init_google_maps()

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
    
    # Footer
    st.markdown("---")
    st.markdown("📊 This is a demo with simulated data")

if __name__ == "__main__":
    main()

# api_response = {
#     "geocoded_waypoints": [
#         {"geocoder_status": "OK", "partial_match": True, "place_id": "ChIJmQJIxlVYwokRLgeuocVOGVU", "types": ["establishment", "point_of_interest", "tourist_attraction"]},
#         {"geocoder_status": "OK", "partial_match": True, "place_id": "ChIJ4zGFAZpYwokRGUGph3Mf37k", "types": ["establishment", "park", "point_of_interest", "tourist_attraction"]}
#     ],
#     "routes": [
#         {
#             "overview_polyline": {"points": "wywwF~eqbML?{CdJm@jBo@c@iAu@wA}@aDuBcC{AyByAmKaHaKwGOKMGS[BI@I@[G_@OWSS_@OI?M@"},
#             "legs": [
#                 {
#                     "steps": [
#                         {"polyline": {"points": "wywwF~eqbMDAF@"}},
#                         {"polyline": {"points": "iywwF~eqbMuBlGe@vAm@jB"}},
#                         {"polyline": {"points": "s_xwFptqbMo@c@]Uk@_@]SGE_@WQKc@YUOeAs@a@Wc@YECi@]o@_@SOUOIGeAq@aAq@WOa@W}ByAYSu@g@m@_@UQqAy@QM[SmAy@_@UmAy@w@g@MIGEGEMGS["}},
#                         {"polyline": {"points": "gmywFbspbM@C@E?E@C?E@E?E?IAA?ICKAGAECECGECCEEECCECCCCACACACACACAC?A?A?A?A?A?A?C?A?C@A?"}}
#                     ]
#                 }
#             ]
#         }
#     ]
# }

# plot_route(api_response)


# src_path = str(Path(__file__).parent.parent)
# sys.path.append(src_path)

# from ..data.data_loader import load_data
# from ..models.predictor import predict

# def set_page_config():
#     """Config inicial de la pag"""
#     st.set_page_config(
#         page_title="NYC Taxi Predictor",
#         page_icon="🚕",
#         layout="wide",
#         initial_sidebar_state="expanded"
#     )

# def sidebar_filters():
#     """Sidebar filters"""
#     st.sidebar.header("Filters")

#     date_range = st.sidebar.date_input(
#         "Select date range",
#         value=[pd.to_datetime('2024-01-01'), pd.to_datetime('2024-01-31')]
#     )

#     passenger_count = st.sidebar_slider(
#         "Passenger numbers",
#         min_value = 1,
#         max_value = 6,
#         value = 1
#     )

#     return date_range, passenger_count


# def main_content():
#     """Main content of the application"""
#     st.title("🚕 NYC Taxi Fare & Duration Predictor")

#     tab1, tab2, tab3 = st.tabs(['Predict', 'Data Analysis', 'Statistics'])

#     with tab1:
#         st.header("Rate and Duration Prediction")
#         col1, col2 = st.columns(2)

#         with col1:
#             pickup_location = st.text_input("Pickup location")
#             dropoff_location = st.text_input("Dropoff location")
#             pickup_datetime = st.datetime_input("Pickup Date & Time")

#             if st.button("Calculate Prediction"):
#                 # Your prediction functions would go here
#                 st.success("Prediction calculated!")
#                 # Show results
#                 st.metric("Estimated Fare", "$25.50")
#                 st.metric("Estimated Duration", "15 min")

#         with col2:
#             # Here should be appear the map
#             st.write("Map Route")
#             # Placeholder for the map
#             st.empty()

#     with tab2:
#         st.header("Analysis of Historical Data")
#         try:
#             df = load_data()

#             # show general metrics
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Total Trips", f"{len(df):,}")
#             with col2:
#                 st.metric("Average Rate", f"${df['fare_amount'].mean():.2f}")
#             with col3:
#                 st.metric("Average Duration", f"{df['trip_duration'].mean():.0f} min")

#             # visualizations
#             st.subheader("Tariff Distribution")
#             # TBD --> here should be stay charts and graphs

#         except Exception as e:
#             st.error(f"Error loading data: {str(e)}")

#     with tab3:
#         st.header("Real-Time Statistics")
#         # TBD --> here we could show updated statistics
#         st.write("Statistics in development...")

# def main():
#     """Main function of the application"""
#     set_page_config()
    
#     # Sidebar
#     date_range, passenger_count = sidebar_filters()
    
#     # Main content
#     main_content()
    
#     # Footer
#     st.markdown("---")
#     st.markdown("Developed for the NYC Taxi Prediction project")

# if __name__ == "__main__":
#     main()