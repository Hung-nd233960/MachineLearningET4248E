# pylint: disable = redefined-outer-name
"""Provide functions to manipulate CT_scan metadata DataFrame."""
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
    Adds or overrides opinion columns for a specific doctor in the DataFrame.

    This function ensures that the following columns are present for the given doctor ID,
    and sets all of their values to 0. If any of these columns already exist in the DataFrame,
    they will be overwritten with zeros.

    Parameters:
        df (pd.DataFrame): The DataFrame to modify.
        doctor_id (str): The identifier of the doctor (e.g., '1', '2', 'A').

    Returns:
        pd.DataFrame: The updated DataFrame with doctor-specific opinion columns reset to 0.

    Columns affected:
        - opinion_basel_doctor{doctor_id}
        - opinion_corona_doctor{doctor_id}
        - opinion_irrelevance_doctor{doctor_id}
        - opinion_quality_doctor{doctor_id}
    """
    df[f"opinion_basel_doctor{doctor_id}"] = 0
    df[f"opinion_corona_doctor{doctor_id}"] = 0
    df[f"opinion_irrelevance_doctor{doctor_id}"] = 0
    df[f"opinion_quality_doctor{doctor_id}"] = 0
    return df

def null_doctor_columns_adder(df: pd.DataFrame, doctor_id: str) -> pd.DataFrame:
    """
    Adds or overrides opinion columns for a specific doctor in the DataFrame with NaN values.

    This function ensures that the following columns are present for the given doctor ID,
    and sets all of their values to NaN. If any of these columns already exist in the DataFrame,
    they will be overwritten with NaN.

    Parameters:
        df (pd.DataFrame): The DataFrame to modify.
        doctor_id (str): The identifier of the doctor (e.g., '1', '2', 'A').

    Returns:
        pd.DataFrame: The updated DataFrame with doctor-specific opinion columns set to NaN.

    Columns affected:
        - opinion_basel_doctor{doctor_id}
        - opinion_corona_doctor{doctor_id}
        - opinion_irrelevance_doctor{doctor_id}
        - opinion_quality_doctor{doctor_id}
    """
    df[f"opinion_basel_doctor{doctor_id}"] = pd.NA
    df[f"opinion_corona_doctor{doctor_id}"] = pd.NA
    df[f"opinion_irrelevance_doctor{doctor_id}"] = pd.NA
    df[f"opinion_quality_doctor{doctor_id}"] = pd.NA
    df["num_ratings"] -= 1
    return df

def undo_doctor_columns(df: pd.DataFrame, doctor_id: str) -> pd.DataFrame:
    """
    Sets to NaN all opinion columns associated with a given doctor ID (UUID), regardless of role.

    If any of these columns in a row had a non-null value, 'num_ratings' is decremented by 1 for that row.

    Parameters:
        df (pd.DataFrame): The DataFrame to modify.
        doctor_id (str): The UUID of the doctor (e.g., '1234', 'user_abc').

    Returns:
        pd.DataFrame: The updated DataFrame with UUID-specific opinion columns set to NaN.
    """
    target_cols = [col for col in df.columns if f"_{doctor_id}_" in col and col.startswith("opinion_")]

    if not target_cols:
        return df

    # Build a mask: rows where ANY of the doctor's columns are non-null
    any_not_na = df[target_cols].notna().any(axis=1)

    # Decrement num_ratings once per such row
    df.loc[any_not_na, "num_ratings"] -= 1

    # Set all the target columns to NaN
    df[target_cols] = pd.NA

    return df

if __name__ == "__main__":
    # Example usage
    df = pd.read_csv("metadata/scan_metadata.csv")
    df = add_static_columns(df)
    print(df.head())
    df.to_csv("metadata/scan_metadata.csv", index=False)
