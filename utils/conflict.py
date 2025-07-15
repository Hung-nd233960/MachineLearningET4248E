from collections import defaultdict
from utils.models import Evaluation, Conflict, ConflictType, Region
from utils.models import ImageSet


def scan_and_update_image_conflicts(session):

    # Step 1: Group all evaluations by image
    evaluations = session.query(Evaluation).all()
    grouped = defaultdict(list)
    for e in evaluations:
        grouped[(e.image_set_id, e.image_id)].append(e)

    # Step 2: Build set of current valid conflicts from evaluation
    current_conflicts = set()
    for (iset_id, img_id), evals in grouped.items():
        if len(evals) < 2:
            continue

        regions = {e.region for e in evals}
        if len(regions) > 1:
            current_conflicts.add((iset_id, img_id, ConflictType.Classification))
        else:
            region = next(iter(regions))
            if region == Region.BasalGanglia:
                scores = {e.basal_score for e in evals}
                if len(scores) > 1:
                    current_conflicts.add((iset_id, img_id, ConflictType.Score))
            elif region == Region.CoronaRadiata:
                scores = {e.corona_score for e in evals}
                if len(scores) > 1:
                    current_conflicts.add((iset_id, img_id, ConflictType.Score))

    # Step 3: Get all existing conflicts
    existing = session.query(Conflict).all()
    existing_map = {(c.image_set_id, c.image_id, c.type): c for c in existing}

    # Step 4: Mark resolved or re-activated
    seen = set()

    for key, conflict in existing_map.items():
        if key in current_conflicts:
            if conflict.resolved:
                conflict.resolved = False  # was resolved, but back again
            seen.add(key)
        else:
            if not conflict.resolved:
                conflict.resolved = True  # no longer a real conflict

    # Step 5: Add new ones that aren't seen yet
    new_conflicts = current_conflicts - seen
    for iset_id, img_id, conflict_type in new_conflicts:
        session.add(
            Conflict(
                image_set_id=iset_id,
                image_id=img_id,
                type=conflict_type,
                resolved=False,
            )
        )

    session.commit()
    print(f"✅ Scan complete: {len(new_conflicts)} new, {len(existing)} reviewed.")


def scan_and_update_image_set_conflicts(session):

    # Step 1: Group evaluations per image set
    image_set_evals = defaultdict(list)

    # We assume low_quality and irrelevant_data will move to a new table (ImageSetEvaluation)
    image_set_level_evals = (
        session.query(
            Evaluation.image_set_id,
            Evaluation.doctor_id,
            Evaluation.low_quality,
            Evaluation.irrelevant_data,
        )
        .distinct()
        .all()
    )

    for iset_id, doctor_id, low_q, irrel in image_set_level_evals:
        image_set_evals[iset_id].append((low_q, irrel))

    current_conflicts = set()

    # Step 2: Look for disagreement per image_set
    for iset_id, flags in image_set_evals.items():
        if len(flags) < 2:
            continue
        low_qualities = {flag[0] for flag in flags}
        irrelevants = {flag[1] for flag in flags}

        if len(low_qualities) > 1:
            current_conflicts.add(
                (iset_id, None, ConflictType.Classification)
            )  # None means global
        elif len(irrelevants) > 1:
            current_conflicts.add((iset_id, None, ConflictType.Classification))

    # Step 3: Update conflict table (reuse logic pattern from image-level scan)
    existing = session.query(Conflict).filter(Conflict.image_id.is_(None)).all()
    existing_map = {(c.image_set_id, c.image_id, c.type): c for c in existing}
    seen = set()

    for key, conflict in existing_map.items():
        if key in current_conflicts:
            if conflict.resolved:
                conflict.resolved = False
            seen.add(key)
        else:
            if not conflict.resolved:
                conflict.resolved = True

    new_conflicts = current_conflicts - seen
    for iset_id, img_id, conflict_type in new_conflicts:
        session.add(
            Conflict(
                image_set_id=iset_id,
                image_id=None,
                type=conflict_type,
                resolved=False,
            )
        )

    session.commit()
    print(
        f"✅ Global scan complete: {len(new_conflicts)} new, {len(existing)} reviewed."
    )

def flag_conflicted_image_sets(session):
    """
    Set the 'conflicted' flag on ImageSet table for any set that has unresolved conflicts.
    """

    # Get set of image_set_ids that are involved in unresolved conflicts
    active_conflict_set_ids = (
        session.query(Conflict.image_set_id).filter_by(resolved=False).distinct().all()
    )
    active_set_ids = {sid for (sid,) in active_conflict_set_ids}

    # Get all image_set_ids to update
    all_set_ids = session.query(ImageSet.image_set_id).all()

    for (set_id,) in all_set_ids:
        session.query(ImageSet).filter_by(image_set_id=set_id).update(
            {"conflicted": set_id in active_set_ids}
        )

    session.commit()
    print(f"🚩 Updated conflict flags for {len(all_set_ids)} image sets.")
