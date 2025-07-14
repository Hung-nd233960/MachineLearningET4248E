from typing import Dict
import pandas as pd


def diagnosis_df(metadata: Dict) -> pd.DataFrame:
    """Convert metadata dictionary to a DataFrame."""
    # Initialize an empty dictionary to hold diagnoses
    diagnoses = {}

    for key, value in metadata.items():
        if ":" in key:
            rater, diagnosis = key.split(":", 1)
            diagnoses.setdefault(diagnosis, {})[rater] = value

    # Create DataFrame
    df = pd.DataFrame.from_dict(diagnoses, orient="index").fillna(0).astype(bool)

    # Optional: sort columns and index for nicer display
    df = df.sort_index().sort_index(axis=1)
    return df
