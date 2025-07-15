from dataclasses import dataclass
from typing import Optional, List
import streamlit as st
import pandas as pd
from utils.models import (
    ImageSetEvaluation,
    Patient,
    Region,
    Image,
    Evaluation,
    ImageSet,
)  # reuse your Enum


@dataclass
class ImageEvaluationSession:
    image_id: str
    image_path: str
    region: Optional[str]
    score: Optional[int]
    slice_index: int = 0


@dataclass
class ImageSetEvaluationSession:
    image_set_id: str
    patient_id: str
    num_images: int
    folder_path: str
    low_quality: bool
    irrelevant_data: bool
    conflicted: bool
    images: List[ImageEvaluationSession]
    current_index: int = 0
    patient_diagnosis: pd.DataFrame = None


def prepare_image_evaluation(
    session, doctor_id: str, image_set_id: str, image_id: str, **kwargs
) -> Optional[ImageEvaluationSession]:
    """
    Retrieve a specific image evaluation made by a doctor.

    Args:
        session: SQLAlchemy session object.
        doctor_id: UUID of the doctor.
        image_set_id: ID of the image set.
        image_id: ID of the image (filename).
        **kwargs: Optional 'parent_path' to construct full image path.

    Returns:
        ImageEvaluation object or None if no evaluation found.
    """
    evaluation = (
        session.query(Evaluation)
        .filter_by(doctor_id=doctor_id, image_set_id=image_set_id, image_id=image_id)
        .first()
    )

    if evaluation is None:
        return None

    image = (
        session.query(Image)
        .filter_by(image_set_id=image_set_id, image_id=image_id)
        .first()
    )

    if image is None:
        raise ValueError(f"Image {image_id} not found in set {image_set_id}.")

    parent_path = kwargs.get("parent_path")
    image_path = f"{parent_path}/{image.image_id}" if parent_path else None

    if evaluation.region == Region.None_:
        score = None
    elif evaluation.region == Region.BasalGanglia:
        score = evaluation.basal_score
    elif evaluation.region == Region.CoronaRadiata:
        score = evaluation.corona_score
    else:
        score = None
    return ImageEvaluationSession(
        image_id=image.image_id,
        slice_index=image.slice_index,
        image_path=image_path,
        region=evaluation.region.value if evaluation.region != Region.None_ else None,
        score=score,
    )


def prepare_image_set_evaluation(
    session, doctor_id: str, image_set_id: str
) -> Optional[ImageSetEvaluationSession]:
    img_set = session.query(ImageSet).filter_by(image_set_id=image_set_id).first()
    if not img_set:
        return None
    folder_path = img_set.folder_path
    patient_id = img_set.patient_id
    conflicted = img_set.conflicted
    num_images = img_set.num_images

    patient_diagnosis = patient_diagnosis_to_df(
        session.query(Patient).filter_by(patient_id=patient_id).first()
    )
    # Step 2: Get image set evaluation
    set_eval = (
        session.query(ImageSetEvaluation)
        .filter_by(doctor_id=doctor_id, image_set_id=image_set_id)
        .first()
    )

    irrelevant = set_eval.is_irrelevant if set_eval else False
    low_quality = set_eval.is_low_quality if set_eval else False

    # Step 3: Get all images for this image set
    images = session.query(Image).filter_by(image_set_id=image_set_id).all()

    # Step 4: Construct image-level evaluations
    image_evaluations = []

    for image in images:
        eval_session = prepare_image_evaluation(
            session,
            doctor_id,
            image_set_id,
            image.image_id,
            parent_path=img_set.folder_path,
        )
        if eval_session:
            image_evaluations.append(eval_session)
        else:
            # If no evaluation exists, create a default one
            image_evaluations.append(
                ImageEvaluationSession(
                    image_id=image.image_id,
                    slice_index=image.slice_index,  # Default value, adjust as needed
                    image_path=(
                        img_set.folder_path + "/" + image.image_id
                        if img_set.folder_path
                        else None
                    ),
                    region=None,  # Default region
                    score=None,  # Default score
                )
            )
    # Step 6: Return full evaluation object
    return ImageSetEvaluationSession(
        image_set_id=image_set_id,
        patient_id=patient_id,
        num_images=num_images,
        conflicted=conflicted,
        irrelevant_data=irrelevant,
        low_quality=low_quality,
        images=image_evaluations,
        patient_diagnosis=patient_diagnosis,
        folder_path=folder_path,
    )


def patient_diagnosis_to_df(patient_obj) -> pd.DataFrame:
    if patient_obj is None:
        return pd.DataFrame()

    # List of all diagnostic attributes
    attrs = [
        "ICH",
        "IPH",
        "IVH",
        "SDH",
        "EDH",
        "SAH",
        "BleedLocation-Left",
        "BleedLocation-Right",
        "ChronicBleed",
        "Fracture",
        "CalvarialFracture",
        "OtherFracture",
        "MassEffect",
        "MidlineShift",
    ]

    # Prepare a dictionary to hold row-wise data
    data = {attr: [] for attr in attrs}

    for attr in attrs:
        for r in [1, 2, 3]:
            value = getattr(patient_obj, f"R{r}:{attr}")
            data[attr].append(value)

    # Build DataFrame: index = attribute, columns = R1, R2, R3
    df = pd.DataFrame(data).T
    df.columns = ["R1", "R2", "R3"]
    df.index.name = "Attribute"

    return df.reset_index()
