import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class DataLoader:
    def __init__(self, data_path, output_path=None):
        self.data_path = data_path
        self.output_path = output_path

    def load_data(self):
        """Load the dataset from the specified path."""
        try:
            df = pd.read_parquet(self.data_path)
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to load data: {e}")

    def summarize_data(self, df):
        """Generate summary statistics and identify missing values, duplicates, and outliers."""
        summary_stats = df.describe(include="all").transpose()
        missing_values_report = df.isnull().sum().to_frame(name="missing_count")
        missing_values_report["missing_percentage"] = (
            missing_values_report["missing_count"] / len(df) * 100
        )
        duplicate_count = df.duplicated().sum()

        return summary_stats, missing_values_report, duplicate_count

    def preprocess(self):
        """Perform basic cleaning and save the preprocessed dataset."""
        pd.set_option("display.float_format", "{:.2f}".format)

        # Load the data
        original_df = self.load_data()
        df = original_df.copy()

        # Summarize the data
        summary_stats, missing_values_report, duplicate_count = self.summarize_data(df)

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

        # Save preprocessed data
        if self.output_path:
            df.to_parquet(self.output_path, index=False)

        return df, summary_stats, missing_values_report, duplicate_count

    def visualize_data(self, df):
        """Visualize distributions of all numeric columns in the dataset."""
        numeric_columns = df.select_dtypes(include=["number"]).columns
        for column in numeric_columns:
            sns.histplot(df[column], kde=True, bins=30)
            plt.title(f"Distribution of {column}")
            plt.xlabel(column)
            plt.ylabel("Frequency")
            plt.show()
