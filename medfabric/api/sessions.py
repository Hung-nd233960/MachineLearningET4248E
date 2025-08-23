# medfabric/api/sessions.py
import logging
from typing import Union, Optional
import uuid as uuid_lib
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from medfabric.db.models import Session as SessionModel, Doctors
from medfabric.api.errors import (
    SessionNotFoundError,
    InvalidUUIDError,
    DatabaseError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)


def validate_uuid(u: Union[str, uuid_lib.UUID]) -> Optional[uuid_lib.UUID]:
    """Return UUID object if valid, else None."""
    if isinstance(u, uuid_lib.UUID):
        return u
    try:
        return uuid_lib.UUID(str(u))
    except ValueError:
        return None


def doctor_exists(db: Session, doctor_id: uuid_lib.UUID) -> bool:
    """Check if a doctor with this UUID exists."""
    return db.query(Doctors).filter(Doctors.uuid == doctor_id).count() > 0


def create_session(db: Session, doctor_id: Union[str, uuid_lib.UUID]) -> SessionModel:
    """Create a new login session for a doctor."""
    doctor_uuid = validate_uuid(doctor_id)
    if not doctor_uuid:
        logger.error("Invalid doctor UUID: %s", doctor_id)
        raise InvalidUUIDError(f"Invalid doctor UUID: {doctor_id}")

    if not doctor_exists(db, doctor_uuid):
        logger.error("Doctor UUID does not exist: %s", doctor_uuid)
        raise UserNotFoundError(f"Doctor UUID does not exist: {doctor_uuid}")

    try:
        new_sess = SessionModel(doctor_id=doctor_uuid)
        db.add(new_sess)
        db.commit()
        db.refresh(new_sess)
        logger.info(
            "Created new session %s for doctor %s", new_sess.session_id, doctor_uuid
        )
        return new_sess
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(
            "Database error while creating session for doctor %s", doctor_uuid
        )
        raise DatabaseError(f"Failed to create session: {e}") from e


def get_session(
    db: Session, session_id: Union[str, uuid_lib.UUID]
) -> Optional[SessionModel]:
    """Retrieve session info by ID."""
    sess_uuid = validate_uuid(session_id)
    if not sess_uuid:
        logger.warning("Invalid session UUID: %s", session_id)
        return None

    sess = db.get(SessionModel, sess_uuid)
    if sess:
        logger.debug("Retrieved session %s", sess_uuid)
    else:
        logger.debug("Session %s not found", sess_uuid)
    return sess


def deactivate_session(db: Session, session_id: Union[str, uuid_lib.UUID]) -> None:
    """Mark a session as inactive (logout)."""
    sess_uuid = validate_uuid(session_id)
    if not sess_uuid:
        logger.error("Invalid session UUID: %s", session_id)
        raise InvalidUUIDError(f"Invalid session UUID: {session_id}")

    try:
        sess = db.get(SessionModel, sess_uuid)
        if not sess:
            logger.error("Tried to deactivate non-existent session %s", sess_uuid)
            raise SessionNotFoundError(f"Session {sess_uuid} does not exist")

        sess.is_active = False
        db.commit()
        logger.info("Deactivated session %s", sess_uuid)

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error while deactivating session %s", sess_uuid)
        raise DatabaseError(f"Failed to deactivate session {sess_uuid}") from e


def list_active_sessions(
    db: Session, doctor_id: Union[str, uuid_lib.UUID]
) -> list[SessionModel]:
    """Return all active sessions for a doctor."""
    doctor_uuid = validate_uuid(doctor_id)
    if not doctor_uuid:
        logger.error("Invalid doctor UUID: %s", doctor_id)
        raise InvalidUUIDError(f"Invalid doctor UUID: {doctor_id}")

    if not doctor_exists(db, doctor_uuid):
        logger.error("Doctor UUID does not exist: %s", doctor_uuid)
        raise UserNotFoundError(f"Doctor UUID {doctor_uuid} does not exist")

    try:
        active_sessions = (
            db.query(SessionModel)
            .filter(
                SessionModel.doctor_id == doctor_uuid,
                SessionModel.is_active.is_(True),
            )
            .all()
        )
        logger.debug(
            "Found %d active sessions for doctor %s", len(active_sessions), doctor_uuid
        )
        return active_sessions

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(
            "Database error while listing sessions for doctor %s", doctor_uuid
        )
        raise DatabaseError(f"Failed to list sessions for doctor {doctor_uuid}") from e
