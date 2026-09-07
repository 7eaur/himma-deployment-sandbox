"""Reconcile the current student choice contract without deleting history.

Why this exists
---------------
Older maintenance overlays were intentionally additive: they could add missing
approved distractors but they did not remove extra rows from ``content_options``.
After several content revisions, those historical rows could remain visible and
produce duplicated/overlapping choices even though the latest content contract
was correct.

A ContentOption may already be referenced by an AttemptResponse, so deleting it
would damage the audit trail.  The 0011 migration therefore gives options an
``is_active`` lifecycle.  This seed makes the latest approved presentation exact:
current rows are active; superseded rows are retired but kept for historical
responses and reports.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from db.database import SessionLocal
from db.models import ContentItem, ContentOption
import seed_student_choice_corrections as approved

VERSION = "HIMMA-ACTIVE-OPTIONS-1.0"
ORDER_INTERACTIONS = {"sequence", "memory_sequence", "path_sequence", "build_word"}


def _visible_key(value: str) -> str:
    """Compare what the learner actually sees; keep pedagogical diacritics."""
    normalized = unicodedata.normalize("NFKC", value or "").replace("ـ", "")
    normalized = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]", "", normalized)
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def _find_item(db, canonical: str) -> ContentItem | None:
    direct = db.query(ContentItem).filter(ContentItem.stable_key == canonical).first()
    if direct is not None:
        return direct
    for item in db.query(ContentItem).all():
        if str((item.template_data or {}).get("canonical_id") or "") == canonical:
            return item
    return None


def _all_step_options(db, step_id: int) -> list[ContentOption]:
    return (
        db.query(ContentOption)
        .filter(ContentOption.step_id == step_id)
        .order_by(ContentOption.order_index, ContentOption.id)
        .all()
    )


def _desired_from_pool(step, pool: list[str], total: int) -> list[str]:
    rows = [row for row in step.options if row.is_active]
    if not rows:
        raise RuntimeError(f"Step {step.id} has no current option to reconcile")
    correct = next((row for row in rows if row.is_correct), rows[0])
    correct_key = _visible_key(correct.text)
    distractors = [value for value in pool if _visible_key(value) != correct_key]
    if len(distractors) < total - 1:
        raise RuntimeError(f"Step {step.id} has too few approved distractors")
    offset = max(0, int(step.order_index) - 1) % len(distractors)
    rotated = distractors[offset:] + distractors[:offset]
    return [correct.text, *rotated[: total - 1]]


def _reconcile_exact(db, step, desired_texts: Iterable[str]) -> tuple[int, int]:
    desired = [str(value) for value in desired_texts]
    rows = _all_step_options(db, step.id)
    active_correct_keys = {
        _visible_key(row.text)
        for row in rows
        if row.is_active and row.is_correct
    }
    used_ids: set[int] = set()
    activated = 0

    for index, text in enumerate(desired, start=1):
        key = _visible_key(text)
        candidates = [row for row in rows if row.id not in used_ids and _visible_key(row.text) == key]
        candidate = next((row for row in candidates if row.is_active), None) or (candidates[0] if candidates else None)
        if candidate is None:
            candidate = ContentOption(
                step_id=step.id,
                text=text,
                is_correct=key in active_correct_keys,
                order_index=index,
                is_active=True,
            )
            db.add(candidate)
            db.flush()
            rows.append(candidate)
            activated += 1
        else:
            if not candidate.is_active:
                activated += 1
            candidate.is_active = True
            candidate.text = text
            candidate.order_index = index
            # Preserve the current academic key; presentation repair must never
            # invent a new answer.  Newly-created rows are distractors unless a
            # matching current correct option existed.
            candidate.is_correct = key in active_correct_keys
        used_ids.add(int(candidate.id))

    retired = 0
    for row in rows:
        if row.id not in used_ids and row.is_active:
            row.is_active = False
            retired += 1
    return activated, retired


def _reconcile_known_contracts(db) -> tuple[int, int]:
    activated = retired = 0

    # These are the latest explicit presentation repairs already approved in
    # seed_student_choice_corrections.  We make their cardinality exact instead
    # of the former "at least N" behavior.
    pools: list[tuple[str, list[str], int]] = [
        (approved.LETTER_FORM_ITEM, approved.LETTER_FORM_POOL, 4),
        (approved.L1_WORD_IMAGE_ITEM, approved.L1_WORD_IMAGE_POOL, 3),
        (approved.L2_WORD_IMAGE_ITEM, approved.L2_WORD_IMAGE_POOL, 3),
        (approved.POST_LETTER_ELEMENT_ITEM, approved.POST_LETTER_ELEMENT_POOL, 3),
        (approved.POST_WORD_ELEMENT_ITEM, approved.POST_WORD_ELEMENT_POOL, 3),
    ]
    for canonical, pool, total in pools:
        item = _find_item(db, canonical)
        if item is None:
            continue
        for step in sorted(item.steps, key=lambda value: value.order_index):
            desired = _desired_from_pool(step, pool, total)
            add, remove = _reconcile_exact(db, step, desired)
            activated += add
            retired += remove

    for canonical, rounds in approved.L3_APPROVED_ROUND_CHOICES.items():
        item = _find_item(db, canonical)
        if item is None:
            continue
        steps = sorted(item.steps, key=lambda value: value.order_index)
        if len(steps) != len(rounds):
            raise RuntimeError(f"{canonical}: round count changed unexpectedly")
        for step, desired in zip(steps, rounds, strict=True):
            add, remove = _reconcile_exact(db, step, desired)
            activated += add
            retired += remove

    segmentation = _find_item(db, "L3-REIN-01")
    if segmentation is not None:
        steps = sorted(segmentation.steps, key=lambda value: value.order_index)
        if len(steps) != len(approved.L3_SEGMENTATION_ROUNDS):
            raise RuntimeError("L3-REIN-01: round count changed unexpectedly")
        for step, desired in zip(steps, approved.L3_SEGMENTATION_ROUNDS, strict=True):
            add, remove = _reconcile_exact(db, step, desired)
            activated += add
            retired += remove

    return activated, retired


def _retire_accidental_visible_duplicates(db) -> int:
    """Remove duplicate cards, but never collapse meaningful ordered repeats.

    ``بَ / بِ / بُ`` remain distinct because diacritics are preserved by
    ``_visible_key``.  Ordered/build-word activities may intentionally repeat the
    same letter (e.g. باب), so semantic deduplication is not applied to them.
    """
    retired = 0
    for item in db.query(ContentItem).all():
        interaction = str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type)
        if interaction in ORDER_INTERACTIONS:
            continue
        for step in item.steps:
            rows = [row for row in _all_step_options(db, step.id) if row.is_active]
            groups: dict[str, list[ContentOption]] = {}
            for row in rows:
                groups.setdefault(_visible_key(row.text), []).append(row)
            for key, duplicates in groups.items():
                if not key or len(duplicates) < 2:
                    continue
                keep = next((row for row in duplicates if row.is_correct), duplicates[0])
                for row in duplicates:
                    if row.id == keep.id:
                        continue
                    row.is_active = False
                    retired += 1
            active = [row for row in rows if row.is_active]
            for index, row in enumerate(sorted(active, key=lambda value: (value.order_index, value.id)), start=1):
                row.order_index = index
    return retired


def _mark_contract(db) -> int:
    marked = 0
    for item in db.query(ContentItem).all():
        data = dict(item.template_data or {})
        if data.get("active_option_contract_version") != VERSION:
            data["active_option_contract_version"] = VERSION
            item.template_data = data
            marked += 1
    return marked


def run_seed() -> dict[str, int]:
    db = SessionLocal()
    try:
        activated, retired = _reconcile_known_contracts(db)
        retired += _retire_accidental_visible_duplicates(db)
        marked = _mark_contract(db)
        db.commit()
        return {"activated": activated, "retired": retired, "marked_items": marked}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Active option contract reconciled: {run_seed()}")
