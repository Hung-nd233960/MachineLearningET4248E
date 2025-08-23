# pylint: disable = too-few-public-methods, invalid-name, missing-module-docstring, missing-class-docstring, missing-function-docstring
import enum
import uuid as uuid_lib
from datetime import datetime
from typing import Optional
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    String,
    Boolean,
    Integer,
    ForeignKey,
    Enum,
    DateTime,
    text,
    Identity,
    MetaData,
)
from sqlalchemy.orm import (
    validates,
    mapped_column,
    DeclarativeBase,
    Mapped,
)

metadata_obj = MetaData()


class Base(DeclarativeBase):
    pass


# --- Enums ---
class Region(enum.Enum):
    None_ = "None"
    BasalCentral = "BasalGangliaCentral"
    BasalCortex = "BasalGangliaCortex"
    CoronaRadiata = "CoronaRadiata"


class Gender(enum.Enum):
    Male = "Male"
    Female = "Female"
    Other = "Other"


class ConflictType(enum.Enum):
    Classification = "Classification"
    Score = "Score"
    Quality = "Quality"
    IrrelevantData = "IrrelevantData"


# --- Tables ---
class Patient(Base):
    """Represents a patient and their initial diagnostic data."""

    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(Enum(Gender), nullable=True)


class Doctors(Base):
    __tablename__ = "doctors"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4
    )
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    @validates("username")
    def validate_username(self, key, value):
        if key != "username":
            return value
        if not value or len(value) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        return value


class ImageSet(Base):
    """Represents a unique CT scan session (image set) belonging to a patient."""

    __tablename__ = "image_sets"

    index: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, cycle=False),  # auto-increment in PostgreSQL
        unique=True,
        nullable=False,
        index=True,
    )

    image_set_id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("patients.patient_id"), nullable=True
    )
    num_images: Mapped[int] = mapped_column(Integer, nullable=False)
    folder_path: Mapped[str] = mapped_column(String, nullable=False)
    conflicted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Image(Base):
    __tablename__ = "images"

    image_id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    image_set_id: Mapped[str] = mapped_column(
        String, ForeignKey("image_sets.image_set_id"), nullable=False
    )
    slice_index: Mapped[int] = mapped_column(Integer, nullable=False)


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4
    )
    doctor_id: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.uuid"), nullable=False
    )
    login_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ImageSetEvaluation(Base):
    __tablename__ = "image_set_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # <-- surrogate PK (recommended for flexibility)

    doctor_id: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    image_set_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("image_sets.image_set_id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )

    is_low_quality: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_irrelevant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "image_set_id", "session_id", name="uq_eval_triplet"
        ),
    )


class ImageEvaluation(Base):
    """Represents a doctor's evaluation of a single image."""

    __tablename__ = "image_evaluations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    doctor_id: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    image_id: Mapped[str] = mapped_column(
        String, ForeignKey("images.image_id"), nullable=False
    )
    session_id: Mapped[uuid_lib.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False
    )
    region: Mapped[Region] = mapped_column(
        Enum(Region), default=Region.None_, nullable=False
    )
    basal_score_central_left: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    basal_score_central_right: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    basal_score_cortex_left: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    basal_score_cortex_right: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    corona_score_left: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    corona_score_right: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("doctor_id", "image_id", "session_id", name="uq_image_eval"),
    )

    @validates("region")
    def validate_region(self, key, value):
        if value not in Region:
            raise ValueError(f"Invalid region: {value}. Must be one of {list(Region)}.")
        return value


# """
# class Conflict(Base):
#     """Represents a conflict found in evaluations."""
#
#     __tablename__ = "conflicts"
#
#     conflict_id: Mapped[int] = mapped_column(
#         Integer, primary_key=True, autoincrement=True
#     )
#     image_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
#     image_set_id: Mapped[str] = mapped_column(String, nullable=False)
#     conflict_type: Mapped[ConflictType] = mapped_column(
#         Enum(ConflictType), nullable=False
#     )
#     resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
#
#     __table_args__ = (
#         ForeignKeyConstraint(
#             ["image_set_id", "image_id"],
#             ["images.image_set_id", "images.image_id"],
#             use_alter=True,
#             name="fk_image_conflict",
#         ),
#     )
# """
