import pandas as pd
import os
import argparse
from pathlib import Path
from typing import Optional
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class DataLoader:
    def __init__(self, 
                 data_path: str, 
                 output_path: Optional[str] = None, 
                 year: Optional[str] = None, 
                 month: Optional[str] = None,
                 split_data: bool = False
    ):
        self.data_path = data_path
        self.output_path = output_path
        self.year = year
        self.month = month
        self.split_data = split_data
        self.taxi_type = "yellow"
        self.df = None
        self.key = os.getenv("key")
        self.host = os.getenv("host")
        # TODO: handle years based on available data
        self.years = ['2022', '2023', '2024']
        self.months = list(map(lambda x: str(x).zfill(2), list(range(1, 13))))

    def get_weather_data(self, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
        """
        Get daily weather data for the specified date range, either from cache or API.
        """
        
        # Create directory for cached weather data if it doesn't exist
        cache_dir = Path("data/weather_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"Using cache directory: {cache_dir}")

        # If processing specific month
        # TODO: handle years based on available data for year only query
        # TODO: handle months and years based on query params
        if self.month and not self.year:
            weather_df = pd.DataFrame()
            month = int(self.month)
            for year in self.years:
                print(f"Processing month: {year}-{month:02d}")
                start_date = pd.Timestamp(f"{year}-{month:02d}-01")
                end_date = start_date + pd.offsets.MonthEnd(0)

                # Create cache filename based on date range
                cache_file = cache_dir / f"weather_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                
                if cache_file.exists():
                    print(f"Loading weather data from cache: {cache_file}")
                    _weather_df = pd.read_csv(cache_file)
                    _weather_df['date'] = pd.to_datetime(_weather_df['date'])
                    weather_df = pd.concat([weather_df, _weather_df])
                else:
                    print(f"Fetching weather data from API for period {start_date.date()} to {end_date.date()}")
                    _weather_df = self.fetch_weather_data(
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    if not _weather_df.empty:
                        print(f"Saving weather data to cache: {cache_file}")
                        _weather_df.to_csv(cache_file, index=False)
                        weather_df = pd.concat([weather_df, _weather_df])
                    else:
                        raise ValueError(f"No weather data retrieved for period {start_date.date()} to {end_date.date()}")
        
        return self.preprocess_weather_data(weather_df)

    def fetch_weather_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch daily weather data from the API."""
        url = "https://meteostat.p.rapidapi.com/stations/daily"
        params = {
            "station": "KNYC0",  # Central Park Station
            "start": start_date,
            "end": end_date,
            "tz": "America/New_York"
        }
        headers = {
            "X-RapidAPI-Key": self.key,
            "X-RapidAPI-Host": self.host
        }
        
        print(f"Making API request for period {start_date} to {end_date}")
        print(f"API URL: {url}")
        print(f"API params: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"API response status: {response.status_code}")
            
            if response.ok and 'data' in response.json():
                df = pd.DataFrame(response.json()['data'])
                print(f"Retrieved data shape: {df.shape}")
                return df
            else:
                print(f"API request failed: {response.text}")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching weather data: {str(e)}")
            return pd.DataFrame()

    def preprocess_weather_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and process weather data."""
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Fill missing values
        df['snow'] = df['snow'].fillna(0)
        df['prcp'] = df['prcp'].fillna(0)  # precipitation
        df['tavg'] = df['tavg'].fillna(df[['tmin', 'tmax']].mean(axis=1))  # average temperature
        df['wspd'] = df['wspd'].fillna(df['wspd'].mean())  # wind speed
        
        return df

    def load_data(self) -> pd.DataFrame:
        """Load the dataset from the specified path and filter by month if specified."""
        try:
            data_path = Path(self.data_path)
            print(f"Loading data from {data_path}")
            
            if data_path.is_dir():
                if self.year and self.month:
                    pattern = f"yellow_tripdata_{self.year}-{int(self.month):02d}.parquet"
                elif self.year:
                    pattern = f"yellow_tripdata_{self.year}*.parquet"
                elif self.month:
                    pattern = f"yellow_tripdata_*-{int(self.month):02d}.parquet"
                else:
                    pattern = "*.parquet"
                print(f"Pattern: {pattern}")
                files = list(data_path.glob(pattern))
                print(f"Found {len(files)} files matching {pattern}, names: {files}")
                if not files:
                    raise FileNotFoundError(f"No matching files found for {pattern}")
                print(f"Loading {pattern}")
                self.df = pd.read_parquet(files[0])
            else:
                self.df = pd.read_parquet(data_path)
            
            print(f"Loaded dataset with shape: {self.df.shape}")
            return self.df
        except Exception as e:
            raise RuntimeError(f"Failed to load data: {e}")
    
    def remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove additional outliers from the dataset."""
        # Remove trips with extreme fares unless justified by trip distance
        df = df[(df["fare_amount"] <= 500) | (df["trip_distance"] > 50)]
        
        # Remove extremely long trips unless justified by fare
        df = df[df["trip_duration"] < 180]  # Cap at 3 hours
        
        # Remove trips with zero distance but high fare
        df = df[~((df["trip_distance"] == 0) & (df["fare_amount"] > 10))]
        
        # Ensure valid NYC taxi zones
        valid_zone_ids = range(1, 264)
        df = df[df["PULocationID"].isin(valid_zone_ids) & df["DOLocationID"].isin(valid_zone_ids)]
        
        # Remove trips outside NYC airport zones
        df = df[(df["DOLocationID"] != 264) & (df["DOLocationID"] != 265)]
        df = df[(df["PULocationID"] != 264) & (df["PULocationID"] != 265)]
        
        # Apply percentile-based filtering for extreme values
        fare_cap = df["fare_amount"].quantile(0.995)
        total_amount_cap = df["total_amount"].quantile(0.995)
        distance_cap = 50  # Further restrict max trip distance
        
        df = df[df["fare_amount"] <= fare_cap]
        df = df[df["total_amount"] <= total_amount_cap]
        df = df[df["trip_distance"] <= distance_cap]
        
        # Remove trips where trip_distance < 1 mile but fare_amount > 50
        df = df[~((df["trip_distance"] < 1) & (df["fare_amount"] > 50))]
        
        # Remove trips where trip_distance > 20 miles but trip_duration < 10 minutes
        df = df[~((df["trip_distance"] > 20) & (df["trip_duration"] < 10))]
        
        return df
    
    def _calculate_trip_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        df["trip_duration"] = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60
        return df[df["trip_duration"] > 0]
    
    def _add_day_of_week(self, df: pd.DataFrame) -> pd.DataFrame:
        df["day_of_week_pu"] = df["tpep_pickup_datetime"].dt.dayofweek
        df["day_of_week_do"] = df["tpep_dropoff_datetime"].dt.dayofweek
        return df
    
    def _add_hour_of_day(self, df: pd.DataFrame) -> pd.DataFrame:
        df["hour_of_day_pu"] = df["tpep_pickup_datetime"].dt.hour
        df["hour_of_day_do"] = df["tpep_dropoff_datetime"].dt.hour
        return df
    
    def _grouped_by_time_of_day(self, df: pd.DataFrame) -> pd.DataFrame:
        df["time_of_day_pu"] = df["hour_of_day_pu"].apply(lambda x: "morning" if 6 <= x < 12 else "afternoon" if 12 <= x < 18 else "evening" if 18 <= x < 21 else "night")
        df["time_of_day_do"] = df["hour_of_day_do"].apply(lambda x: "morning" if 6 <= x < 12 else "afternoon" if 12 <= x < 18 else "evening" if 18 <= x < 21 else "night")
        return df
    
    def _drop_extra_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.drop(columns=["LocationID_pu", "LocationID_do"], errors='ignore')
    
    def join_vs_taxi_zones(self, df: pd.DataFrame) -> pd.DataFrame:
        taxi_zones = pd.read_csv("data/taxi_zones.csv")
        df = df.merge(taxi_zones, left_on="PULocationID", right_on="LocationID", how="left")
        df = df.merge(taxi_zones, left_on="DOLocationID", right_on="LocationID", how="left", suffixes=("_pu", "_do"))
        return df

    def preprocess(self) -> pd.DataFrame:
        """Perform basic cleaning, outlier removal, and save the preprocessed dataset."""
        
        # Load the data
        original_df = self.load_data()
        df = original_df.copy()
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = df.dropna()
        
        # Ensure datetime columns exist before computing trip duration
        if "tpep_pickup_datetime" in df.columns and "tpep_dropoff_datetime" in df.columns:
            df["trip_duration"] = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60
            df = df[df["trip_duration"] > 0]  # Remove invalid durations

        # Remove negative fare amounts and total amounts
        df = df[df["fare_amount"] >= 0]
        df = df[df["total_amount"] >= 0]
        
        # Remove outliers
        df = self.remove_outliers(df)
        df = self.join_vs_taxi_zones(df)
        df = self._add_day_of_week(df)
        df = self._add_hour_of_day(df)
        df = self._grouped_by_time_of_day(df)
        df = self._drop_extra_columns(df)

        start_date = df['tpep_pickup_datetime'].min()
        end_date = df['tpep_pickup_datetime'].max()
        weather_df = self.get_weather_data(pd.Timestamp(start_date), pd.Timestamp(end_date))
        
        df['join_date'] = df['tpep_pickup_datetime'].dt.strftime('%Y-%m-%d')
        weather_df['join_date'] = weather_df['date'].dt.strftime('%Y-%m-%d')

        df = pd.merge(
            df,
            weather_df,
            on='join_date',
            how='left'
        )
        
        # Drop temporary columns
        df = df.drop(['join_date', 'wpgt', 'tsun', 'date'], axis=1)

        df = self._drop_dates_no_weather_data(df)
        
        # Save preprocessed data
        self.save_processed_data(df)

        print(f"Preprocessed data shape: {df.shape}")
        return df
    
    def _drop_dates_no_weather_data(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f"Size before drops: {df.shape}")
        df = df[df['tavg'].notna()]
        print(f"Size after tavg: {df.shape}")
        df = df[df['tmin'].notna()]
        print(f"Size after tmin: {df.shape}")
        df = df[df['tmax'].notna()]
        print(f"Size after tmax: {df.shape}")
        df = df[df['prcp'].notna()]
        print(f"Size after prcp: {df.shape}")
        df = df[df['snow'].notna()]
        print(f"Size after snow: {df.shape}")
        df = df[df['wdir'].notna()]
        print(f"Size after wdir: {df.shape}")
        df = df[df['wspd'].notna()]
        print(f"Size after wspd: {df.shape}")
        #df = df[df['wpgt'].notna()]
        #print(f"Size after wpgt: {df.shape}")
        df = df[df['pres'].notna()]
        print(f"Size after pres: {df.shape}")
        # df = df[df['tsun'].notna()]
        # print(f"Size after tsun: {df.shape}")
        return df
    
    def save_processed_data(self, df: pd.DataFrame) -> None:
        output_path = Path(self.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        base_filename = f"{self.taxi_type}_processed"
        if self.year:
            base_filename += f"_{self.year}"
        if self.month:
            base_filename += f"_{int(self.month):02d}"
        output_file = output_path / f"{base_filename}.parquet"
        df.to_parquet(output_file, index=False)
        print(f"Saved processed dataset to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process NYC Taxi Trip data')
    default_data_path = str(Path(os.getcwd()) / 'data' / 'raw')
    default_output_path = str(Path(os.getcwd()) / 'data' / 'processed')
    parser.add_argument('--data-path', type=str, default=default_data_path, help=f'Path to the data directory or file (default: {default_data_path})')
    parser.add_argument('--output-path', type=str, default=default_output_path, help=f'Path to save processed data (default: {default_output_path})')
    parser.add_argument('--year', type=str, default=None, help='Year to process (e.g., 2022)')
    parser.add_argument('--month', type=str, default=None, help='Month to process (e.g., 01)')
    parser.add_argument('--split-data', action='store_true', help='Split data into train/test/val sets')
    parser.add_argument('--no-split-data', action='store_false', dest='split_data', help='Do not split data into train/test/val sets')

    args = parser.parse_args()
    print(f"Processing data from {args.data_path} to {args.output_path}, year: {args.year}, month: {args.month}, split_data: {args.split_data}")
    output_path = Path(args.output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    data_loader = DataLoader(data_path=args.data_path, output_path=str(output_path), year=args.year, month=args.month, split_data=args.split_data)
    data_loader.preprocess()
    print("Data processing completed successfully")
