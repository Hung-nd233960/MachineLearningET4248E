# pylint: disable = missing-module-docstring
import os
from collections import defaultdict
import pandas as pd


def database_formation(csv_file: str, export_csv=True):
    """
    This function reads a CSV file containing image paths, extracts relevant parts,
    and counts the number of images for each (patient, scan_type) pair.
    It then creates a DataFrame and optionally exports it to a CSV file.
    """

    # Check if the CSV file exists
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file {csv_file} does not exist.")

    df = pd.read_csv(csv_file, header=None)
# Read the CSV file

    image_paths = df[0].tolist()  # Assume first column has image paths

    # Extract relevant parts
    records = []
    for path in image_paths:
        try:
            normalized_path = path.replace("\\", "/")  # Normalize slashes
            parts = normalized_path.strip().split("/")
            patient_id = parts[1]  # e.g., CQ500-CT-042
            scan_type = parts[2]  # e.g., "type_of_ct_scan"
            key = (patient_id, scan_type)
            records.append(key)
        except IndexError:
            print(f"Skipping malformed path: {path}")


    # Count the number of images for each (patient, scan_type)

    counter = defaultdict(int)
    for record in records:
        counter[record] += 1

    # Create DataFrame from the counter
    data = []
    for (patient_id, scan_type), count in counter.items():
        data.append({
            "scan_type": scan_type,
            "patient_id": patient_id,
            "num_images": count,
        })

    df_out = pd.DataFrame(data, columns=[
        "scan_type",
        "patient_id",
        "num_images",
    ])

    # Optionally export to CSV
    if export_csv:
        df_out.to_csv("ct_scans.csv", index=False)
        print("CSV exported successfully.")

    print(df_out.head())



if __name__ == "__main__":
    CSV_FILE = "metadata/image_metadata.csv"  # Replace with your actual file
    database_formation(CSV_FILE)

