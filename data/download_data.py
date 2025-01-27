import os
import requests
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import argparse

# Create data directories if they don't exist
RAW_DATA_DIR = Path('./data/raw')
PROCESSED_DATA_DIR = Path('./data/processed')
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Base URL for the NYC taxi data
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

def download_file(url, output_path):
    """Download a file from a URL to the specified path."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as file, tqdm(
        desc=output_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)

def download_taxi_data(year, month, taxi_type='yellow'):
    """Download taxi data for a specific year, month, and type."""
    filename = f"{taxi_type}_tripdata_{year}-{month:02d}.parquet"
    url = f"{BASE_URL}/{filename}"
    output_path = RAW_DATA_DIR / filename
    
    if not output_path.exists():
        try:
            download_file(url, output_path)
            return True
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return False
    return False

def main():
    parser = argparse.ArgumentParser(description='Download NYC Taxi Trip data')
    parser.add_argument('--years', type=str, default='2022,2023,2024',
                       help='Comma-separated list of years to download (default: 2022,2023,2024)')
    parser.add_argument('--taxi-type', type=str, default='yellow',
                       help='Type of taxi data to download (default: yellow)')
    args = parser.parse_args()

    # Parse years from command line
    years = [int(year.strip()) for year in args.years.split(',')]
    
    months = range(1, 13)
    
    print(f"Downloading {args.taxi_type} taxi data for years: {years}...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for year in years:
            for month in months:
                futures.append(
                    executor.submit(download_taxi_data, year, month, args.taxi_type)
                )
        
        for future in concurrent.futures.as_completed(futures):
            future.result()

if __name__ == "__main__":
    main() 