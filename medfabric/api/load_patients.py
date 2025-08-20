import os
import pandas as pd
from sqlalchemy.orm import Session
from utils.db.database import engine
from utils.db.models import ImageSet, Image


def load_patients(engine_=engine):
    # Load your CSV
    df = pd.read_csv("metadata/patient_metadata.csv")

    # Convert Yes/No, 0/1, TRUE/FALSE → Boolean
    df.replace(
        {"Yes": True, "No": False, "TRUE": True, "FALSE": False, 1: True, 0: False},
        inplace=True,
    )

    # Save to DB using pandas
    df.to_sql("patients", con=engine_, if_exists="replace", index=False)


def load_image_sets_from_csv(csv_path: str, data_path: str, engine_=engine) -> None:
    """
    Load image sets from a CSV file and insert them into the database.

    Args:
        csv_path (str): Path to the CSV file.
        data_path (str): Base folder path for images.
        engine_: SQLAlchemy engine object.
    """
    df = pd.read_csv(csv_path)

    # Generate folder paths and add conflicted column
    df["folder_path"] = df.apply(
        lambda row: f"{data_path.rstrip('/')}/{row['patient_id']}/{row['scan_type']}",
        axis=1,
    )
    df["conflicted"] = False  # default value

    with Session(engine_) as session:
        for _, row in df.iterrows():
            image_set = ImageSet(
                image_set_id=row["scan_type"],
                patient_id=row["patient_id"],
                num_images=row["num_images"],
                folder_path=row["folder_path"],
                conflicted=row["conflicted"],
            )
            session.add(image_set)
        session.commit()
    print("✅ Loaded image sets into database.")


def load_images_from_filesystem(engine_=engine) -> None:
    """
    Scan folders based on image_sets table and populate the images table.
    """
    with Session(engine_) as session:
        image_sets = session.query(ImageSet).all()

        for image_set in image_sets:
            folder = image_set.folder_path
            if not os.path.isdir(folder):
                print(f"⚠️ Skipping missing folder: {folder}")
                continue

            # Get sorted PNG files
            png_files = sorted(
                [f for f in os.listdir(folder) if f.lower().endswith(".png")]
            )

            for index, filename in enumerate(png_files):
                img = Image(
                    image_id=filename,
                    image_set_id=image_set.image_set_id,
                    slice_index=index,
                )
                session.add(img)

        session.commit()

    print("✅ Loaded images into database.")
