import pandas as pd
from typing import Optional, Tuple
from pathlib import Path
import argparse

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
        self.df = None

    def load_data(self) -> pd.DataFrame:
        """Load the dataset from the specified path."""
        try:
            data_path = Path(self.data_path)
            
            # If data_path is a directory, find matching files
            if data_path.is_dir():
                pattern = f"*_{self.year}-*.parquet" if self.year else f"*-{self.month}.parquet" if self.month else "*.parquet"
                files = list(data_path.glob(pattern))

                if not files:
                    raise FileNotFoundError(f"No matching files found for pattern: {pattern}")
                
                print(f"Found {len(files)} matching files: {[f.name for f in files]}")

                dfs = []
                for file in files:
                    try:
                        df = pd.read_parquet(file)
                        dfs.append(df)
                    except Exception as e:
                        print(f"Error reading file {file}: {str(e)}")
                
                if not dfs:
                    raise RuntimeError("No data could be loaded from matching files")
                
                self.df = pd.concat(dfs, ignore_index=True)
                
            else:
                # If data_path is a file, read it directly
                self.df = pd.read_parquet(data_path)
            
            print(f"Loaded dataset with shape: {self.df.shape}")
            return self.df
            
        except Exception as e:
            raise RuntimeError(f"Failed to load data: {e}")

    def preprocess(self) -> pd.DataFrame:
        """Perform basic cleaning and save the preprocessed dataset."""
        pd.set_option("display.float_format", "{:.2f}".format)

        # Load the data
        original_df = self.load_data()
        df = original_df.copy()

        # Remove duplicates
        df = df.drop_duplicates()

        # Handle missing values
        if "fare_amount" in df.columns and "trip_distance" in df.columns:
            df = df.dropna(subset=["fare_amount", "trip_distance"])

        # Additional preprocessing
        if "pickup_datetime" in df.columns and "dropoff_datetime" in df.columns:
            df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
            df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], errors="coerce")

            # Drop rows with invalid datetime conversions
            df.dropna(subset=["pickup_datetime", "dropoff_datetime"], inplace=True)

            # Calculate trip duration in minutes
            df["trip_duration"] = (
                df["dropoff_datetime"] - df["pickup_datetime"]
            ).dt.total_seconds() / 60
            df = df[df["trip_duration"] > 0]  # Remove invalid durations

        if "passenger_count" in df.columns:
            df = df[df["passenger_count"] <= 4]  # Keep only trips with passenger count <= 4
        if "MTA_tax" in df.columns:
            df = df[(df["MTA_tax"] >= 0) & (df["MTA_tax"] <= 0.50)]  # MTA_tax between 0 and 0.50
        if "improvement_surcharge" in df.columns:
            df = df[df["improvement_surcharge"] > 0 & (df["improvement_surcharge"] <= 0.30)] # Fixed value found in documentation
        if "extra" in df.columns:
            df = df[(df["extra"] > 0) & (df["extra"] < 1)]  # Extra surcharge between 0 and 1 (exclusive)
        if "airport_fee" in df.columns:
            df = df[(df["airport_fee"] > 0)]
        if "tolls_amount" in df.columns:
            df = df[(df["tolls_amount"] >= 0) & (df["tolls_amount"] <= 10)]  # Keep only valid tolls_amount values
        if "RateCodeID" in df.columns:
            df = df[(df["RateCodeID"] >= 0) & (df["RateCodeID"] <= 6)]  # Keep only valid RateCodeID values
        if "Fare_amount" in df.columns:
            df = df[(df["Fare_amount"] > 0)]

        df = self.remove_bad_date_data(df)
        df = self._calculate_trip_duration(df)
        df = self.remove_bad_trip_duration(df)
        df = self.remove_bad_trip_distance(df)
        df = self.join_vs_taxi_zones(df)

        # Save preprocessed data
        if self.output_path:
            if self.split_data:
                paths = ['train', 'test', 'val']
                for path in paths:
                    df.sample(frac=0.33).to_parquet(f"{self.output_path}/{path}.parquet", index=False)
            else:
                df.to_parquet(self.output_path, index=False)

    def _calculate_trip_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trip duration in minutes."""
        df["trip_duration"] = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60
        return df

    def remove_bad_date_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove data with invalid date.""" 
        df = df[df["tpep_pickup_datetime"] < df["tpep_dropoff_datetime"]]
        return df
    
    def remove_bad_trip_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove data with invalid trip duration."""
        df = df[df["trip_duration"] > 0]
        df = df[df["trip_duration"] < 120]
        return df
    
    def remove_bad_trip_distance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove data with invalid trip distance."""
        df = df[df["trip_distance"] > 0]
        df = df[df["trip_distance"] <= 7]
        return df

    def join_vs_taxi_zones(self, df: pd.DataFrame) -> pd.DataFrame:
        """Join the dataset with the taxi zones dataset."""
        taxi_zones = pd.read_csv("data/taxi_zones.csv")
        df = df.merge(taxi_zones, left_on="PULocationID", right_on="LocationID", how="left", suffixes=("_pu", "_pu_zone"))
        df = df.merge(taxi_zones, left_on="DOLocationID", right_on="LocationID", how="left", suffixes=("_do", "_do_zone"))
        return df
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process NYC Taxi Trip data')
    parser.add_argument('--data-path', type=str, default='data/raw/',
                       help='Path to the data directory or file (default: data/raw/)')
    parser.add_argument('--output-path', type=str, default='data/processed/',
                       help='Path to save processed data (default: data/processed/)')
    parser.add_argument('--year', type=str, default=None,
                       help='Year to process (e.g., 2022)')
    parser.add_argument('--month', type=str, default=None,
                       help='Month to process (e.g., 01)')
    parser.add_argument('--split-data', action='store_true', default=True,
                       help='Split data into train/test/val sets')
    
    args = parser.parse_args()

    if args.year is None and args.month is None:
        while True:
            response = input('\nWARNING: No year or month specified. This will process ALL available data and may require significant memory.\nDo you want to continue? (yes/no): ').lower().strip()
            if response.lower() in ['yes', 'y']:
                print("Proceeding with full data processing...")
                break
            elif response.lower() in ['no', 'n']:
                print("Operation cancelled by user.")
                exit(0)
            else:
                print("Please answer 'yes' or 'no'")
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize and run data loader
    print(f"Starting data processing with parameters: {vars(args)}")
    try:
        data_loader = DataLoader(
            data_path=args.data_path,
            output_path=str(output_path),
            year=args.year,
            month=args.month,
            split_data=args.split_data
        )
        data_loader.preprocess()
        print("Data processing completed successfully")
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        raise