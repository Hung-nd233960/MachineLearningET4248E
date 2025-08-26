# pylint: disable=too-many-arguments,too-many-locals, missing-module-docstring
# medfabric/api/image_evaluation_input.py
import uuid as uuid_lib
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from medfabric.db.models import ImageEvaluation, Region
from medfabric.api.errors import (
    UserNotFoundError,
    ImageNotFoundError,
    DatabaseError,
    SessionNotFoundError,
    SessionMismatchError,
    SessionInactiveError,
    InvalidEvaluationError,
    EvaluationAlreadyExistsError,
)
from medfabric.api.sessions import doctor_exists, get_session
from medfabric.api.image_input import (
    check_image_exists_by_uuid,
    get_set_id_from_image_id,
)
from medfabric.api.image_set_evaluation_input import (
    check_set_evaluation_exists,
)
from medfabric.api.config import SCORE_LIMITS


def add_evaluate_image(
    session: Session,
    doctor_id: uuid_lib.UUID,
    image_uuid: uuid_lib.UUID,
    session_id: uuid_lib.UUID,
    region: Region = Region.None_,
    basal_score_central_left: Optional[int] = None,
    basal_score_central_right: Optional[int] = None,
    basal_score_cortex_left: Optional[int] = None,
    basal_score_cortex_right: Optional[int] = None,
    corona_score_left: Optional[int] = None,
    corona_score_right: Optional[int] = None,
    notes: Optional[str] = None,
) -> ImageEvaluation:
    """
    Evaluates a single image by a doctor.
    """

    # --- Entity existence checks ---
    if not doctor_exists(session, doctor_id):
        raise UserNotFoundError("Doctor with the given UUID does not exist.")

    if not check_image_exists_by_uuid(session, image_uuid):
        raise ImageNotFoundError("Image with the given UUID does not exist.")

    session_result = get_session(session, session_id)
    if not session_result:
        raise SessionNotFoundError("Session with the given ID does not exist.")

    if session_result.doctor_id != doctor_id:
        raise SessionMismatchError("The session does not belong to the given doctor.")

    if not session_result.is_active:
        raise SessionInactiveError("The session is not active.")

    if not isinstance(region, Region):
        raise InvalidEvaluationError(f"Expected Region, got {region!r}")

    image_set_uuid = get_set_id_from_image_id(session, image_uuid)
    if not image_set_uuid:
        raise ImageNotFoundError("Image does not belong to any image set.")

    # --- Duplicate evaluation checks ---
    if check_set_evaluation_exists(session, doctor_id, image_set_uuid, session_id):
        raise EvaluationAlreadyExistsError(
            "An evaluation for this image set by the doctor in the given session already exists."
        )

    if check_image_evaluation_exists(session, doctor_id, image_uuid, session_id):
        raise EvaluationAlreadyExistsError(
            "An evaluation for this image by the doctor in the given session already exists."
        )

    # --- Validate region and score consistency ---
    region_score_requirements(
        region,
        basal_score_central_left,
        basal_score_central_right,
        basal_score_cortex_left,
        basal_score_cortex_right,
        corona_score_left,
        corona_score_right,
    )

    # Check score ranges
    validate_evaluation_scores(
        basal_score_central_left=basal_score_central_left,
        basal_score_central_right=basal_score_central_right,
        basal_score_cortex_left=basal_score_cortex_left,
        basal_score_cortex_right=basal_score_cortex_right,
        corona_score_left=corona_score_left,
        corona_score_right=corona_score_right,
    )

    # --- Create evaluation ---
    evaluation = ImageEvaluation(
        doctor_id=doctor_id,
        image_uuid=image_uuid,
        session_id=session_id,
        region=region,
        basal_score_central_left=basal_score_central_left,
        basal_score_central_right=basal_score_central_right,
        basal_score_cortex_left=basal_score_cortex_left,
        basal_score_cortex_right=basal_score_cortex_right,
        corona_score_left=corona_score_left,
        corona_score_right=corona_score_right,
        notes=notes,
    )

    try:
        session.add(evaluation)
        session.commit()
        return evaluation
    except SQLAlchemyError as e:
        session.rollback()
        raise DatabaseError(f"Failed to add image evaluation: {e}") from e


def check_image_evaluation_exists(
    session: Session,
    doctor_id: uuid_lib.UUID,
    image_uuid: uuid_lib.UUID,
    session_id: uuid_lib.UUID,
) -> bool:
    """
    Checks if an image evaluation exists for the given doctor, image, and session.

    Args:
        session (Session): SQLAlchemy session.
        doctor_id (uuid.UUID): ID of the doctor.
        image_uuid (uuid.UUID): ID of the image.
        session_id (uuid.UUID): ID of the session.

    Returns:
        bool: True if the evaluation exists, False otherwise.
    """
    return (
        session.query(ImageEvaluation)
        .filter_by(doctor_id=doctor_id, image_uuid=image_uuid, session_id=session_id)
        .first()
        is not None
    )


def validate_evaluation_scores(**kwargs):
    """
    Validates that the provided scores are within acceptable ranges.
    Raises InvalidEvaluationError if any score is out of range."""
    for name, max_val in SCORE_LIMITS.items():
        value = kwargs.get(name)
        if value is not None and not 0 <= value <= max_val:
            raise InvalidEvaluationError(
                f"{name} must be between 0 and {max_val}, got {value}."
            )


def region_score_requirements(
    region: Region,
    basal_score_central_left,
    basal_score_central_right,
    basal_score_cortex_left,
    basal_score_cortex_right,
    corona_score_left,
    corona_score_right,
):
    """Validates that the provided scores align with the specified region."""
    scores = {
        "basal_score_central_left": basal_score_central_left,
        "basal_score_central_right": basal_score_central_right,
        "basal_score_cortex_left": basal_score_cortex_left,
        "basal_score_cortex_right": basal_score_cortex_right,
        "corona_score_left": corona_score_left,
        "corona_score_right": corona_score_right,
    }
    region_score_requirements = {
        Region.None_: {
            "required": [],
            "forbidden": [
                "basal_score_central_left",
                "basal_score_central_right",
                "basal_score_cortex_left",
                "basal_score_cortex_right",
                "corona_score_left",
                "corona_score_right",
            ],
        },
        Region.BasalCentral: {
            "required": ["basal_score_central_left", "basal_score_central_right"],
            "forbidden": ["corona_score_left", "corona_score_right"],
        },
        Region.BasalCortex: {
            "required": ["basal_score_cortex_left", "basal_score_cortex_right"],
            "forbidden": ["corona_score_left", "corona_score_right"],
        },
        Region.CoronaRadiata: {
            "required": ["corona_score_left", "corona_score_right"],
            "forbidden": [
                "basal_score_central_left",
                "basal_score_central_right",
                "basal_score_cortex_left",
                "basal_score_cortex_right",
            ],
        },
    }
    reqs = region_score_requirements[region]

    # Check required fields
    for field in reqs["required"]:
        if scores[field] is None:
            raise InvalidEvaluationError(
                f"{field} must be provided for region '{region.name}'."
            )

    # Check forbidden fields
    for field in reqs["forbidden"]:
        if scores[field] is not None:
            raise InvalidEvaluationError(
                f"{field} must not be provided for region '{region.name}'."
            )
