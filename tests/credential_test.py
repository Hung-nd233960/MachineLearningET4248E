# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
# tests/credential_test.py
import uuid
import pytest
from medfabric.db.models import Doctors
from medfabric.api.errors import (
    InvalidCredentialsError,
    UserNotFoundError,
    DuplicateEntryError,
)
from medfabric.api.credentials import (
    hash_password,
    verify_password,
    register_doctor,
    check_doctor_already_exists,
    login_doctor,
    get_uuid_from_username,
    get_username_from_uuid,
)


def test_hash_and_verify_password():
    pw = "supersecret"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpw", hashed) is False


def test_register_doctor_success(db_session):
    doctor = register_doctor(db_session, "alice", "pw123", email="alice@example.com")
    assert doctor.username == "alice"
    assert doctor.email == "alice@example.com"
    assert doctor.password_hash != "pw123"  # should be hashed
    assert isinstance(doctor.uuid, uuid.UUID)

    # doctor persisted
    found = db_session.query(Doctors).filter_by(username="alice").first()
    assert found is not None


def test_register_doctor_duplicate_username(db_session):
    register_doctor(db_session, "bob", "pw123")
    with pytest.raises(DuplicateEntryError) as excinfo:
        register_doctor(db_session, "bob", "pw456")
    assert "already exists" in str(excinfo.value)


def test_check_doctor_already_exists(db_session):
    register_doctor(db_session, "charlie", "pw123")
    assert check_doctor_already_exists(db_session, "charlie") is True
    assert check_doctor_already_exists(db_session, "ghost") is False


def test_login_doctor_success(db_session):
    register_doctor(db_session, "dana", "pw123")
    doctor = login_doctor(db_session, "dana", "pw123")
    assert doctor is not None


def test_login_doctor_wrong_password(db_session):
    register_doctor(db_session, "eve", "pw123")
    with pytest.raises(InvalidCredentialsError):
        login_doctor(db_session, "eve", "wrongpw")


def test_login_doctor_no_user(db_session):
    with pytest.raises(UserNotFoundError):
        login_doctor(db_session, "nobody", "pw123")


def test_get_uuid_and_username(db_session):
    doc = register_doctor(db_session, "frank", "pw123")

    uuid_val = get_uuid_from_username(db_session, "frank")
    assert uuid_val == doc.uuid
    assert isinstance(uuid_val, uuid.UUID)

    username_val = get_username_from_uuid(db_session, uuid_val)
    assert username_val == "frank"

    # non-existing
    assert get_uuid_from_username(db_session, "ghost") is None
    assert get_username_from_uuid(db_session, uuid.uuid4()) is None
