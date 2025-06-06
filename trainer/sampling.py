from sklearn.utils import resample
import pandas as pd

def oversample_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    max_count = df['label'].value_counts().max()
    return pd.concat([
        resample(df[df['label'] == label], replace=True, n_samples=max_count, random_state=42)
        for label in df['label'].unique()
    ])

def undersample_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    min_count = df['label'].value_counts().min()
    return pd.concat([
        resample(df[df['label'] == label], replace=True, n_samples=min_count, random_state=42)
        for label in df['label'].unique()
    ])
