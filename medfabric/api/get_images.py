# medfabric/api/get_images.py
import uuid as uuid_lib
from sqlalchemy.orm import Session
from medfabric.db.models import Image


def get_images_by_set_id(
    session: Session, image_set_uuid: uuid_lib.UUID
) -> list[Image]:
    """
    Retrieve all images associated with a given image set ID.

    Args:
        session (Session): SQLAlchemy DB session
        image_set_uuid (uuid_lib.UUID): ID of the image set

    Returns:
        List of Image objects associated with the image set in ascending order of slice index
    """
    return (
        session.query(Image)
        .filter_by(image_set_id=image_set_uuid)
        .order_by(Image.slice_index.asc())
        .all()
    )
