import pandas as pd
import re


# --- Helpers ---
def extract_patient_num(patient_id: str) -> int:
    """Extract numeric part from patient_id like CQ500-CT-123 → 123"""
    m = re.search(r"CQ500-CT-(\d+)", patient_id)
    return int(m.group(1)) if m else -1


def extract_slice_num(image_id: str) -> int:
    """Extract numeric part from DICOM filename like CT000123.dcm → 123"""
    m = re.search(r"CT(\d+)\.dcm", image_id, re.IGNORECASE)
    return int(m.group(1)) if m else -1


# --- 1. Sort image_sets_summary.csv ---
df_sets = pd.read_csv("eda_public_data/image_sets_summary.csv")
df_sets["patient_num"] = df_sets["patient_id"].apply(extract_patient_num)
df_sets = df_sets.sort_values(by=["patient_num", "image_set_id"]).drop(
    columns=["patient_num"]
)
df_sets.to_csv("image_sets_summary_sorted.csv", index=False)
print("✅ Saved sorted image_sets_summary_sorted.csv")

# --- 2. Sort images_summary.csv ---
df_images = pd.read_csv("eda_public_data/images_summary.csv")
df_images["patient_num"] = df_images["patient_id"].apply(extract_patient_num)
df_images["slice_num"] = df_images["image_id"].apply(extract_slice_num)

df_images = df_images.sort_values(by=["patient_num", "image_set_id", "slice_num"]).drop(
    columns=["patient_num", "slice_num"]
)

df_images.to_csv("images_summary_sorted.csv", index=False)
print("✅ Saved sorted images_summary_sorted.csv")
