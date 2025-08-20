from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from utils.db.models import Evaluation, Doctor, Region, ImageSetEvaluation
from api.config import BASEL_MAX, CORONA_MAX


def add_or_update_image_evaluation(
    session: Session,
    doctor_id: str,
    image_id: str,
    image_set_id: str,
    region: Region,
    basal_score: int | None = None,
    corona_score: int | None = None,
    notes: str | None = None,
) -> Evaluation:
    """
    Add or update an evaluation with validation.
    """

    # Check doctor exists
    doctor = session.query(Doctor).filter_by(uuid=doctor_id).first()
    if not doctor:
        raise ValueError(f"Doctor ID '{doctor_id}' does not exist.")

    # Validation
    if region is None:
        raise ValueError("Region must not be None.")

    if region == Region.BasalGanglia:
        if basal_score is None or not (0 <= basal_score <= BASEL_MAX):
            raise ValueError(f"BasalGanglia score must be between 0 and {BASEL_MAX}.")
        if corona_score is not None:
            raise ValueError("Corona score must be null for BasalGanglia.")
    elif region == Region.CoronaRadiata:
        if corona_score is None or not (0 <= corona_score <= CORONA_MAX):
            raise ValueError(f"CoronaRadiata score must be between 0 and {CORONA_MAX}.")
        if basal_score is not None:
            raise ValueError("Basal score must be null for CoronaRadiata.")
    elif region == Region.None_:
        if basal_score is not None or corona_score is not None:
            raise ValueError("Scores must be null when region is None.")

    # Check if evaluation already exists
    evaluation = (
        session.query(Evaluation)
        .filter_by(doctor_id=doctor_id, image_id=image_id, image_set_id=image_set_id)
        .first()
    )

    if evaluation:
        # Update existing
        evaluation.region = region
        evaluation.basal_score = basal_score
        evaluation.corona_score = corona_score
        evaluation.notes = notes
        print("🔁 Evaluation updated.")
    else:
        # Add new
        evaluation = Evaluation(
            doctor_id=doctor_id,
            image_id=image_id,
            image_set_id=image_set_id,
            region=region,
            basal_score=basal_score,
            corona_score=corona_score,
            notes=notes or "",
        )
        session.add(evaluation)
        print("✅ Evaluation created.")

    try:
        session.commit()
        return evaluation
    except IntegrityError as e:
        session.rollback()
        raise ValueError(f"❌ Failed to write evaluation: {e}") from e


def delete_image_evaluation(
    session: Session, doctor_id: str, image_id: str, image_set_id: str
) -> bool:
    """
    Delete an evaluation by doctor and image reference.

    Returns:
        True if deleted, False if no such evaluation exists.
    """
    evaluation = (
        session.query(Evaluation)
        .filter_by(doctor_id=doctor_id, image_id=image_id, image_set_id=image_set_id)
        .first()
    )

    if evaluation:
        session.delete(evaluation)
        session.commit()
        print("🗑️ Evaluation deleted.")
        return True
    else:
        print("⚠️ Evaluation not found.")
        return False


def add_or_update_set_evaluation(
    session, doctor_id: str, image_set_id: str, low_quality=False, irrelevant=False
):
    """
    Add or update a doctor's evaluation for an image set.
    """
    evaluation = (
        session.query(ImageSetEvaluation)
        .filter_by(doctor_id=doctor_id, image_set_id=image_set_id)
        .first()
    )

    if evaluation:
        # Update existing
        evaluation.low_quality = low_quality
        evaluation.irrelevant = irrelevant
        print(f"🔁 Updated evaluation for {image_set_id}")
    else:
        # Insert new
        evaluation = ImageSetEvaluation(
            doctor_id=doctor_id,
            image_set_id=image_set_id,
            is_low_quality=low_quality,
            is_irrelevant=irrelevant,
        )
        session.add(evaluation)
        print(f"🆕 Added evaluation for {image_set_id}")

    session.commit()


def delete_evaluations_for_image_set(session: Session, image_set_id: str) -> int:
    """
    Delete all per-image and per-image-set evaluations for a given image set ID.

    Returns:
        int: Total number of deleted evaluation records.
    """
    # Delete per-image evaluations
    deleted_image_evals = (
        session.query(Evaluation).filter_by(image_set_id=image_set_id).delete()
    )

    # Delete image-set-level evaluations
    deleted_set_evals = (
        session.query(ImageSetEvaluation).filter_by(image_set_id=image_set_id).delete()
    )

    session.commit()
    total_deleted = deleted_image_evals + deleted_set_evals
    print(
        f"🗑️ Deleted {deleted_image_evals} image evaluations and {deleted_set_evals} set evaluations for '{image_set_id}'"
    )

    return total_deleted
