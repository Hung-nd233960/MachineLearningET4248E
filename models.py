# pylint: disable = too-few-public-methods, invalid-name, missing-module-docstring, missing-class-docstring, missing-function-docstring
import enum
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    Enum,
    ForeignKeyConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates

Base = declarative_base()


class Patient(Base):
    """
    Represents a patient and their initial diagnostic data from up to 3 raters.
    """

    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True)
    Category = Column(String, nullable=True)

    # Rater fields (bools). Assume they can be null if not all raters filled them.
    for r in [1, 2, 3]:
        for attr in [
            "ICH",
            "IPH",
            "IVH",
            "SDH",
            "EDH",
            "SAH",
            "BleedLocation-Left",
            "BleedLocation-Right",
            "ChronicBleed",
            "Fracture",
            "CalvarialFracture",
            "OtherFracture",
            "MassEffect",
            "MidlineShift",
        ]:
            locals()[f"R{r}:{attr}"] = Column(Boolean, nullable=True)


class ImageSet(Base):
    """
    Represents a unique CT scan session (image set) belonging to a patient.
    """

    __tablename__ = "image_sets"

    image_set_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    num_images = Column(Integer, nullable=False)
    folder_path = Column(String, nullable=False)
    conflicted = Column(Boolean, default=False, nullable=False)


class Image(Base):
    """
    Represents a single slice (image) in an image set.
    Composite key: (image_set_id, image_id)
    """

    __tablename__ = "images"

    image_id = Column(String, primary_key=True)  # e.g., "004.png"
    image_set_id = Column(
        String, ForeignKey("image_sets.image_set_id"), primary_key=True
    )
    slice_index = Column(Integer, nullable=False)


class Doctor(Base):
    """
    Represents a doctor (rater) in the system.
    """

    __tablename__ = "doctors"

    uuid = Column(String, primary_key=True)  # Can be upgraded to UUID type
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)  # Must be present


class Region(enum.Enum):
    None_ = "None"
    BasalGanglia = "BasalGanglia"
    CoronaRadiata = "CoronaRadiata"


class Evaluation(Base):
    """
    Represents a doctor's evaluation of a single image.
    Composite key: (doctor_id, image_set_id, image_id)
    """

    __tablename__ = "evaluations"

    doctor_id = Column(
        String, ForeignKey("doctors.uuid"), primary_key=True, nullable=False
    )
    image_id = Column(String, primary_key=True, nullable=False)
    image_set_id = Column(String, primary_key=True, nullable=False)

    region = Column(Enum(Region), nullable=False, default=Region.None_)
    basal_score = Column(Integer, nullable=True)
    corona_score = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(
            ["image_set_id", "image_id"], ["images.image_set_id", "images.image_id"]
        ),
    )

    @validates("basal_score", "corona_score", "region")
    def validate_scores(self, key, value):
        if key == "basal_score":
            if self.region == Region.BasalGanglia:
                if value is None or not 0 <= value <= 4:
                    raise ValueError("BasalGanglia score must be between 0 and 4.")
            else:
                if value is not None:
                    raise ValueError(
                        "Basal score must be null unless region is BasalGanglia."
                    )
        elif key == "corona_score":
            if self.region == Region.CoronaRadiata:
                if value is None or not 0 <= value <= 6:
                    raise ValueError("CoronaRadiata score must be between 0 and 6.")
            else:
                if value is not None:
                    raise ValueError(
                        "Corona score must be null unless region is CoronaRadiata."
                    )
        elif key == "region":
            if value is None:
                raise ValueError("Region cannot be None.")
        return value


class ConflictType(enum.Enum):
    Classification = "Classification"
    Score = "Score"
    Quality = "Quality"
    IrrelevantData = "IrrelevantData"


class Conflict(Base):
    """
    Represents a conflict found in evaluations:
    - Can be image-level (e.g. region/score disagreements)
    - Or image set-level (e.g. low_quality/irrelevant_data disagreement)
    """
    __tablename__ = "conflicts"

    conflict_id = Column(Integer, primary_key=True, autoincrement=True)

    image_id = Column(String, nullable=True)
    image_set_id = Column(String, nullable=False)

    type = Column(Enum(ConflictType), nullable=False)
    resolved = Column(Boolean, default=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["image_set_id", "image_id"],
            ["images.image_set_id", "images.image_id"],
            use_alter=True,
            name="fk_image_conflict",
        ),
    )

class ImageSetEvaluation(Base):
    """
    Doctor-specific evaluation of the entire image set.
    """
    __tablename__ = "image_set_evaluations"

    doctor_id = Column(String, ForeignKey("doctors.uuid"), primary_key=True)
    image_set_id = Column(String, ForeignKey("image_sets.image_set_id"), primary_key=True)

    is_low_quality = Column(Boolean, default=False, nullable=False)
    is_irrelevant = Column(Boolean, default=False, nullable=False)
