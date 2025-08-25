# medfabric/api/image_input.py
"""Module for handling image operations in the MedFabric API."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from medfabric.db.models import Image
from medfabric.api.errors import (
    DatabaseError,
    ImageAlreadyExistsError,
    InvalidImageError,
    ImageSetNotFoundError,
)
from medfabric.api.image_set_input import get_image_set


def check_image_exists_by_id(session: Session, image_id: str) -> bool:
    """
    Check if an image with the given ID exists.

    Args:
        session (Session): SQLAlchemy DB session
        image_id (str): ID of the image to check

    Returns:
        True if exists, False otherwise
    """
    return session.query(Image).filter_by(image_id=image_id).first() is not None


def check_image_exists_by_set_and_index(
    session: Session, image_set_id: str, slice_index: int
) -> bool:
    """
    Check if an image with the given image set ID and slice index exists.

    Args:
        session (Session): SQLAlchemy DB session
        image_set_id (str): ID of the image set
        slice_index (int): Slice index of the image

    Returns:
        True if exists, False otherwise
    """
    return (
        session.query(Image)
        .filter_by(image_set_id=image_set_id, slice_index=slice_index)
        .count()
        > 0
    )


def get_set_id_from_image_id(session: Session, image_id: str) -> Optional[str]:
    """
    Retrieve the image set ID for a given image ID.

    Args:
        session (Session): SQLAlchemy DB session
        image_id (str): ID of the image

    Returns:
        Image set ID if found, else None
    """
    image = session.query(Image).filter_by(image_id=image_id).first()
    return image.image_set_id if image else None


def is_image_in_set(session: Session, image_id: str, image_set_id: str) -> bool:
    """
    Return True only if the image exists and belongs to the given set.
    Otherwise, return False without leaking whether the image exists at all.
    """
    return (
        session.query(Image)
        .filter_by(image_id=image_id, image_set_id=image_set_id)
        .first()
        is not None
    )


def add_image(
    session: Session, image_id: str, image_set_id: str, slice_index: int
) -> Image:
    """
    Add a new image to the database.

    Args:
        session (Session): SQLAlchemy session.
        image_id (str): Unique identifier for the image.
        image_set_id (str): ID of the image set the image belongs to.
        slice_index (int): Index of the image slice.

    Returns:
        Image: The created image record.
    """
    if not image_id:
        raise InvalidImageError("Image ID cannot be empty.")

    if check_image_exists_by_id(session, image_id):
        raise ImageAlreadyExistsError(f"Image with ID '{image_id}' already exists.")

    if slice_index < 0:
        raise InvalidImageError("Slice index must be non-negative.")

    image_set = get_image_set(session, image_set_id)
    if not image_set:
        raise ImageSetNotFoundError(
            f"Image set with ID '{image_set_id}' does not exist."
        )
    if slice_index >= image_set.num_images:
        raise InvalidImageError(
            f"Slice index {slice_index} exceeds number of images in set ({image_set.num_images})."
        )

    if check_image_exists_by_set_and_index(session, image_set_id, slice_index):
        raise ImageAlreadyExistsError(
            f"Image with slice index '{slice_index}' already exists in image set '{image_set_id}'."
        )

    image = Image(image_id=image_id, image_set_id=image_set_id, slice_index=slice_index)
    try:
        session.add(image)
        session.commit()
        return image
    except SQLAlchemyError as exc:
        session.rollback()
        raise DatabaseError(f"Failed to add image: {exc}") from exc
