# pylint: disable=missing-function-docstring,missing-module-docstring
# tests/image_set_input.py
import pytest
from medfabric.db.models import ImageSet
from medfabric.api.errors import (
    PatientNotFoundError,
    ImageSetAlreadyExistsError,
    InvalidImageSetError,
)
from medfabric.api.image_set_input import add_image_set
from medfabric.api.patients import add_patient


def test_add_image_set_success(db_session):
    # Add a patient first
    add_patient(db_session, "patient123", category="oncology", age=50)
    # Call the function
    image_set = add_image_set(
        session=db_session,
        image_set_id="set1",
        patient_id="patient123",
        folder_path="/data/patient123/set1",
        num_images=5,
        description="Test scan",
    )

    assert image_set.image_set_id == "set1"
    assert image_set.num_images == 5
    assert image_set.patient_id == "patient123"
    assert image_set.folder_path == "/data/patient123/set1"
    assert image_set.description == "Test scan"


def test_empty_image_set_id(db_session):
    with pytest.raises(InvalidImageSetError):
        add_image_set(db_session, "", num_images=3)


def test_add_image_set_already_exists(db_session):
    # Insert existing image set
    existing = ImageSet(
        image_set_id="set1",
        patient_id=None,
        num_images=3,
        folder_path="/data/none/set1",
    )
    db_session.add(existing)
    db_session.commit()

    with pytest.raises(ImageSetAlreadyExistsError):
        add_image_set(db_session, "set1", 5)


def test_add_image_set_patient_not_found(db_session):
    with pytest.raises(PatientNotFoundError):
        add_image_set(db_session, "set2", 4, patient_id="missing")


def test_add_image_set_invalid_num_images(db_session):
    with pytest.raises(InvalidImageSetError):
        add_image_set(db_session, "set3", 0)


def test_get_image_set_success(db_session):
    # Add a patient first
    add_patient(db_session, "patient456", category="cardiology", age=60)
    # Add an image set
    add_image_set(
        session=db_session,
        image_set_id="set2",
        patient_id="patient456",
        num_images=10,
        description="Heart scan",
    )

    # Retrieve the image set
    image_set = db_session.query(ImageSet).filter_by(image_set_id="set2").first()
    assert image_set is not None
    assert image_set.image_set_id == "set2"
    assert image_set.num_images == 10
    assert image_set.patient_id == "patient456"
    assert image_set.description == "Heart scan"


def test_get_image_set_not_found(db_session):
    image_set = db_session.query(ImageSet).filter_by(image_set_id="nonexistent").first()
    assert image_set is None
