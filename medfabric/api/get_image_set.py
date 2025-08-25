# medfabric/api/get_image_set.py
from typing import Optional
from sqlalchemy.orm import Session
from medfabric.db.models import ImageSet
from medfabric.api.errors import ImageSetNotFoundError, InvalidImageSetPathError


def get_image_set_with_validation(
    session: Session, image_set_id: str
) -> Optional[ImageSet]:
    """
    Retrieve an image set by its ID.

    Args:
        session (Session): SQLAlchemy DB session
        image_set_id (str): ID of the image set to retrieve

    Returns:
        ImageSet if found, None otherwise
    """
    image_set = (
        session.query(ImageSet).filter_by(image_set_id=image_set_id).one_or_none()
    )
    if image_set is None:
        raise ImageSetNotFoundError(f"Image set with ID '{image_set_id}' not found.")
    if image_set.folder_path is None:
        raise InvalidImageSetPathError(
            f"Image set with ID '{image_set_id}' has an invalid or non-existent folder path."
        )
    return image_set
