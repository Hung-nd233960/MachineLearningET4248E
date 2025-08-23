# pylint: disable=missing-module-docstring, missing-class-docstring, missing-function-docstring
# tests/patient_test.py
import pytest
from sqlalchemy.orm import Session
from medfabric.api.patients import add_patient, check_patient_exists
from medfabric.api.errors import (
    PatientAlreadyExistsError,
    PatientInvalidDataError,
)
from medfabric.db.models import Gender


def test_add_patient_success_minimal(db_session: Session):
    patient = add_patient(db_session, "p001")
    assert patient.patient_id == "p001"
    assert patient.category is None
    assert patient.age is None
    assert patient.gender is None
    assert check_patient_exists(db_session, "p001") is True


@pytest.mark.parametrize(
    "category, age, gender",
    [
        ("oncology", None, None),
        (None, 45, None),
        (None, None, Gender.Male),
        ("cardiology", 60, Gender.Female),
    ],
)
def test_add_patient_success_variations(db_session: Session, category, age, gender):
    pid = f"p_{category}_{age}_{gender}".replace(" ", "_")
    patient = add_patient(db_session, pid, category=category, age=age, gender=gender)
    assert patient.patient_id == pid
    assert patient.category == category
    assert patient.age == age
    assert patient.gender == gender


def test_add_patient_empty_id(db_session: Session):
    with pytest.raises(PatientInvalidDataError):
        add_patient(db_session, "")


def test_add_patient_already_exists(db_session: Session):
    add_patient(db_session, "p002")
    with pytest.raises(PatientAlreadyExistsError):
        add_patient(db_session, "p002")


def test_check_patient_exists_true_false(db_session: Session):
    assert check_patient_exists(db_session, "doesnotexist") is False
    add_patient(db_session, "p010")
    assert check_patient_exists(db_session, "p010") is True
