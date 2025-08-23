# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
# tests/sessions_test.py
import uuid as uuid_lib
import pytest
from medfabric.api.sessions import (
    create_session,
    get_session,
    deactivate_session,
    list_active_sessions,
    validate_uuid,
)
from medfabric.db.models import Doctors
from medfabric.api.errors import (
    InvalidUUIDError,
    UserNotFoundError,
    SessionNotFoundError,
)


def test_validate_uuid():
    valid_str = str(uuid_lib.uuid4())
    invalid_str = "not-a-uuid"

    assert isinstance(validate_uuid(valid_str), uuid_lib.UUID)
    assert validate_uuid(invalid_str) is None


def test_create_session_success(db_session):
    # first create a doctor
    doctor = Doctors(username="testdoc", password_hash="hashedpw")
    db_session.add(doctor)
    db_session.commit()

    new_sess = create_session(db_session, doctor.uuid)
    assert new_sess.doctor_id == doctor.uuid
    assert new_sess.is_active is True

    # should appear in DB
    db_sess = db_session.get(type(new_sess), new_sess.session_id)
    assert db_sess is not None


def test_create_session_invalid_uuid(db_session):
    with pytest.raises(InvalidUUIDError):
        create_session(db_session, "not-a-uuid")


def test_create_session_nonexistent_doctor(db_session):
    fake_uuid = uuid_lib.uuid4()
    with pytest.raises(UserNotFoundError):
        create_session(db_session, fake_uuid)


def test_get_session(db_session):
    doctor = Doctors(username="getdoc", password_hash="hashedpw")
    db_session.add(doctor)
    db_session.commit()

    new_sess = create_session(db_session, doctor.uuid)
    retrieved = get_session(db_session, new_sess.session_id)
    assert retrieved is not None
    assert retrieved.session_id == new_sess.session_id

    # invalid UUID returns None
    assert get_session(db_session, "bad-uuid") is None

    # non-existing UUID returns None
    assert get_session(db_session, uuid_lib.uuid4()) is None


def test_deactivate_session(db_session):
    doctor = Doctors(username="deactdoc", password_hash="hashedpw")
    db_session.add(doctor)
    db_session.commit()

    new_sess = create_session(db_session, doctor.uuid)
    deactivate_session(db_session, new_sess.session_id)

    db_sess = db_session.get(type(new_sess), new_sess.session_id)
    assert db_sess.is_active is False

    # invalid UUID raises
    with pytest.raises(InvalidUUIDError):
        deactivate_session(db_session, "not-a-uuid")

    # non-existing UUID raises
    with pytest.raises(SessionNotFoundError):
        deactivate_session(db_session, uuid_lib.uuid4())


def test_list_active_sessions(db_session):
    doctor = Doctors(username="listdoc", password_hash="hashedpw")
    db_session.add(doctor)
    db_session.commit()

    # no sessions yet
    active = list_active_sessions(db_session, doctor.uuid)
    assert active == []

    # create two sessions
    s1 = create_session(db_session, doctor.uuid)
    s2 = create_session(db_session, doctor.uuid)

    active = list_active_sessions(db_session, doctor.uuid)
    assert len(active) == 2

    # deactivate one
    deactivate_session(db_session, s1.session_id)
    active = list_active_sessions(db_session, doctor.uuid)
    assert len(active) == 1

    # invalid UUID returns empty list
    with pytest.raises(InvalidUUIDError):
        list_active_sessions(db_session, "not-a-uuid")

    with pytest.raises(UserNotFoundError):
        # non-existing doctor raises
        list_active_sessions(db_session, uuid_lib.uuid4())
