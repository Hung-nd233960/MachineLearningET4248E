# pylint: disable=missing-function-docstring,missing-module-docstring, unused-argument
# tests/image_input_test.py
from uuid import UUID
import pytest
from sqlalchemy.orm import Session
from medfabric.api.image_input import (
    add_image,
    check_image_exists_by_uuid,
    check_image_exists_by_set_and_index,
)
from medfabric.api.image_set_input import add_image_set
from medfabric.db.models import ImageSet


from medfabric.api.errors import (
    ImageAlreadyExistsError,
    InvalidImageError,
    ImageSetNotFoundError,
)


@pytest.fixture
def image_set(db_session: Session) -> ImageSet:
    """Create an image set with 3 slices."""
    img_set = add_image_set(
        db_session, "set1", folder_path="/path/to/set1", num_images=3
    )
    return img_set


def test_add_image_success(db_session: Session, image_set: ImageSet):
    img = add_image(db_session, "img1", image_set.uuid, 0)
    assert img.image_id == "img1"
    assert img.slice_index == 0
    assert check_image_exists_by_uuid(db_session, img.uuid)
    assert check_image_exists_by_set_and_index(db_session, image_set.uuid, 0)


def test_add_image_duplicate_id(db_session, image_set):
    add_image(db_session, "img1", image_set.uuid, 0)
    with pytest.raises(ImageAlreadyExistsError):
        add_image(db_session, "img1", image_set.uuid, 1)  # same ID, different slice


def test_add_image_duplicate_slice_index(db_session, image_set):
    add_image(db_session, "img1", image_set.uuid, 0)
    with pytest.raises(ImageAlreadyExistsError):
        add_image(db_session, "img2", image_set.uuid, 0)  # different ID, same slice


def test_add_image_invalid_id(db_session, image_set):
    with pytest.raises(InvalidImageError):
        add_image(db_session, "", image_set.uuid, 0)


def test_add_image_negative_slice_index(db_session, image_set):
    with pytest.raises(InvalidImageError):
        add_image(db_session, "img1", image_set.uuid, -1)


def test_add_image_slice_index_too_large(db_session, image_set):
    with pytest.raises(InvalidImageError):
        add_image(db_session, "img1", image_set.uuid, 99)


def test_add_image_to_nonexistent_set(db_session, image_set):
    with pytest.raises(ImageSetNotFoundError):
        add_image(db_session, "img1", UUID("123e4567-e89b-12d3-a456-426614174000"), 0)
