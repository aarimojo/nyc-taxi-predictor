# NYC Taxi Trip Predictor

A machine learning system that predicts taxi trip duration and costs in New York City using historical taxi trip data from the NYC Taxi & Limousine Commission.

## Features

- Data pipeline for processing NYC taxi trip records
- Machine learning models for predicting trip duration and cost
- REST API for real-time predictions
- Interactive Jupyter notebooks for data exploration
- Docker support for easy deployment

## Project Structure
```
nyc-taxi-predictor/
├── .gitignore
├── README.md
├── docker-compose.yml
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── predictions.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── prediction.py
│   └── services/
│   │   ├── __init__.py
│   │   └── zone_mapper.py
│   └── data/
│       └── nycneighborhoods_converted.geo.json
├── data/
│   ├── raw/
│   ├── processed/
│   ├── geojson_coordinates_procesing.py
│   ├── geojson_create_geojson_file.py
│   └── download_data.py
├── notebooks/
│   ├── 01_initial_data_exploration.ipynb
│   └── 02_feature_engineering.ipynb
└── src/
    └── frontend/
        ├── components/
        │   ├── __init__.py
        │   ├── charts.py
        │   └── maps.py
        ├── utils/
        │   ├── __init__.py
        │   ├── api.py
        │   ├── config.py
        │   └── logger.py
        ├── app.py
        ├── Dockerfile
        └── requirements.txt
```

## Data Source

This project uses the [NYC Taxi Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) provided by the NYC Taxi & Limousine Commission (TLC).

## Installation

### Local Installation

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Download the initial dataset:
```bash
python data/download_data.py
```

### Using Docker

There are two ways to use Docker with this project:

#### Option 1: VS Code Remote Containers

1. Install the "Remote Development" extension in VS Code
2. Open the project in VS Code
3. When prompted, click "Reopen in Container" or press F1 and select "Remote-Containers: Reopen in Container"
4. VS Code will build the container and set up the development environment

#### Option 2: Docker Compose

1. Start all services:
```bash
docker-compose up --build
```

2. Or start specific services:
```bash
# Run Jupyter Notebook
docker-compose up notebook

# Run the API
docker-compose up api

# Download data
docker-compose run data

# Download specific years
docker-compose run data --years 2023,2024
```

### Accessing Services

#### Jupyter Notebook
- URL: http://localhost:8888
- Token: taxi

#### API
- Main URL: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Development Workflow

When using Docker:
- All project files are mounted in the container
- Changes to files are immediately reflected
- Data downloaded through Docker is available in the `data/` directory
- Jupyter notebooks can be created and edited from the browser

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop a specific service
docker-compose stop notebook
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b new_function`)
3. Commit your changes (`git commit -m 'Add amazing feature with new function'`)
4. Push to the branch (`git push origin new_function`)
5. Open a Pull Request

