import pandas as pd
from medfabric.db.database import Session
from medfabric.api.patients import (
    add_patient,
    PatientInvalidDataError,
    PatientAlreadyExistsError,
)

# Read CSV
df = pd.read_csv("public_data/eda_public_data/annotations_filtered.csv")

# Get first column
first_col = df.iloc[:, 0]

# Print values
patient_id_list = first_col.tolist()

for patient_id in patient_id_list:
    with Session() as session:
        try:
            add_patient(session, patient_id=str(patient_id))
            print(f"Added patient with ID: {patient_id}")
        except PatientAlreadyExistsError:
            print(f"Patient with ID {patient_id} already exists. Skipping.")
        except PatientInvalidDataError as e:
            print(f"Invalid data for patient ID {patient_id}: {e}. Skipping.")
        except Exception as e:
            print(f"Error adding patient ID {patient_id}: {e}. Skipping.")
