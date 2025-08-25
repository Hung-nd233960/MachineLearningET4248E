# medfabric/api/image_set_input.py
"""Module for handling image set input operations in the MedFabric API."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from medfabric.db.models import ImageSet
from medfabric.api.errors import (
    PatientNotFoundError,
    DatabaseError,
    ImageSetAlreadyExistsError,
    InvalidImageSetError,
)
from medfabric.api.patients import check_patient_exists


def add_image_set(
    session: Session,
    image_set_id: str,
    num_images: int,
    folder_path: Optional[str] = None,
    patient_id: Optional[str] = None,
    description: Optional[str] = None,
) -> ImageSet:
    """
    Add a new image set to the database.
    Args:
        session (Session): SQLAlchemy session.
        image_set_id (str): Unique identifier for the image set.
        patient_id (str): ID of the patient associated with the image set.
        num_images (int): Number of images in the set.
        folder_path (str, optional): Path to the folder containing the images.
        description (str, optional): Description of the image set.
    Returns:
        ImageSet: The created image set record.
    """
    if not image_set_id:
        raise InvalidImageSetError("Image set ID cannot be empty.")

    if check_image_set_exists(session, image_set_id):
        raise ImageSetAlreadyExistsError(
            f"Image set with ID '{image_set_id}' already exists."
        )

    if patient_id is not None:
        if not check_patient_exists(session, patient_id):
            raise PatientNotFoundError(
                f"Patient with ID '{patient_id}' does not exist."
            )
    if num_images <= 0:
        raise InvalidImageSetError("Number of images must be greater than zero.")

    if not description:
        description = None

    image_set = ImageSet(
        image_set_id=image_set_id,
        patient_id=patient_id,
        num_images=num_images,
        folder_path=folder_path,
        description=description,
    )
    try:
        session.add(image_set)
        session.commit()
        return image_set
    except SQLAlchemyError as exc:
        session.rollback()
        raise DatabaseError(f"Failed to add image set: {exc}") from exc


def get_image_set(session: Session, image_set_id: str) -> Optional[ImageSet]:
    """
    Retrieve an image set by its ID.

    Args:
        session (Session): SQLAlchemy DB session
        image_set_id (str): ID of the image set to retrieve

    Returns:
        ImageSet if found, None otherwise
    """
    return session.query(ImageSet).filter_by(image_set_id=image_set_id).one_or_none()


def check_image_set_exists(session: Session, image_set_id: str) -> bool:
    """
    Check if an image set with the given ID exists.

    Args:
        session (Session): SQLAlchemy DB session
        image_set_id (str): ID of the image set to check

    Returns:
        True if exists, False otherwise
    """
    return (
        session.query(ImageSet).filter_by(image_set_id=image_set_id).first() is not None
    )
