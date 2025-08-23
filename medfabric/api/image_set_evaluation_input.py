import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from medfabric.db.models import Doctors, Region, ImageSetEvaluation, ImageSet
from medfabric.api.config import (
    BASEL_CENTRAL_MAX,
    BASEL_CORTEX_MAX,
    CORONA_MAX,
    DATA_PATH,
)
from medfabric.api.errors import (
    UserNotFoundError,
    SessionNotFoundError,
    SessionInactiveError,
    SessionMismatchError,
    DatabaseError,
    SessionAlreadyExistsError,
)
from medfabric.api.sessions import doctor_exists, get_session


def evaluate_image_set(
    session: Session,
    doctor_id: uuid_lib.UUID,
    image_set_id: str,
    session_id: uuid_lib.UUID,
    is_low_quality: bool = False,
    is_irrelevant: bool = False,
) -> ImageSetEvaluation:
    """
    Evaluates an image set by a doctor.

    Args:
        session (Session): SQLAlchemy session.
        doctor_id (uuid_lib.UUID): ID of the doctor evaluating the image set.
        image_set_id (str): ID of the image set being evaluated.
        session_id (uuid_lib.UUID): ID of the session during which the evaluation is made.
        is_low_quality (bool): Indicates if the image set is of low quality.
        is_irrelevant (bool): Indicates if the image set is irrelevant.

    Returns:
        ImageSetEvaluation: The created evaluation record.
    """

    if not doctor_exists(session, doctor_id):
        raise UserNotFoundError("Doctor with the given UUID does not exist.")

    session_result = get_session(session, session_id)
    if not session_result:
        raise SessionNotFoundError("Session with the given UUID does not exist.")
    if session_result.doctor_id != doctor_id:
        raise SessionMismatchError("Session does not belong to the specified doctor.")
    if not session_result.is_active:
        raise SessionInactiveError("Session is not active.")

    try:
        evaluation = ImageSetEvaluation(
            doctor_id=doctor_id,
            image_set_id=image_set_id,
            session_id=session_id,
            is_low_quality=is_low_quality,
            is_irrelevant=is_irrelevant,
        )
        session.add(evaluation)
        session.commit()
        return evaluation
    except IntegrityError as exc:
        session.rollback()
        raise SessionAlreadyExistsError(
            "An evaluation for this triplet already exists."
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise DatabaseError("Failed to evaluate image set.") from exc
