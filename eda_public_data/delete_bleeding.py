import os
import pandas as pd
import shutil

# Path to CSV
csv_path = "eda_test/reads.csv"
base_dir = "eda_test/data/"

# Read CSV
df = pd.read_csv(csv_path)

# Identify bleeding-related columns
bleed_keywords = [
    "ICH",
    "IPH",
    "IVH",
    "SDH",
    "EDH",
    "SAH",
    "BleedLocation-Left",
    "BleedLocation-Right",
    "ChronicBleed",
]

bleed_columns = [col for col in df.columns if any(k in col for k in bleed_keywords)]

print("Bleeding columns detected:", bleed_columns)

# Find rows where any bleeding column == 1
bleed_rows = df[df[bleed_columns].eq(1).any(axis=1)]

# Delete corresponding folders in data/
for idx, row in bleed_rows.iterrows():
    folder_name = row["name"]
    folder_path = os.path.join(base_dir, folder_name)
    if os.path.isdir(folder_path):
        print(f"Deleting folder: {folder_path}")
        shutil.rmtree(folder_path)
    else:
        print(f"Folder not found: {folder_path}")

# Drop these rows from the dataframe
df = df.drop(bleed_rows.index)

# Save updated CSV (overwrite or to new file)
df.to_csv("annotations_filtered.csv", index=False)

print("Done. Updated CSV saved as annotations_filtered.csv")
