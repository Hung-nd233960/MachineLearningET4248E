import uuid
import pytest
from medfabric.db.models import Doctors
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


def test_register_doctor_success(session):
    doctor = register_doctor(session, "alice", "pw123", email="alice@example.com")
    assert doctor.username == "alice"
    assert doctor.email == "alice@example.com"
    assert doctor.password_hash != "pw123"  # should be hashed
    assert isinstance(doctor.uuid, uuid.UUID)

    # doctor persisted
    found = session.query(Doctors).filter_by(username="alice").first()
    assert found is not None


def test_register_doctor_duplicate_username(session):
    register_doctor(session, "bob", "pw123")
    with pytest.raises(ValueError) as excinfo:
        register_doctor(session, "bob", "pw456")
    assert "already exists" in str(excinfo.value)


def test_check_doctor_already_exists(session):
    register_doctor(session, "charlie", "pw123")
    assert check_doctor_already_exists(session, "charlie") is True
    assert check_doctor_already_exists(session, "ghost") is False


def test_login_doctor_success(session, capsys):
    register_doctor(session, "dana", "pw123")
    doctor = login_doctor(session, "dana", "pw123")
    assert doctor is not None
    captured = capsys.readouterr()
    assert "✅ Login successful" in captured.out


def test_login_doctor_wrong_password(session, capsys):
    register_doctor(session, "eve", "pw123")
    result = login_doctor(session, "eve", "wrongpw")
    assert result is None
    captured = capsys.readouterr()
    assert "❌ Invalid password." in captured.out


def test_login_doctor_no_user(session, capsys):
    result = login_doctor(session, "nobody", "pw123")
    assert result is None
    captured = capsys.readouterr()
    assert "❌ Username not found." in captured.out


def test_get_uuid_and_username(session):
    doc = register_doctor(session, "frank", "pw123")

    uuid_val = get_uuid_from_username(session, "frank")
    assert uuid_val == doc.uuid
    assert isinstance(uuid_val, uuid.UUID)

    username_val = get_username_from_uuid(session, uuid_val)
    assert username_val == "frank"

    # non-existing
    assert get_uuid_from_username(session, "ghost") is None
    assert get_username_from_uuid(session, uuid.uuid4()) is None
