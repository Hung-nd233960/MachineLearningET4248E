import os
import pandas as pd

base_dir = "eda_public_data/data/"
records = []

for patient_id in os.listdir(base_dir):
    patient_path = os.path.join(base_dir, patient_id)
    if not os.path.isdir(patient_path):
        continue
    if not patient_id.startswith("CQ500-CT-"):
        continue

    # Each image set is a folder under the patient folder
    for image_set_id in os.listdir(patient_path):
        image_set_path = os.path.join(patient_path, image_set_id)
        if not os.path.isdir(image_set_path):
            continue

        # Count DICOM files (ending in .dcm)
        num_images = sum(
            1
            for f in os.listdir(image_set_path)
            if os.path.isfile(os.path.join(image_set_path, f))
            and f.lower().endswith(".dcm")
        )

        records.append(
            {
                "image_set_id": image_set_id,
                "patient_id": patient_id,
                "num_images": num_images,
            }
        )

# Convert to DataFrame and save to CSV
df = pd.DataFrame(records)
df.to_csv("image_sets_summary.csv", index=False)

print("Done. Saved to image_sets_summary.csv")
