from typing import Optional
import uuid
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from utils.models import Doctor  # assuming your model is named models.py

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def register_doctor(session, username: str, password: str, **kwargs):
    """
    Register a new doctor with a hashed password.

    Args:
        session: SQLAlchemy DB session
        username (str): desired username
        password (str): plaintext password
        **kwargs: additional fields like email

    Returns:
        Doctor instance or raises Exception on failure
    """
    doctor = Doctor(
        uuid=str(uuid.uuid4()),
        username=username,
        email=kwargs.get("email"),
        password_hash=hash_password(password),
    )

    try:
        session.add(doctor)
        session.commit()
        print(f"✅ Registered doctor {username}")
        return doctor
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"❌ Username '{username}' already exists.") from exc


def check_doctor_already_exists(session, username: str) -> bool:
    """
    Check if a doctor with the given username already exists.

    Args:
        session: SQLAlchemy DB session
        username (str): username to check

    Returns:
        True if exists, False otherwise
    """
    return session.query(Doctor).filter_by(username=username).count() > 0


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def login_doctor(session, username: str, password: str):
    """
    Login a doctor by username and password.

    Returns:
        Doctor object on success, None on failure.
    """
    doctor = session.query(Doctor).filter_by(username=username).first()
    if not doctor:
        print("❌ Username not found.")
        return None

    if verify_password(password, doctor.password_hash):
        print(f"✅ Login successful for {username}")
        return doctor
    else:
        print("❌ Invalid password.")
        return None


def get_uuid_from_username(session, username: str) -> Optional[str]:
    doctor = session.query(Doctor).filter_by(username=username).first()
    return doctor.uuid if doctor else None


def get_username_from_uuid(session, uuid: str) -> Optional[str]:
    doctor = session.query(Doctor).filter_by(uuid=uuid).first()
    return doctor.username if doctor else None
