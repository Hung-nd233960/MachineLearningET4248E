import os
from typing import List
import pandas as pd

from utils.reconciliate import reconcilate

def choose_test_data(scan_metadata: pd.DataFrame,
                     sample_number: int = 5,
                     mode: str = "least_chosen") -> pd.DataFrame:
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
        df_filtered = df[(~df["true_irrelevance"].astype(bool)) &
                         (~df["true_disquality"].astype(bool))]
        df['num_ratings'] = pd.to_numeric(df['num_ratings'], errors='coerce')
        df_filtered = df # Not filtering here, as we want to consider all scans
        return df.head(sample_number) # true sample number of least chosen

    if mode == "random":
        return df.sample(n=sample_number)
  
    raise ValueError("Invalid mode. Choose 'least_chosen' or 'random'.")

def choose_annotation_data(scan_metadata: pd.DataFrame,
                      sample_number: int = 5,
                      mode: str = "least_chosen") -> pd.DataFrame:
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

    if mode == "least_chosen":
        df_filtered = df[(~df["true_irrelevance"].astype(bool)) &
                         (~df["true_disquality"].astype(bool))]
        df['num_ratings'] = pd.to_numeric(df['num_ratings'], errors='coerce')
        df_filtered = df
        df_sorted = df_filtered.sort_values(by='num_ratings', ascending=True)
        df_unique = df_sorted.drop_duplicates(subset=['patient_id'], keep='first')
        return df_unique.head(sample_number) # true sample number of least chosen

    if mode == "random":
        return df.sample(n=sample_number)
    
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

    df_filtered = df[(~df["true_irrelevance"].astype(bool)) &
                        (~df["true_disquality"].astype(bool))]
    df['num_ratings'] = pd.to_numeric(df['num_ratings'], errors='coerce')
    df_filtered = df[df['num_ratings'] > 0]
    return df_filtered

def train_data_prepare(data_path: str, chosen_data: pd.DataFrame, 
                       csv_export: bool = True) -> pd.DataFrame:
    """
    Prepare the training data by extracting image paths and labels.
    
    Args:
        chosen_data (pd.DataFrame): DataFrame containing chosen training data.
    
    Returns:
        pd.DataFrame: A DataFrame with columns ['path', 'label'] for training.
    """

    image_label_pairs = []
    for _, row in chosen_data.iterrows():
        pid = str(row['patient_id'])
        scan_type = str(row['scan_type'])
        folder = os.path.join(data_path, pid, scan_type)
        try:
            images = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(('.png'))
            ]
            images = sorted(images)

            basel_opinions = [int(row[col]) - 1 for col in row.index 
                  if col.startswith("opinion_basel_doctor") and pd.notna(row[col])]

            thal_opinions = [int(row[col]) - 1 for col in row.index 
                 if col.startswith("opinion_thalamus_doctor") and pd.notna(row[col])]
            ### WARNING: MAY IMPLEMENT A NEW FUNCTION TO RECONCILATE
            idx_basel = reconcilate(basel_opinions)
            idx_thal = reconcilate(thal_opinions)

            for i, img_path in enumerate(images):
                if i == idx_basel:
                    label = 'BasalGanglia'
                elif i == idx_thal:
                    label = 'Thalamus'
                else:
                    label = 'None'
                image_label_pairs.append((img_path, label))
        except Exception as e:
            print(f"Skipping {folder} due to error: {e}")

        # Save the image-label pairs to a CSV file
        df = pd.DataFrame(image_label_pairs, columns=['path', 'label'])
        if csv_export:
            df.to_csv('train.csv', index=False)

    return df

def test_data_prepare(data_path: str, chosen_data: pd.DataFrame, 
                      csv_export: bool = True) -> pd.DataFrame:
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
        pid = str(row['patient_id'])
        scan_type = str(row['scan_type'])
        folder = os.path.join(data_path, pid, scan_type)

        try:
            images = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith('.png')
            ]
            images = sorted(images)
            image_paths.extend(images)
        except Exception as e:
            print(f"Skipping {folder} due to error: {e}")

    df = pd.DataFrame(image_paths, columns=['path'])

    if csv_export:
        df.to_csv('test_images.csv', index=False)

    return df


if __name__ == "__main__":
    # Example usage
    data_path = "data"
    scan_metadata = pd.read_csv("metadata/scan_metadata.csv")
    chosen_data = choose_test_data(scan_metadata, sample_number=5, mode="least_chosen")
    print(chosen_data)
    chosen_data = test_data_prepare(data_path, chosen_data, csv_export=True)
    print(chosen_data)