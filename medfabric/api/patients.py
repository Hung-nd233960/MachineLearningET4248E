# pylint: disable=missing-function-docstring,missing-module-docstring
# medfabric/api/patients.py
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from medfabric.db.models import Patient, Gender
from medfabric.api.errors import (
    PatientAlreadyExistsError,
    PatientInvalidDataError,
    DatabaseError,
)


def check_patient_exists(session: Session, patient_id: str) -> bool:
    """
    Check if a patient with the given ID exists.

    Args:
        session (Session): SQLAlchemy DB session
        patient_id (str): ID of the patient to check

    Returns:
        True if exists, False otherwise
    """
    return session.query(Patient).filter_by(patient_id=patient_id).count() > 0


def add_patient(
    session: Session,
    patient_id: str,
    category: Optional[str] = None,
    age: Optional[int] = None,
    gender: Optional[Gender] = None,
) -> Patient:
    """
    Add a new patient to the database.

    Args:
        session (Session): SQLAlchemy DB session.
        patient_id (str): Unique ID for the patient.
        category (Optional[str]): Category of the patient.
        age (Optional[int]): Age of the patient.
        gender (Optional[Gender]): Gender of the patient.
    Returns:
        Patient: The created patient object.
    """
    if not patient_id:
        raise PatientInvalidDataError("Patient ID cannot be empty.")
    if check_patient_exists(session, patient_id):
        raise PatientAlreadyExistsError(f"Patient with ID {patient_id} already exists.")

    patient = Patient(patient_id=patient_id, category=category, age=age, gender=gender)
    try:
        session.add(patient)
        session.commit()
        return patient
    except SQLAlchemyError as exc:
        session.rollback()
        raise DatabaseError(f"Failed to add patient: {exc}") from exc


def get_patient(session: Session, patient_id: str) -> Optional[Patient]:
    """
    Retrieve a patient by their ID.

    Args:
        session (Session): SQLAlchemy DB session
        patient_id (str): ID of the patient to retrieve

    Returns:
        Patient if found, None otherwise
    """
    return session.query(Patient).filter_by(patient_id=patient_id).one_or_none()
