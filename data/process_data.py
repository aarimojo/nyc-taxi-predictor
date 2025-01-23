import pandas as pd
from typing import Optional, Tuple
from pathlib import Path
import argparse
import os

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

    def save_processed_data(self, df: pd.DataFrame) -> None:
        """Save the processed data to parquet file(s)."""
        if not self.output_path:
            return

        # Create output directory if it doesn't exist
        output_path = Path(self.output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Construct base filename
        base_filename = f"{self.taxi_type}_processed"
        if self.year:
            base_filename += f"_{self.year}"
        if self.month:
            base_filename += f"_{int(self.month):02d}"

        if self.split_data:
            # Split into train (70%), validation (15%), and test (15%)
            train_df = df.sample(frac=0.7, random_state=42)
            remaining_df = df.drop(train_df.index)
            val_df = remaining_df.sample(frac=0.5, random_state=42)
            test_df = remaining_df.drop(val_df.index)

            # Save split datasets
            train_df.to_parquet(output_path / f"{base_filename}_train.parquet", index=False)
            val_df.to_parquet(output_path / f"{base_filename}_val.parquet", index=False)
            test_df.to_parquet(output_path / f"{base_filename}_test.parquet", index=False)
            
            print(f"Saved split datasets to {output_path}")
        else:
            # Save single dataset
            output_file = output_path / f"{base_filename}.parquet"
            df.to_parquet(output_file, index=False)
            print(f"Saved processed dataset to {output_file}")

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
            print("Processing pickup and dropoff datetimes")
            df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
            df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], errors="coerce")

            # Drop rows with invalid datetime conversions
            df.dropna(subset=["pickup_datetime", "dropoff_datetime"], inplace=True)

            # Calculate trip duration in minutes
            df["trip_duration"] = (
                df["dropoff_datetime"] - df["pickup_datetime"]
            ).dt.total_seconds() / 60
            df = df[df["trip_duration"] > 0]  # Remove invalid durations

        print("Removing bad date data")
        df = self.remove_bad_date_data(df)
        print("Calculating trip duration")
        df = self._calculate_trip_duration(df)
        print("Removing bad trip duration")
        df = self.remove_bad_trip_duration(df)
        print("Removing bad trip distance")
        df = self.remove_bad_trip_distance(df)
        print("Joining with taxi zones")
        df = self.join_vs_taxi_zones(df)
        print("Adding day of week")
        df = self._add_day_of_week(df)
        print("Adding hour of day")
        df = self._add_hour_of_day(df)
        print("Grouping by time of day")
        df = self._grouped_by_time_of_day(df)


        #finally
        print("Dropping extra columns")
        df = self._drop_extra_columns(df)

        # Save preprocessed data
        self.save_processed_data(df)

    def _add_day_of_week(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add day of week to the dataset."""
        df["day_of_week_pu"] = df["tpep_pickup_datetime"].dt.dayofweek
        df["day_of_week_do"] = df["tpep_dropoff_datetime"].dt.dayofweek
        return df
    
    def _add_hour_of_day(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add hour of day to the dataset."""
        df["hour_of_day_pu"] = df["tpep_pickup_datetime"].dt.hour
        df["hour_of_day_do"] = df["tpep_dropoff_datetime"].dt.hour
        return df
    
    def _grouped_by_time_of_day(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group the dataset by time of day."""
        df["time_of_day_pu"] = df["hour_of_day_pu"].apply(lambda x: "morning" if 6 <= x < 12 else "afternoon" if 12 <= x < 18 else "evening" if 18 <= x < 21 else "night")
        df["time_of_day_do"] = df["hour_of_day_do"].apply(lambda x: "morning" if 6 <= x < 12 else "afternoon" if 12 <= x < 18 else "evening" if 18 <= x < 21 else "night")
        return df

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
        df = df[df["trip_distance"] < 100]
        return df
    
    def remove_bad_fare_amount(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove data with invalid fare amount."""
        df = df[df["fare_amount"] > 0]
        df = df[df["fare_amount"] < 1000]
        return df
    
    def remove_trips_outside_nyc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove data with trips outside NYC."""
        df = df[df["DOLocationID"] != 264]
        df = df[df["DOLocationID"] != 265]
        df = df[df["PULocationID"] != 264]
        df = df[df["PULocationID"] != 265]
        return df

    def join_vs_taxi_zones(self, df: pd.DataFrame) -> pd.DataFrame:
        """Join the dataset with the taxi zones dataset."""
        taxi_zones = pd.read_csv("data/taxi_zones.csv")
        df = df.merge(taxi_zones, left_on="PULocationID", right_on="LocationID", how="left")
        df = df.merge(taxi_zones, left_on="DOLocationID", right_on="LocationID", how="left", suffixes=("_pu", "_do"))
        return df
    
    def _drop_extra_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop extra columns."""
        df = df.drop(columns=["LocationID_pu", "LocationID_do"])
        return df
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process NYC Taxi Trip data')

    default_data_path = str(Path(os.getcwd()) / 'data' / 'raw')
    default_output_path = str(Path(os.getcwd()) / 'data' / 'processed')
    
    parser.add_argument('--data-path', type=str, default=default_data_path,
                       help=f'Path to the data directory or file (default: {default_data_path})')
    parser.add_argument('--output-path', type=str, default=default_output_path,
                       help=f'Path to save processed data (default: {default_output_path})')
    parser.add_argument('--year', type=str, default=None,
                       help='Year to process (e.g., 2022)')
    parser.add_argument('--month', type=str, default=None,
                       help='Month to process (e.g., 01)')
    parser.add_argument('--split-data', action='store_true',
                       help='Split data into train/test/val sets')
    parser.add_argument('--no-split-data', action='store_false', dest='split_data',
                       help='Do not split data into train/test/val sets')
    
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