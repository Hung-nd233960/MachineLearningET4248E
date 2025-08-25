# pylint: disable=missing-function-docstring, missing-module-docstring, redefined-outer-name
# tests/image_evaluation_input_test.py
import pytest
import uuid as uuid_lib
from sqlalchemy.orm import Session
from medfabric.db.models import Region, ImageEvaluation
from medfabric.api.config import BASAL_CENTRAL_MAX, BASAL_CORTEX_MAX, CORONA_MAX
from medfabric.api.credentials import register_doctor
from medfabric.api.image_input import add_image
from medfabric.api.image_set_input import add_image_set
from medfabric.api.image_evaluation_input import (
    add_evaluate_image,
    region_score_requirements,
    validate_evaluation_scores,
    check_image_evaluation_exists,
)
from medfabric.api.sessions import create_session
from medfabric.api.errors import (
    UserNotFoundError,
    ImageNotFoundError,
    SessionNotFoundError,
    SessionInactiveError,
    SessionMismatchError,
    InvalidEvaluationError,
    EvaluationAlreadyExistsError,
)


@pytest.mark.parametrize(
    "region,scores",
    [
        # ✅ Success cases
        (
            Region.None_,
            dict.fromkeys(
                [
                    "basal_score_central_left",
                    "basal_score_central_right",
                    "basal_score_cortex_left",
                    "basal_score_cortex_right",
                    "corona_score_left",
                    "corona_score_right",
                ],
                None,
            ),
        ),
        (
            Region.BasalCentral,
            {
                "basal_score_central_left": 1,
                "basal_score_central_right": 2,
                "basal_score_cortex_left": None,
                "basal_score_cortex_right": None,
                "corona_score_left": None,
                "corona_score_right": None,
            },
        ),
        (
            Region.BasalCortex,
            {
                "basal_score_central_left": None,
                "basal_score_central_right": None,
                "basal_score_cortex_left": 1,
                "basal_score_cortex_right": 2,
                "corona_score_left": None,
                "corona_score_right": None,
            },
        ),
        (
            Region.CoronaRadiata,
            {
                "basal_score_central_left": None,
                "basal_score_central_right": None,
                "basal_score_cortex_left": None,
                "basal_score_cortex_right": None,
                "corona_score_left": 1,
                "corona_score_right": 2,
            },
        ),
    ],
)
def test_success_cases_region_enforcement(region, scores):
    # should not raise
    region_score_requirements(region, **scores)


@pytest.mark.parametrize(
    "region,scores",
    [
        # ❌ None_: forbidden present
        (
            Region.None_,
            {
                "basal_score_central_left": 1,  # forbidden
                "basal_score_central_right": None,
                "basal_score_cortex_left": None,
                "basal_score_cortex_right": None,
                "corona_score_left": None,
                "corona_score_right": None,
            },
        ),
        # ❌ BasalCentral: missing required
        (
            Region.BasalCentral,
            {
                "basal_score_central_left": 1,
                "basal_score_central_right": None,  # missing
                "basal_score_cortex_left": None,
                "basal_score_cortex_right": None,
                "corona_score_left": None,
                "corona_score_right": None,
            },
        ),
        # ❌ BasalCentral: forbidden present
        (
            Region.BasalCentral,
            {
                "basal_score_central_left": 1,
                "basal_score_central_right": 2,
                "basal_score_cortex_left": None,
                "basal_score_cortex_right": None,
                "corona_score_left": 9,  # forbidden
                "corona_score_right": None,
            },
        ),
        # ❌ BasalCortex: missing required
        (
            Region.BasalCortex,
            {
                "basal_score_central_left": None,
                "basal_score_central_right": None,
                "basal_score_cortex_left": None,  # missing
                "basal_score_cortex_right": 2,
                "corona_score_left": None,
                "corona_score_right": None,
            },
        ),
        # ❌ BasalCortex: forbidden present
        (
            Region.BasalCortex,
            {
                "basal_score_central_left": None,
                "basal_score_central_right": None,
                "basal_score_cortex_left": 1,
                "basal_score_cortex_right": 2,
                "corona_score_left": 9,  # forbidden
                "corona_score_right": None,
            },
        ),
        # ❌ CoronaRadiata: missing required
        (
            Region.CoronaRadiata,
            {
                "basal_score_central_left": None,
                "basal_score_central_right": None,
                "basal_score_cortex_left": None,
                "basal_score_cortex_right": None,
                "corona_score_left": 1,
                "corona_score_right": None,  # missing
            },
        ),
        # ❌ CoronaRadiata: forbidden present
        (
            Region.CoronaRadiata,
            {
                "basal_score_central_left": 7,  # forbidden
                "basal_score_central_right": None,
                "basal_score_cortex_left": None,
                "basal_score_cortex_right": None,
                "corona_score_left": 1,
                "corona_score_right": 2,
            },
        ),
    ],
)
def test_failure_cases_region_enforcement(region, scores):
    with pytest.raises(InvalidEvaluationError):
        region_score_requirements(region, **scores)


@pytest.mark.parametrize(
    "scores",
    [
        # ✅ Success cases
        {
            "basal_score_central_left": 0,
            "basal_score_central_right": BASAL_CENTRAL_MAX,
            "basal_score_cortex_left": 0,
            "basal_score_cortex_right": BASAL_CORTEX_MAX,
            "corona_score_left": 0,
            "corona_score_right": CORONA_MAX,
        },
        {
            "basal_score_central_left": None,
            "basal_score_central_right": None,
            "basal_score_cortex_left": None,
            "basal_score_cortex_right": None,
            "corona_score_left": None,
            "corona_score_right": None,
        },
        {
            "basal_score_central_left": int(BASAL_CENTRAL_MAX / 2),
            "basal_score_central_right": int(BASAL_CENTRAL_MAX / 2),
            "basal_score_cortex_left": int(BASAL_CORTEX_MAX / 2),
            "basal_score_cortex_right": int(BASAL_CORTEX_MAX / 2),
            "corona_score_left": int(CORONA_MAX / 2),
            "corona_score_right": int(CORONA_MAX / 2),
        },
        {
            "basal_score_central_left": 1,
            "basal_score_central_right": 2,
            "basal_score_cortex_left": 1,
            "basal_score_cortex_right": 2,
            "corona_score_left": 1,
            "corona_score_right": 2,
        },
        {
            "basal_score_central_left": 0,
            "basal_score_central_right": BASAL_CENTRAL_MAX - 1,
            "basal_score_cortex_left": 0,
            "basal_score_cortex_right": BASAL_CORTEX_MAX - 1,
            "corona_score_left": 0,
            "corona_score_right": CORONA_MAX - 1,
        },
    ],
)
def test_success_cases_score_validation(scores):
    # should not raise
    validate_evaluation_scores(**scores)


@pytest.mark.parametrize(
    "scores",
    [
        # ❌ Below minimum
        {
            "basal_score_central_left": -1,
            "basal_score_central_right": 2,
            "basal_score_cortex_left": 1,
            "basal_score_cortex_right": 1,
            "corona_score_left": 1,
            "corona_score_right": 1,
        },
        # ❌ Above maximum
        {
            "basal_score_central_left": 1,
            "basal_score_central_right": BASAL_CENTRAL_MAX + 1,
            "basal_score_cortex_left": 1,
            "basal_score_cortex_right": 1,
            "corona_score_left": 1,
            "corona_score_right": 1,
        },
        # ❌ Mixed invalid
        {
            "basal_score_central_left": 1,
            "basal_score_central_right": 2,
            "basal_score_cortex_left": -3,
            "basal_score_cortex_right": BASAL_CORTEX_MAX + 2,
            "corona_score_left": 1,
            "corona_score_right": 1,
        },
    ],
)
def test_failure_cases_score_validation(scores):
    with pytest.raises(InvalidEvaluationError):
        validate_evaluation_scores(**scores)


@pytest.fixture
def doctor(db_session: Session):
    """Create and return a test doctor."""
    return register_doctor(db_session, "doc1", "password123")


@pytest.fixture
def image_set(db_session: Session):
    """Create and return a test image set."""
    return add_image_set(db_session, "set1", 5)


@pytest.fixture
def session(db_session: Session, doctor):
    """Create and return a test session for the doctor."""
    return create_session(db_session, doctor.uuid)


@pytest.fixture
def image(db_session: Session, image_set):
    """Create and return a test image in the given image set."""
    return add_image(
        db_session, image_id="img1", image_set_id=image_set.image_set_id, slice_index=1
    )


def test_add_evaluate_image_success(db_session, doctor, image, session):
    evaluation = add_evaluate_image(
        db_session,
        doctor.uuid,
        image.image_id,
        session.session_id,
        region=Region.BasalCentral,
        basal_score_central_left=2,
        basal_score_central_right=3,
        basal_score_cortex_left=None,
        basal_score_cortex_right=None,
        corona_score_left=None,
        corona_score_right=None,
        notes="Test evaluation",
    )
    assert evaluation.doctor_id == doctor.uuid
    assert evaluation.image_id == image.image_id
    assert evaluation.session_id == session.session_id
    assert evaluation.region == Region.BasalCentral
    assert evaluation.basal_score_central_left == 2
    assert evaluation.basal_score_central_right == 3
    assert evaluation.basal_score_cortex_left is None
    assert evaluation.basal_score_cortex_right is None
    assert evaluation.corona_score_left is None
    assert evaluation.corona_score_right is None
    assert evaluation.notes == "Test evaluation"


def test_add_evaluate_image_doctor_not_found(db_session, image, session):
    fake_doctor_id = uuid_lib.uuid4()
    with pytest.raises(UserNotFoundError):
        add_evaluate_image(
            db_session,
            fake_doctor_id,
            image.image_id,
            session.session_id,
            region=Region.BasalCentral,
            basal_score_central_left=2,
            basal_score_central_right=3,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Test evaluation",
        )


def test_add_evaluate_image_image_not_found(db_session, doctor, session):
    fake_image_id = "nonexistent-image"
    with pytest.raises(ImageNotFoundError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            fake_image_id,
            session.session_id,
            region=Region.BasalCentral,
            basal_score_central_left=2,
            basal_score_central_right=3,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Test evaluation",
        )


def test_add_evaluate_image_session_not_found(db_session, doctor, image):
    fake_session_id = uuid_lib.uuid4()
    with pytest.raises(SessionNotFoundError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            image.image_id,
            fake_session_id,
            region=Region.BasalCentral,
            basal_score_central_left=2,
            basal_score_central_right=3,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Test evaluation",
        )


def test_add_evaluate_image_session_inactive(db_session, doctor, image):
    sess = create_session(db_session, doctor.uuid)
    # Manually set session to inactive
    sess.is_active = False
    db_session.commit()
    with pytest.raises(SessionInactiveError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            image.image_id,
            sess.session_id,
            region=Region.BasalCentral,
            basal_score_central_left=2,
            basal_score_central_right=3,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Test evaluation",
        )


def test_add_evaluate_image_session_mismatch(db_session, doctor, image):
    other_doctor = register_doctor(db_session, "doc2", "password456")
    sess = create_session(db_session, other_doctor.uuid)
    with pytest.raises(SessionMismatchError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            image.image_id,
            sess.session_id,
            region=Region.BasalCentral,
            basal_score_central_left=2,
            basal_score_central_right=3,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Test evaluation",
        )


def test_add_evaluate_image_invalid_region(db_session, doctor, image, session):
    with pytest.raises(InvalidEvaluationError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            image.image_id,
            session.session_id,
            region="InvalidRegion",  # Invalid region
            basal_score_central_left=2,
            basal_score_central_right=3,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Test evaluation",
        )


def test_add_evaluate_image_invalid_scores(db_session, doctor, image, session):
    with pytest.raises(InvalidEvaluationError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            image.image_id,
            session.session_id,
            region=Region.BasalCentral,
            basal_score_central_left=-1,  # Invalid score
            basal_score_central_right=3,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Test evaluation",
        )


def test_add_evaluate_image_duplicate_evaluation(db_session, doctor, image, session):
    add_evaluate_image(
        db_session,
        doctor.uuid,
        image.image_id,
        session.session_id,
        region=Region.BasalCentral,
        basal_score_central_left=2,
        basal_score_central_right=3,
        basal_score_cortex_left=None,
        basal_score_cortex_right=None,
        corona_score_left=None,
        corona_score_right=None,
        notes="First evaluation",
    )
    with pytest.raises(EvaluationAlreadyExistsError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            image.image_id,
            session.session_id,
            region=Region.BasalCentral,
            basal_score_central_left=1,
            basal_score_central_right=2,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Duplicate evaluation",
        )


def test_check_image_evaluation_exists(db_session, doctor, image, session):
    assert not check_image_evaluation_exists(
        db_session,
        doctor.uuid,
        image.image_id,
        session.session_id,
    )
    add_evaluate_image(
        db_session,
        doctor.uuid,
        image.image_id,
        session.session_id,
        region=Region.BasalCentral,
        basal_score_central_left=2,
        basal_score_central_right=3,
        basal_score_cortex_left=None,
        basal_score_cortex_right=None,
        corona_score_left=None,
        corona_score_right=None,
        notes="Test evaluation",
    )
    assert check_image_evaluation_exists(
        db_session,
        doctor.uuid,
        image.image_id,
        session.session_id,
    )


def test_add_evaluate_image_duplicate_does_not_break_existing(
    db_session, doctor, image, session
):
    add_evaluate_image(
        db_session,
        doctor.uuid,
        image.image_id,
        session.session_id,
        region=Region.BasalCentral,
        basal_score_central_left=2,
        basal_score_central_right=3,
        basal_score_cortex_left=None,
        basal_score_cortex_right=None,
        corona_score_left=None,
        corona_score_right=None,
        notes="First evaluation",
    )
    with pytest.raises(EvaluationAlreadyExistsError):
        add_evaluate_image(
            db_session,
            doctor.uuid,
            image.image_id,
            session.session_id,
            region=Region.BasalCentral,
            basal_score_central_left=1,
            basal_score_central_right=2,
            basal_score_cortex_left=None,
            basal_score_cortex_right=None,
            corona_score_left=None,
            corona_score_right=None,
            notes="Duplicate evaluation",
        )
    # Ensure the original evaluation still exists and is unchanged
    evaluations = (
        db_session.query(ImageEvaluation)
        .filter_by(
            doctor_id=doctor.uuid,
            image_id=image.image_id,
            session_id=session.session_id,
        )
        .all()
    )
    assert len(evaluations) == 1
    evaluation_ = evaluations[0]
    assert evaluation_.basal_score_central_left == 2
    assert evaluation_.basal_score_central_right == 3
    assert evaluation_.notes == "First evaluation"
