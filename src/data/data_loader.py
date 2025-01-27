import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

"""
Data loading 
"""

class DataLoader:
    def __init__(self, data_path, output_path=None):
        self.data_path = data_path
        self.output_path = output_path

    def load_data(self):
        """Load the dataset from the specified path."""
        try:
            df = pd.read_parquet(self.data_path)
            return df.copy()
        except Exception as e:
            raise RuntimeError(f"Failed to load data: {e}")