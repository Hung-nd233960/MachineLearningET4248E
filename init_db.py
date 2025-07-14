from models import (
    Base,
    Patient,
    ImageSet,
    Image,
    Doctor,
    Evaluation,
    Conflict,
    ImageSetEvaluation
)
from sqlalchemy import create_engine

engine = create_engine("sqlite:///medfabric.sqlite3")
Base.metadata.create_all(engine)
print("🧱 All tables created if not exist.")
