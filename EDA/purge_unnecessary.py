import pandas as pd
import os
import shutil

# Read the CSV file
df = pd.read_csv("cleaned_dataset.csv")
archive_path = "archive"
# Extract the first column (assuming it's named or indexed as 0)
column_data = df.iloc[:, 0]

# Convert the values to strings and process to remove dashes
formatted_data = column_data.astype(str).apply(lambda x: x.replace("-", ""))

# Create the list with "CQ500CTxxx CQ500CTxxx" format
allowlist_formatted_data = [data + " " + data for data in formatted_data]


# Print the result
print(allowlist_formatted_data)

for root, dirs, files in os.walk(archive_path, topdown=False):
    for dir_name in dirs:
        # Check if the folder name is in the whitelist
        folder_path = os.path.join(root, dir_name)

        if dir_name in allowlist_formatted_data:
            print(f"Skipping whitelisted folder: {folder_path}")
            continue
        if "CQ500CT" in dir_name:
            try:
                # Delete the folder if it's not in the whitelist
                shutil.rmtree(folder_path)
                print(f"Deleted folder: {folder_path}")
            except Exception as e:
                print(f"Error deleting {folder_path}: {e}")
