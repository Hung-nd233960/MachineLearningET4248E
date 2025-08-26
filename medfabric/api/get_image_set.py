# medfabric/api/get_image_set.py
from typing import Optional
import uuid as uuid_lib
from sqlalchemy.orm import Session
from medfabric.db.models import ImageSet
from medfabric.api.errors import ImageSetNotFoundError, InvalidImageSetPathError


def get_image_set_with_validation(
    session: Session, image_set_uuid: uuid_lib.UUID
) -> Optional[ImageSet]:
    """
    Retrieve an image set by its UUID.

    Args:
        session (Session): SQLAlchemy DB session
        image_set_uuid (str): UUID of the image set to retrieve

    Returns:
        ImageSet if found, None otherwise
    """
    image_set = (
        session.query(ImageSet).filter_by(image_set_uuid=image_set_uuid).one_or_none()
    )
    if image_set is None:
        raise ImageSetNotFoundError(
            f"Image set with UUID '{image_set_uuid}' not found."
        )
    if image_set.folder_path is None:
        raise InvalidImageSetPathError(
            f"Image set with UUID '{image_set_uuid}' has an invalid or non-existent folder path."
        )
    return image_set
