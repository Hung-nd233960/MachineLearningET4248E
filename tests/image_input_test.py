# pylint: disable=missing-function-docstring,missing-module-docstring, unused-argument
# tests/image_input_test.py
import pytest
from medfabric.api.image_input import (
    add_image,
    check_image_exists_by_id,
    check_image_exists_by_set_and_index,
)
from medfabric.db.models import ImageSet
from medfabric.api.errors import (
    ImageAlreadyExistsError,
    InvalidImageError,
    ImageSetNotFoundError,
)


@pytest.fixture
def image_set(db_session):
    """Create an image set with 3 slices."""
    img_set = ImageSet(image_set_id="set1", num_images=3)
    db_session.add(img_set)
    db_session.commit()
    return img_set


def test_add_image_success(db_session, image_set):
    img = add_image(db_session, "img1", "set1", 0)
    assert img.image_id == "img1"
    assert img.slice_index == 0
    assert check_image_exists_by_id(db_session, "img1")
    assert check_image_exists_by_set_and_index(db_session, "set1", 0)


def test_add_image_duplicate_id(db_session, image_set):
    add_image(db_session, "img1", "set1", 0)
    with pytest.raises(ImageAlreadyExistsError):
        add_image(db_session, "img1", "set1", 1)  # same ID, different slice


def test_add_image_duplicate_slice_index(db_session, image_set):
    add_image(db_session, "img1", "set1", 0)
    with pytest.raises(ImageAlreadyExistsError):
        add_image(db_session, "img2", "set1", 0)  # different ID, same slice


def test_add_image_invalid_id(db_session, image_set):
    with pytest.raises(InvalidImageError):
        add_image(db_session, "", "set1", 0)


def test_add_image_negative_slice_index(db_session, image_set):
    with pytest.raises(InvalidImageError):
        add_image(db_session, "img1", "set1", -1)


def test_add_image_slice_index_too_large(db_session, image_set):
    with pytest.raises(InvalidImageError):
        add_image(db_session, "img1", "set1", 99)


def test_add_image_to_nonexistent_set(db_session, image_set):
    with pytest.raises(ImageSetNotFoundError):
        add_image(db_session, "img1", "does_not_exist", 0)
