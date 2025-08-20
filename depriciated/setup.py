from sqlalchemy import create_engine
from utils.load_patients import (
    load_image_sets_from_csv,
    load_patients,
    load_images_from_filesystem,
)
from utils.db.models import Base


def init_db():
    """
    Initialize the database by creating all tables.
    """
    engine = create_engine("sqlite:///medfabric.sqlite3")
    Base.metadata.create_all(engine)
    print("🧱 All tables created if not exist.")


def setup_db():
    load_patients()
    print("✅ Patients loaded into database.")
    load_image_sets_from_csv("metadata/scan_metadata_backup.csv", "data/")
    print("✅ Image sets loaded into database.")
    load_images_from_filesystem()
    print("✅ Images loaded into database.")


if __name__ == "__main__":
    init_db()
    setup_db()
    print("✅ Database setup complete.")
