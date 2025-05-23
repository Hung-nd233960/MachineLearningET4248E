import os
import re
import shutil
from collections import defaultdict


def delete_bone_ct_folders(root_dir):
    # Regex pattern to match folders containing "bone" (case-insensitive)
    pattern = re.compile(r"bone", re.IGNORECASE)

    # Walk through the directory
    for dirpath, dirnames, _ in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            if pattern.search(dirname):
                folder_path = os.path.join(dirpath, dirname)
                print(f"Deleting: {folder_path}")
                shutil.rmtree(folder_path)  # Remove the entire folder


def explore_ct_data(folder_path):
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder not found: {folder_path}")
        return

    patient_count = 0
    ct_type_counts = defaultdict(int)

    # Navigate through qctXX folders (01 to 19)
    for qct in range(1, 20):
        qct_folder = os.path.join(folder_path, f"qct{qct:02d}")
        if not os.path.exists(qct_folder):
            continue

        # Look for patient folders with format "CQ500CTyy CQ500CTyy"
        patient_folders = [
            f
            for f in os.listdir(qct_folder)
            if os.path.isdir(os.path.join(qct_folder, f))
            and re.match(r"^CQ500CT\d{2,3} CQ500CT\d{2,3}$", f)
        ]
        patient_count += len(patient_folders)

        for patient in patient_folders:
            patient_path = os.path.join(qct_folder, patient, "Unknown Study")
            if not os.path.exists(patient_path):
                print(f"[WARNING] 'Unknown Study' not found for patient: {patient}")
                continue

            ct_types = [
                f
                for f in os.listdir(patient_path)
                if os.path.isdir(os.path.join(patient_path, f))
            ]

            for ct_type in ct_types:
                ct_type_counts[ct_type] += 1

    print(f"Total patients found: {patient_count}\n")
    print("Unique CT types and their counts:")
    for ct_type, count in ct_type_counts.items():
        print(f"  - {ct_type}: {count}")

    print("\nExploration Complete!")


# Example usage:
folder_path = "archive"  # Update with the correct path
delete_bone_ct_folders(folder_path)
explore_ct_data(folder_path)
