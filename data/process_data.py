import pandas as pd
import os
import argparse
from pathlib import Path
from typing import Optional

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
        """Load the dataset from the specified path and filter by month if specified."""
        try:
            data_path = Path(self.data_path)
            
            if data_path.is_dir():
                if self.year and self.month:
                    pattern = f"yellow_tripdata_{self.year}-{int(self.month):02d}.parquet"
                else:
                    pattern = "*.parquet"
                
                files = list(data_path.glob(pattern))
                
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
        
        # Save preprocessed data
        self.save_processed_data(df)
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