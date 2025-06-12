"""
Basic Columns
name → Identifier for each CT scan (e.g., CQ500-CT-427).
Category → Case category (B1 or B2, likely indicating severity or presence of pathology).

Radiologist Annotations (R1, R2, R3)
Each feature is labeled by three radiologists (R1, R2, R3). The values are binary (0 or 1):
1 → The radiologist observed the condition.
0 → The radiologist did not observe the condition.

Hemorrhage-related Annotations
R#:ICH → Intracranial hemorrhage (any bleeding inside the skull).
R#:IPH → Intraparenchymal hemorrhage (bleeding within the brain tissue).
R#:IVH → Intraventricular hemorrhage (bleeding into the brain's ventricles).
R#:SDH → Subdural hematoma (bleeding under the dura mater).
R#:EDH → Epidural hematoma (bleeding between the skull and dura mater).
R#:SAH → Subarachnoid hemorrhage (bleeding into the space around the brain).

Bleed Location
R#:BleedLocation-Left → Bleed found in the left hemisphere.
R#:BleedLocation-Right → Bleed found in the right hemisphere.
R#:ChronicBleed → Indicates whether the bleed is chronic (long-standing).

Fracture-related Annotations
R#:Fracture → Presence of any fracture.
R#:CalvarialFracture → Fracture in the calvaria (the dome-like upper skull).
R#:OtherFracture → Other types of fractures in the skull.

Mass Effect & Midline Shift
R#:MassEffect → Signs of mass effect, where swelling or bleeding displaces brain structures.
R#:MidlineShift → Whether the brain's midline is shifted,
                  which indicates severe trauma or pressure.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Reading data and initial exploration
df = pd.read_csv("archive/reads.csv")
print(df.head())  # First few rows
print(df.info())  # Column types
print(df.isnull().sum())  # Missing values
print(df.describe())  # Summary statistics
print(df.columns)  # Column names
# There are no missing values in the dataset.

df.drop(columns=["name"], inplace=True)
# Convert categorical 'Category' column to numerical
df["Category"] = df["Category"].map({"B1": 0, "B2": 1})

# There are columns of R1, R2, R3, it stands for doctors 1, 2, 3 opinions.
# We will compute the average score and majority vote for each condition.
# Extracting condition names from the columns
condition_names = set(col[3:] for col in df.columns if col.startswith("R1:"))
# Compute average scores (soft consensus)
for condition in condition_names:
    df[f"{condition}_Avg"] = df[
        [f"R1:{condition}", f"R2:{condition}", f"R3:{condition}"]
    ].mean(axis=1)
# Compute majority vote (binary decision)
for condition in condition_names:
    df[f"{condition}_Majority"] = (
        df[[f"R1:{condition}", f"R2:{condition}", f"R3:{condition}"]].sum(axis=1) >= 2
    ).astype(int)
# Drop original R1, R2, R3 columns
df.drop(
    columns=[
        col
        for col in df.columns
        if col.startswith("R1:") or col.startswith("R2:") or col.startswith("R3:")
    ],
    inplace=True,
)

df.hist(figsize=(12, 8), bins=20, edgecolor="black")
plt.suptitle("Histograms of Numeric Columns", fontsize=16)
plt.show()


# Compute correlation matrix

# Select only columns that end with "Avg" and include "Category"
selected_columns = ["Category"] + [col for col in df.columns if col.endswith("Avg")]
df_avg = df[selected_columns].corr()

# Plot heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(df_avg.corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.title("Heatmap of Averaged Radiologist Annotations")
plt.show()

# Since the scope of the project is predicting ischemic stroke, we will delete the columns related to hemorrhage.

df = pd.read_csv("archive/reads.csv")
df["Category"] = df["Category"].map({"B1": 0, "B2": 1})

bleeding_columns = [
    "R1:ICH",
    "R1:IPH",
    "R1:IVH",
    "R1:SDH",
    "R1:EDH",
    "R1:SAH",
    "R2:ICH",
    "R2:IPH",
    "R2:IVH",
    "R2:SDH",
    "R2:EDH",
    "R2:SAH",
    "R3:ICH",
    "R3:IPH",
    "R3:IVH",
    "R3:SDH",
    "R3:EDH",
    "R3:SAH",
]

# Filter out rows where any of the bleeding columns have a value of 1
df_cleaned = df[~df[bleeding_columns].eq(1).any(axis=1)]

print(df_cleaned.head())  # First few rows

df_cleaned.to_csv("patient_metadata.csv", index=False)
