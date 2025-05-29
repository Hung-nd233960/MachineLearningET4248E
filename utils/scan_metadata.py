# pylint: disable = redefined-outer-name
""" Provide functions to manipulate CT_scan metadata DataFrame."""
import pandas as pd

def add_static_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds static columns to the DataFrame.
    """
    df["num_ratings"] = 0
    df["true_irrelevance"] = 0
    df["true_disquality"] = 0
    return df

def more_doctor_columns_adder(df: pd.DataFrame, doctor_id: str) -> pd.DataFrame:
    """
    Adds more doctor opinion columns to the DataFrame.
    """
    df[f"opinion_basel_doctor{doctor_id}"] = 0
    df[f"opinion_thalamus_doctor{doctor_id}"] = 0
    df[f"opinion_irrelevance_doctor{doctor_id}"] = 0
    df[f"opinion_quality_doctor{doctor_id}"] = 0

    return df

if __name__ == "__main__":
    # Example usage
    df = pd.read_csv("metadata/scan_metadata.csv")
    df = add_static_columns(df)
    print(df.head())
    df.to_csv("metadata/scan_metadata.csv", index=False)

