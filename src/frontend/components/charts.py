import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_fare_distribution(df: pd.DataFrame):
    """
    Create a histogram of the rate distribution
    """
    fig = px.histogram(
        df,
        x='fare_amount',
        nbins=50,
        title='Fare Distribution',
        labels={'fare_amount': 'Fare ($)', 'count': 'Frequency'}
    )
    return st.plotly_chart(fig)

def plot_trips_by_hour(df: pd.DataFrame):
    """
    Create a bar chart of trips per hour
    """
    # Asumiendo que existe una columna datetime, extraemos  la hora
    df['hour'] = pd.to_datetime(df['pickup_datetime']).dt.hour
    hourly_trips = df['hour'].value_counts().sort_index()
    
    fig = px.bar(
        x=hourly_trips.index,
        y=hourly_trips.values,
        title='Number of Trips per Hour',
        labels={'x': 'Hour of day', 'y': 'Number of trips'}
    )
    return st.plotly_chart(fig)

def plot_average_fare_by_distance(df: pd.DataFrame):
    """
    Create a scatter plot of rate vs distance
    """
    fig = px.scatter(
        df,
        x='trip_distance',
        y='fare_amount',
        title='Relationship between Distance and Rate',
        labels={'trip_distance': 'Distance (km)', 'fare_amount': 'Fare ($)'},
        trendline="ols"
    )
    return st.plotly_chart(fig)

def plot_prediction_comparison(actual, predicted, metric_name="Tarifa"):
    """
    Create a comparison graph between actual and predicted values
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(len(actual))),
        y=actual,
        name='Real Value',
        mode='lines'
    ))
    
    fig.add_trace(go.Scatter(
        x=list(range(len(predicted))),
        y=predicted,
        name='Prediction',
        mode='lines'
    ))
    
    fig.update_layout(
        title=f'Comparing {metric_name}: Actual vs Prediction',
        xaxis_title='Index',
        yaxis_title=metric_name
    )
    
    return st.plotly_chart(fig)

def create_metrics_dashboard(df: pd.DataFrame):
    """
    Create a dashboard with important metrics
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Average Fare",
            value=f"${df['fare_amount'].mean():.2f}",
            delta=f"{df['fare_amount'].std():.2f}"
        )
    
    with col2:
        st.metric(
            label="Average Distance",
            value=f"{df['trip_distance'].mean():.2f} km",
            delta=f"{df['trip_distance'].std():.2f}"
        )
    
    with col3:
        st.metric(
            label="Average Duration",
            value=f"{df['trip_duration'].mean():.0f} min",
            delta=f"{df['trip_duration'].std():.0f}"
        )