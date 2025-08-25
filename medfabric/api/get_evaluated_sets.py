import uuid as uuid_lib
from typing import List
from sqlalchemy import select, union
from sqlalchemy.orm import Session
from medfabric.db.models import Image, ImageEvaluation, ImageSetEvaluation


def get_doctor_image_sets(session: Session, doctor_id: uuid_lib.UUID) -> List[str]:
    """
    Given a doctor_id, return all unique image_set_ids that doctor has annotated.
    Includes both rejected sets (image_set_evaluations) and valid sets (image_evaluations).
    """
    # From image_evaluations → Image → ImageSet
    q1 = (
        select(Image.image_set_id)
        .join(ImageEvaluation, ImageEvaluation.image_id == Image.image_id)
        .where(ImageEvaluation.doctor_id == doctor_id)
        .distinct()
    )

    # From image_set_evaluations directly
    q2 = (
        select(ImageSetEvaluation.image_set_id)
        .where(ImageSetEvaluation.doctor_id == doctor_id)
        .distinct()
    )

    # Union both queries
    union_q = union(q1, q2).subquery()

    # Return unique IDs
    return [row[0] for row in session.execute(select(union_q.c.image_set_id)).all()]
