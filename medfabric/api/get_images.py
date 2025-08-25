# medfabric/api/get_images.py
from sqlalchemy.orm import Session
from medfabric.db.models import Image


def get_images_by_set_id(session: Session, image_set_id: str) -> list[Image]:
    """
    Retrieve all images associated with a given image set ID.

    Args:
        session (Session): SQLAlchemy DB session
        image_set_id (str): ID of the image set

    Returns:
        List of Image objects associated with the image set in ascending order of slice index
    """
    return (
        session.query(Image)
        .filter_by(image_set_id=image_set_id)
        .order_by(Image.slice_index.asc())
        .all()
    )
