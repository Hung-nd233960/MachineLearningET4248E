# pylint: disable=missing-function-docstring,missing-module-docstring
from typing import Optional
from uuid import UUID, uuid4
import logging
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from medfabric.db.models import Doctors


# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    # DEBUG: password hashing is internal detail, not usually INFO
    logger.debug("Hashing password")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # DEBUG: verification attempt (but DO NOT log the actual password!)
    logger.debug("Verifying password for user login")
    return pwd_context.verify(plain_password, hashed_password)


def register_doctor(
    session: Session, username: str, password: str, **kwargs
) -> Doctors:
    doctor = Doctors(
        uuid=uuid4(),
        username=username,
        email=kwargs.get("email"),
        password_hash=hash_password(password),
    )

    try:
        session.add(doctor)
        session.commit()
        # INFO: successful, high-level event
        logger.info("Registered doctor '%s'", username)
        return doctor

    except IntegrityError as exc:
        session.rollback()
        # ERROR: operation failed
        logger.error(
            "Failed to register doctor '%s': username already exists", username
        )
        raise ValueError(f"Username '{username}' already exists.") from exc


def check_doctor_already_exists(session: Session, username: str) -> bool:
    """
    Check if a doctor with the given username already exists.

    Args:
        session (Session): SQLAlchemy DB session
        username (str): username to check

    Returns:
        True if exists, False otherwise
    """
    return session.query(Doctors).filter_by(username=username).count() > 0


def login_doctor(session: Session, username: str, password: str):
    """
    Login a doctor by username and password.

    Returns:
        Doctor object on success, None on failure.
    """
    doctor = session.query(Doctors).filter_by(username=username).first()
    if not doctor:
        print("❌ Username not found.")
        return None

    if verify_password(password, doctor.password_hash):
        print(f"✅ Login successful for {username}")
        return doctor
    print("❌ Invalid password.")
    return None


def get_uuid_from_username(session, username: str) -> Optional[UUID]:
    doctor = session.query(Doctors).filter_by(username=username).first()
    return doctor.uuid if doctor else None


def get_username_from_uuid(session, uuid: UUID) -> Optional[str]:
    doctor = session.query(Doctors).filter_by(uuid=uuid).first()
    return doctor.username if doctor else None
