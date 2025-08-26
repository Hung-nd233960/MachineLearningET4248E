# pylint: disable=missing-function-docstring,missing-module-docstring, unused-argument
# tests/image_set_evaluation_input_test.py
import uuid as uuid_lib
import pytest

from sqlalchemy.orm import Session as db_Session
from medfabric.api.credentials import register_doctor
from medfabric.api.image_set_evaluation_input import (
    add_evaluate_image_set,
    check_set_evaluation_exists,
)
from medfabric.db.models import Doctors, ImageSet, Session
from medfabric.api.image_set_input import add_image_set
from medfabric.api.sessions import create_session
from medfabric.api.errors import (
    UserNotFoundError,
    SessionNotFoundError,
    SessionInactiveError,
    SessionMismatchError,
    ImageSetNotFoundError,
    InvalidEvaluationError,
    EvaluationAlreadyExistsError,
)


@pytest.fixture
def doctor(db_session: db_Session) -> Doctors:
    """Create and return a test doctor."""
    return register_doctor(db_session, "doc1", "password123")


@pytest.fixture
def image_set(db_session: db_Session) -> ImageSet:
    """Create and return a test image set."""
    return add_image_set(db_session, "set1", 5)


@pytest.fixture
def session(db_session: db_Session, doctor: Doctors) -> Session:
    """Create and return a test session for the doctor."""
    return create_session(db_session, doctor.uuid)


def test_add_evaluate_image_set_success(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet, session: Session
):
    evaluation = add_evaluate_image_set(
        db_session,
        doctor.uuid,
        image_set.uuid,
        session.session_id,
        is_low_quality=True,
        is_irrelevant=False,
    )
    assert evaluation.doctor_id == doctor.uuid
    assert evaluation.image_set_uuid == image_set.uuid
    assert evaluation.session_id == session.session_id
    assert evaluation.is_low_quality is True
    assert evaluation.is_irrelevant is False


def test_add_evaluate_image_set_doctor_not_found(
    db_session: db_Session, image_set: ImageSet, session: Session
):
    fake_doctor_id = uuid_lib.uuid4()
    with pytest.raises(UserNotFoundError):
        add_evaluate_image_set(
            db_session,
            fake_doctor_id,
            image_set.uuid,
            session.session_id,
        )


def test_add_evaluate_image_set_session_not_found(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet
):
    fake_session_id = uuid_lib.uuid4()
    with pytest.raises(SessionNotFoundError):
        add_evaluate_image_set(
            db_session,
            doctor.uuid,
            image_set.uuid,
            fake_session_id,
        )


def test_add_evaluate_image_set_session_inactive(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet
):
    sess = create_session(db_session, doctor.uuid)
    # Manually set session to inactive
    sess.is_active = False
    db_session.commit()
    with pytest.raises(SessionInactiveError):
        add_evaluate_image_set(
            db_session,
            doctor.uuid,
            image_set.uuid,
            sess.session_id,
        )


def test_add_evaluate_image_set_session_mismatch(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet
):
    other_doctor = register_doctor(db_session, "doc2", "password456")
    sess = create_session(db_session, other_doctor.uuid)
    with pytest.raises(SessionMismatchError):
        add_evaluate_image_set(
            db_session,
            doctor.uuid,
            image_set.uuid,
            sess.session_id,
        )


def test_add_evaluate_image_set_image_set_not_found(
    db_session: db_Session, doctor: Doctors, session: Session
):
    with pytest.raises(ImageSetNotFoundError):
        add_evaluate_image_set(
            db_session,
            doctor.uuid,
            uuid_lib.uuid4(),
            session.session_id,
        )


def test_add_evaluate_image_set_invalid_evaluation(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet, session: Session
):
    with pytest.raises(InvalidEvaluationError):
        add_evaluate_image_set(
            db_session,
            doctor.uuid,
            image_set.uuid,
            session.session_id,
            is_low_quality=False,
            is_irrelevant=False,
        )


def test_add_evaluate_image_set_duplicate_evaluation(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet, session: Session
):
    add_evaluate_image_set(
        db_session,
        doctor.uuid,
        image_set.uuid,
        session.session_id,
        is_low_quality=True,
    )
    with pytest.raises(EvaluationAlreadyExistsError):
        add_evaluate_image_set(
            db_session,
            doctor.uuid,
            image_set.uuid,
            session.session_id,
            is_low_quality=False,
            is_irrelevant=True,
        )


def test_check_evaluation_exists(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet, session: Session
):
    assert not check_set_evaluation_exists(
        db_session,
        doctor.uuid,
        image_set.uuid,
        session.session_id,
    )
    add_evaluate_image_set(
        db_session,
        doctor.uuid,
        image_set.uuid,
        session.session_id,
        is_low_quality=True,
    )
    assert check_set_evaluation_exists(
        db_session,
        doctor.uuid,
        image_set.uuid,
        session.session_id,
    )


def test_add_evaluate_image_set_duplicate_does_not_break_existing(
    db_session: db_Session, doctor: Doctors, image_set: ImageSet, session: Session
):
    add_evaluate_image_set(
        db_session,
        doctor.uuid,
        image_set.uuid,
        session.session_id,
        is_low_quality=True,
    )
    with pytest.raises(EvaluationAlreadyExistsError):
        add_evaluate_image_set(
            db_session,
            doctor.uuid,
            image_set.uuid,
            session.session_id,
            is_irrelevant=True,
        )
    # Make sure the first evaluation still exists in DB
    assert check_set_evaluation_exists(
        db_session, doctor.uuid, image_set.uuid, session.session_id
    )
