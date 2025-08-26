import pandas as pd
from medfabric.db.database import Session
from medfabric.api.image_set_input import add_image_set
from medfabric.api.errors import ImageSetAlreadyExistsError

# Read CSV
df = pd.read_csv("public_data/eda_public_data/image_sets_summary_sorted.csv")

# Open DB session
with Session() as session:
    for _, row in df.iterrows():
        image_set_id = row["image_set_id"]
        patient_id = row["patient_id"]
        num_images = int(row["num_images"])

        try:
            add_image_set(
                session=session,
                image_set_id=image_set_id,
                patient_id=patient_id,
                num_images=num_images,
            )
            print(
                f"✅ Added {image_set_id} (patient {patient_id}, {num_images} images)"
            )
        except ImageSetAlreadyExistsError:
            print(f"⚠️ Skipped {image_set_id}, already exists")
        except Exception as e:
            print(f"❌ Error adding {image_set_id}: {e}")
