import os
import pandas as pd


def count_dicoms_in_subfolders(root_folder: str, output_csv: str):
    """
    Count DICOM (.dcm) files in each subfolder and save results to CSV.

    Args:
        root_folder (str): Path to the root folder containing subfolders of DICOMs.
        output_csv (str): Path to save the CSV file.
    """
    results = []

    # Iterate through subfolders
    for subfolder in os.listdir(root_folder):
        subfolder_path = os.path.join(root_folder, subfolder)
        if os.path.isdir(subfolder_path):
            dcm_count = sum(
                1 for f in os.listdir(subfolder_path) if f.lower().endswith(".dcm")
            )
            results.append({"folder": subfolder, "num_dcm_files": dcm_count})

    # Save to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved results to {output_csv}")
    return df


if __name__ == "__main__":
    root = "ct_data/"  # change this!
    output = "eda_private/results/dcm_file_count.csv"  # CSV file to save
    df = count_dicoms_in_subfolders(root, output)
    print(df)
