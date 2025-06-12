import os
from typing import Optional
import re
import pandas as pd

from utils.credential_manager import CredentialManager
from utils.reconciliate import reconcilate


def choose_test_data(
    scan_metadata: pd.DataFrame, sample_number: int = 5, mode: str = "least_chosen"
) -> pd.DataFrame:
    """
    Choose a set of training data based on the specified mode.

    Args:
        scan_metadata (pd.DataFrame): DataFrame containing scan metadata.
        number (int): Number of training sets to choose.
        mode (str): Mode for choosing the training data. Options are "least_chosen" or "random".

    Returns:
        pd.Dataframe: List of chosen training entries as pandas DataFrame.
    """
    df = scan_metadata.copy()

    if mode == "least_chosen":
        df_filtered = df[
            (~df["true_irrelevance"].astype(bool))
            & (~df["true_disquality"].astype(bool))
        ]
        df["num_ratings"] = pd.to_numeric(df["num_ratings"], errors="coerce")
        df_filtered = df  # Not filtering here, as we want to consider all scans
        return df.head(sample_number)  # true sample number of least chosen

    if mode == "random":
        return df.sample(n=sample_number)

    raise ValueError("Invalid mode. Choose 'least_chosen' or 'random'.")


def choose_annotation_data(
    scan_metadata: pd.DataFrame, sample_number: int = 5, mode: str = "least_chosen"
) -> pd.DataFrame:
    """
    Choose a set of annotation data based on the specified mode.

    Args:
        scan_metadata (pd.DataFrame): DataFrame containing scan metadata.
        number (int): Number of annotation sets to choose.
        mode (str): Mode for choosing the annotation data. Options are "least_chosen" or "random".

    Returns:
        pd.Dataframe: List of chosen annotation entries as pandas DataFrame.
    """
    df = scan_metadata.copy()

    if mode == "least_chosen" or mode == "override":
        df_filtered = df[
            (~df["true_irrelevance"].astype(bool))
            & (~df["true_disquality"].astype(bool))
        ]
        df["num_ratings"] = pd.to_numeric(df["num_ratings"], errors="coerce")
        df_filtered = df
        df_sorted = df_filtered.sort_values(by="num_ratings", ascending=True)
        df_unique = df_sorted.drop_duplicates(subset=["patient_id"], keep="first")
        return df_unique.head(sample_number)  # true sample number of least chosen

    if mode == "random":
        return df.sample(n=sample_number)

    if mode == "verify":
        # Step 1: Filter for relevant and qualified scans
        base_filter = (~df["true_irrelevance"].astype(bool)) & (
            ~df["true_disquality"].astype(bool)
        )

        # Step 2: Identify all columns annotated by labelers
        labeler_columns = [col for col in df.columns if col.endswith("_labeler")]

        # Step 3: Find rows where at least one labeler has annotated
        labeler_annotated_mask = df[labeler_columns].notnull().any(axis=1)

        # Step 4: Combine both filters
        df_filtered = df[base_filter & labeler_annotated_mask]
        df_sorted = df_filtered.sort_values(by="num_ratings", ascending=True)
        df_unique = df_sorted.drop_duplicates(subset=["patient_id"], keep="first")
        return df_filtered.sample(n=sample_number)

    raise ValueError("Invalid mode. Choose 'least_chosen' or 'random'.")


def choose_train_data(scan_metadata: pd.DataFrame, mode: str = ""):
    """
    Choose a set of training data based on the specified mode.

    Args:
        scan_metadata (pd.DataFrame): DataFrame containing scan metadata.
        mode (str): Mode for choosing the training data. Options are now not developed yet.

    Returns:
        pd.Dataframe: List of chosen training entries as pandas DataFrame.
    """
    df = scan_metadata.copy()
    df["num_ratings"] = pd.to_numeric(df["num_ratings"], errors="coerce")

    # Step 1: Remove irrelevant and disqualified scans
    df_filtered = df[
        (~df["true_irrelevance"].astype(bool)) & (~df["true_disquality"].astype(bool))
    ]

    # Step 2: Keep only rows with at least one rating
    df_filtered = df_filtered[df_filtered["num_ratings"] > 0]

    # Step 3: Require at least one labeler opinion
    labeler_columns = [col for col in df_filtered.columns if col.endswith("_labeler")]
    labeler_mask = df_filtered[labeler_columns].notnull().any(axis=1)
    df_filtered = df_filtered[labeler_mask]

    return df_filtered


def train_data_prepare(
    data_path: str, chosen_data: pd.DataFrame, csv_export: bool = True
) -> pd.DataFrame:
    """
    Prepare the training data by extracting image paths and labels.

    Args:
        chosen_data (pd.DataFrame): DataFrame containing chosen training data.

    Returns:
        pd.DataFrame: A DataFrame with columns ['path', 'label'] for training.
    """

    image_label_pairs = []
    for _, row in chosen_data.iterrows():
        pid = str(row["patient_id"])
        scan_type = str(row["scan_type"])
        folder = os.path.join(data_path, pid, scan_type)
        try:
            images = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith((".png"))
            ]
            images = sorted(images)

            basel_opinions = [
                int(row[col]) - 1
                for col in row.index
                if col.startswith("opinion_basel_")
                and pd.notna(row[col])
                and col.endswith("_verifier")
            ]

            thal_opinions = [
                int(row[col]) - 1
                for col in row.index
                if col.startswith("opinion_corona_")
                and pd.notna(row[col])
                and col.endswith("_verifier")
            ]
            ### WARNING: MAY IMPLEMENT A NEW FUNCTION TO RECONCILATE
            idx_basel = reconcilate(basel_opinions)
            idx_thal = reconcilate(thal_opinions)

            for i, img_path in enumerate(images):
                if i == idx_basel:
                    label = "BasalGanglia"
                elif i == idx_thal:
                    label = "CoronaRadiata"
                else:
                    label = "None"
                image_label_pairs.append((img_path, label))
        except Exception as e:
            print(f"Skipping {folder} due to error: {e}")

        # Save the image-label pairs to a CSV file
        df = pd.DataFrame(image_label_pairs, columns=["path", "label"])
        if csv_export:
            df.to_csv("train.csv", index=False)

    return df


def test_data_prepare(
    data_path: str, chosen_data: pd.DataFrame, csv_export: bool = True
) -> pd.DataFrame:
    """
    Prepare the test data by extracting image paths for all chosen entries.

    Args:
        data_path (str): Root directory containing patient folders.
        chosen_data (pd.DataFrame): DataFrame of selected scan metadata.
        csv_export (bool): Whether to export the result to a CSV.

    Returns:
        pd.DataFrame: DataFrame with column ['path'] containing all test image paths.
    """
    image_paths = []

    for _, row in chosen_data.iterrows():
        pid = str(row["patient_id"])
        scan_type = str(row["scan_type"])
        folder = os.path.join(data_path, pid, scan_type)

        try:
            images = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(".png")
            ]
            images = sorted(images)
            image_paths.extend(images)
        except Exception as e:
            print(f"Skipping {folder} due to error: {e}")

    df = pd.DataFrame(image_paths, columns=["path"])

    if csv_export:
        df.to_csv("test_images.csv", index=False)

    return df


def extract_labeler_opinions_from_row(
    row: pd.Series, cm: CredentialManager
) -> Optional[pd.DataFrame]:
    """
    Extracts all non-empty labeler opinions from a single row of scan metadata and organizes them
    into a summary DataFrame with one row per doctor (labeler).

    Parameters:
    ----------
    row : pd.Series
        A single row from the scan metadata DataFrame, containing opinion columns like
        'opinion_basel_<uuid>_labeler', 'opinion_corona_<uuid>_labeler', etc.

    cm : object
        An object that has a method `get_username(uuid: str) -> str`,
        which maps doctor UUIDs to usernames.

    Returns:
    -------
    pd.DataFrame or None
        A DataFrame with one row per doctor, and columns:
            - Username
            - IrrelevantOpinion
            - IrrelevanceOpinion
            - BasalOpinion
            - CoronaOpinion
        If there are no valid (non-null) labeler opinions in the row, returns None.
    """
    # Step 1: Find all keys in the row that end with "_labeler"
    labeler_keys = [k for k in row.index if k.endswith("_labeler")]

    # If there are no labeler-related columns at all, exit early
    if not labeler_keys:
        return None

    doctor_data = {}  # Dictionary to hold opinions grouped by username

    for key in labeler_keys:
        # Match the column name pattern: opinion_<type>_<uuid>_labeler
        match = re.match(r"opinion_(\w+?)_(.+?)_labeler$", key)
        if not match:
            continue  # Skip malformed keys that don't match expected format

        opinion_type, uuid = match.groups()
        value = row[key]

        # Skip empty values (None, NaN, or empty string)
        if pd.isna(value) or value in ("", None):
            continue

        # Get doctor username from UUID
        username = cm.get_username_by_id(uuid)

        # Create a new entry for the doctor if not already present
        if username not in doctor_data:
            doctor_data[username] = {}

        # Convert opinion type to a readable and consistent column name
        readable_key = {
            "irrelevance": "IrrelevanceOpinion",
            "disquality": "DisqualityOpinion",
            "basel": "BasalOpinion",
            "corona": "CoronaOpinion",
        }.get(opinion_type, opinion_type.capitalize() + "Opinion")

        # Store the opinion value under the readable column name
        doctor_data[username][readable_key] = value

    # If no valid opinions were found, return None
    if not doctor_data:
        return None

    # Convert the collected doctor data to a DataFrame
    return pd.DataFrame.from_dict(doctor_data, orient="index").reset_index(
        names="Username"
    )


if __name__ == "__main__":
    # Example usage
    data_path = "data"
    scan_metadata = pd.read_csv("metadata/scan_metadata.csv")
    chosen_data = choose_test_data(scan_metadata, sample_number=5, mode="least_chosen")
    print(chosen_data)
    chosen_data = test_data_prepare(data_path, chosen_data, csv_export=True)
    print(chosen_data)
