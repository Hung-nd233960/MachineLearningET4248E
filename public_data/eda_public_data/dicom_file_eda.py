import os
import re
import pandas as pd

base_dir = "eda_public_data/data/"
records = []

# Regex to extract slice index from file name like CT123456.dcm
slice_pattern = re.compile(r"CT(\d+)\.dcm$", re.IGNORECASE)

for patient_id in os.listdir(base_dir):
    patient_path = os.path.join(base_dir, patient_id)
    if not os.path.isdir(patient_path):
        continue
    if not patient_id.startswith("CQ500-CT-"):
        continue

    for image_set_id in os.listdir(patient_path):
        image_set_path = os.path.join(patient_path, image_set_id)
        if not os.path.isdir(image_set_path):
            continue

        for image_id in os.listdir(image_set_path):
            image_path = os.path.join(image_set_path, image_id)
            if not os.path.isfile(image_path):
                continue
            if not image_id.lower().endswith(".dcm"):
                continue

            m = slice_pattern.match(image_id)
            if not m:
                print(f"⚠️ Skipping unexpected filename: {image_id}")
                continue

            slice_index = int(m.group(1))

            records.append(
                {
                    "image_id": image_id,
                    "image_set_id": image_set_id,
                    "patient_id": patient_id,
                    "slice_index": slice_index,
                }
            )

# Save to CSV
df = pd.DataFrame(records)
df.to_csv("images_summary.csv", index=False)

print("Done. Saved to images_summary.csv")
