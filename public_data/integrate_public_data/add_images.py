import pandas as pd
from medfabric.db.database import Session
from medfabric.api.image_set_input import get_image_set_by_id_and_patient
from medfabric.api.image_input import add_image
from medfabric.api.errors import ImageAlreadyExistsError

# Read CSV
df = pd.read_csv("public_data/eda_public_data/images_summary_sorted.csv")

with Session() as session:
    for _, row in df.iterrows():
        image_id = row["image_id"]
        image_set_id = row["image_set_id"]
        patient_id = row["patient_id"]
        slice_index = int(row["slice_index"])

        try:
            image_set_uuid = get_image_set_by_id_and_patient(
                session=session,
                image_set_id=image_set_id,
                patient_id=patient_id,
            )
            if image_set_uuid is None:
                print(
                    f"❌ Error adding {image_id}: Image set {image_set_id} for patient {patient_id} not found"
                )
                continue
            add_image(
                session=session,
                image_id=image_id,
                image_set_uuid=image_set_uuid,
                slice_index=slice_index,
            )
            print(
                f"✅ Added {image_id} (set {image_set_id}, patient {patient_id}, slice {slice_index})"
            )
        except ImageAlreadyExistsError:
            print(f"⚠️ Skipped {image_id}, already exists")
        except Exception as e:
            print(f"❌ Error adding {image_id}: {e}")
            session.rollback()
