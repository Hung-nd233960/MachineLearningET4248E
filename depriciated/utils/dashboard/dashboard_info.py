from typing import Tuple
import pandas as pd


def dashboard_info(df: pd.DataFrame, uuid: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate summary DataFrames for the dashboard.

    Each DataFrame includes 'scan_type', 'patient_id', 'num_images'.
    The second DataFrame (remaining) includes two extra columns:
    - 'Labeled By Others': True if any other labeler's set of columns is not NaN.
    - 'Verified By Others': True if any other verifier's set of columns is not NaN.

    Args:
        df (pd.DataFrame): Full DataFrame with opinions and metadata.
        uuid (str): The UUID of the current user.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            - First: Self-labeled rows
            - Second: Remaining rows with added columns
    """

    def is_fully_labeled(row: pd.Series, columns: list[str]) -> bool:
        """Return True if all specified columns in a row are non-null."""
        return bool(columns) and row[columns].notna().all()

    # Step 1: Get current UUID columns
    uuid_columns = [col for col in df.columns if uuid in col]
    print(f"UUID columns found: {uuid_columns}")
    # Exclude rows where "true_irrelevance" or "true_disquality" are non-zero
    exclude_mask = (
        df.get("true_irrelevance", pd.Series(False, index=df.index)).astype(bool)
    ) | (df.get("true_disquality", pd.Series(False, index=df.index)).astype(bool))

    df = df[~exclude_mask].copy()
    print(f"Rows after excluding true_irrelevance or true_disquality: {len(df)}")
    if not uuid_columns:
        print(f"No columns found for UUID: {uuid}")
        labeled_mask = pd.Series([False] * len(df), index=df.index)
        self_labeled_df = pd.DataFrame()
    else:
        labeled_mask = df[uuid_columns].notna().all(axis=1)
        self_labeled_df = df[labeled_mask].copy()

    remaining_df = df[~labeled_mask].copy()
    print(f"Remaining rows after excluding self-labeled: {len(remaining_df)}")
    # Step 2: Identify all labeler and verifier columns
    labeler_cols = [col for col in df.columns if "_labeler" in col]
    verifier_cols = [col for col in df.columns if "_verifier" in col]

    other_labeler_uuids = set(
        col.split("_")[-2] for col in labeler_cols if uuid not in col
    )

    other_verifier_uuids = set(
        col.split("_")[-2] for col in verifier_cols if uuid not in col
    )

    # Step 3: Annotate remaining rows
    def labeled_by_others(row):
        for other_uuid in other_labeler_uuids:
            cols = [col for col in labeler_cols if other_uuid in col]
            if is_fully_labeled(row, cols):
                return True
        return False

    def verified_by_others(row):
        for other_uuid in other_verifier_uuids:
            cols = [col for col in verifier_cols if other_uuid in col]
            if is_fully_labeled(row, cols):
                return True
        return False

    remaining_df["Labeled By Others"] = remaining_df.apply(labeled_by_others, axis=1)
    remaining_df["Verified By Others"] = remaining_df.apply(verified_by_others, axis=1)

    # Step 4: Final formatting
    rename_dict = {
        "scan_type": "Scan Type",
        "patient_id": "Patient ID",
        "num_images": "Number of Images",
        "num_ratings": "Number of Ratings",
    }
    self_labeled_df.rename(columns=rename_dict, inplace=True)
    remaining_df.rename(columns=rename_dict, inplace=True)
    remaining_df.reset_index(drop=True, inplace=True)

    for col in ["true_irrelevance", "true_disquality"]:
        self_labeled_df.drop(columns=col, inplace=True, errors="ignore")
        remaining_df.drop(columns=col, inplace=True, errors="ignore")

    remaining_df["Verify"] = False
    return self_labeled_df, remaining_df
