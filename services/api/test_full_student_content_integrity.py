"""Exhaustive student-content runtime integrity gate.

This scans every seeded pretest, posttest, core and reinforcement round. The gate
protects presentation separation, option cardinality, DB-only runtime metadata and
media mapping. It intentionally reports all discovered violations in one failure.
"""
from __future__ import annotations

import re
import unicodedata

import seed_all
from assessment_view import _clean_payload
from content_runtime import canonical_id, canonical_interaction, media_gaps, presentation_data, step_assets
from db.database import SessionLocal
from db.models import ContentItem

SINGLE = {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}
MULTI = {"choose_many", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}
READ = {"read_aloud", "timed_read_aloud"}
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}
IMAGE_CHOICE = {"choose_image", "listen_choose_image"}
SERIALIZED_MARKERS = ("الخيارات:", "الصور:", "طريقة الإجابة:", "الإجابة الصحيحة:")


def _display_key(value: str) -> str:
    """Normalize only invisible formatting; preserve pedagogical distinctions."""
    value = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", value).strip()


def _issue(errors: list[str], canonical: str, step_no: int | None, message: str) -> None:
    prefix = canonical if step_no is None else f"{canonical}/R{step_no:02d}"
    errors.append(f"{prefix}: {message}")


def test_complete_student_runtime_has_no_presentation_or_choice_overlap():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125
    assert result["db_runtime_items"] == 125

    db = SessionLocal()
    errors: list[str] = []
    try:
        items = db.query(ContentItem).order_by(ContentItem.kind, ContentItem.level_id, ContentItem.order_index).all()
        counts = {
            "pretest_question": 0,
            "posttest_question": 0,
            "core_activity": 0,
            "reinforcement_activity": 0,
        }
        order_groups: dict[tuple[str, int], list[int]] = {}

        for item in items:
            canonical = canonical_id(item)
            interaction = canonical_interaction(item)
            counts[item.kind] = counts.get(item.kind, 0) + 1
            order_groups.setdefault((item.kind, int(item.level_id)), []).append(int(item.order_index))
            runtime = (item.template_data or {}).get("db_runtime") or {}
            if runtime.get("version") != "HIMMA-DB-RUNTIME-1.0":
                _issue(errors, canonical, None, "missing DB runtime snapshot")
            if not item.steps:
                _issue(errors, canonical, None, "item has no executable rounds")
                continue

            if item.kind == "pretest_question":
                experience = (item.template_data or {}).get("pretest_experience") or {}
                if not experience:
                    _issue(errors, canonical, None, "missing pretest_experience")
            elif item.kind == "posttest_question":
                experience = (item.template_data or {}).get("posttest_experience") or {}
                if not experience:
                    _issue(errors, canonical, None, "missing posttest_experience")
            else:
                experience = (item.template_data or {}).get("learning_experience") or {}
                rounds = experience.get("rounds") or []
                if len(rounds) != len(item.steps):
                    _issue(errors, canonical, None, f"learning presentation rounds={len(rounds)} but DB steps={len(item.steps)}")

            for expected_order, step in enumerate(sorted(item.steps, key=lambda value: value.order_index), start=1):
                if int(step.order_index) != expected_order:
                    _issue(errors, canonical, int(step.order_index), f"non-consecutive round order; expected {expected_order}")
                options = sorted(step.options, key=lambda value: value.order_index)
                texts = [str(option.text).strip() for option in options]
                normalized = [_display_key(text) for text in texts]
                correct = [option for option in options if option.is_correct]
                assets = step_assets(item, step)
                gaps = media_gaps(item, step)
                audio_assets = [asset for asset in assets if asset["asset_type"] == "audio"]
                image_assets = [asset for asset in assets if asset["asset_type"] == "image"]

                if interaction in SINGLE:
                    if not 2 <= len(options) <= 5:
                        _issue(errors, canonical, step.order_index, f"single-choice option count is {len(options)}")
                    if len(correct) != 1:
                        _issue(errors, canonical, step.order_index, f"single-choice correct option count is {len(correct)}")
                    if len(set(normalized)) != len(normalized):
                        _issue(errors, canonical, step.order_index, f"duplicate visible choice text: {texts}")
                elif interaction in MULTI:
                    if not 2 <= len(options) <= 6:
                        _issue(errors, canonical, step.order_index, f"multi-choice option count is {len(options)}")
                    if not 1 <= len(correct) < len(options):
                        _issue(errors, canonical, step.order_index, f"multi-choice correct count is {len(correct)} of {len(options)}")
                    if len(set(normalized)) != len(normalized):
                        _issue(errors, canonical, step.order_index, f"duplicate visible multi-choice text: {texts}")
                elif interaction in ORDER:
                    if not 2 <= len(options) <= 8:
                        _issue(errors, canonical, step.order_index, f"ordered-task option count is {len(options)}")
                elif interaction in READ:
                    if options:
                        _issue(errors, canonical, step.order_index, "read-aloud round unexpectedly has choice options")
                    if not str(step.expected_reading_text or "").strip():
                        _issue(errors, canonical, step.order_index, "read-aloud round has no expected reading text")

                if interaction in LISTEN and not audio_assets and not gaps:
                    _issue(errors, canonical, step.order_index, "listening round has no audio and no declared media gap")

                if interaction in IMAGE_CHOICE and not gaps:
                    mapped = [asset for asset in image_assets if asset.get("option_id") is not None]
                    mapped_ids = [asset["option_id"] for asset in mapped]
                    if len(mapped) != len(options):
                        _issue(errors, canonical, step.order_index, f"image choices mapped={len(mapped)} but options={len(options)}")
                    if len(set(mapped_ids)) != len(mapped_ids):
                        _issue(errors, canonical, step.order_index, "two image assets map to the same option")

                presentation = presentation_data(item, step)
                if item.kind in {"core_activity", "reinforcement_activity"}:
                    for field in ("question_text", "instruction_text", "encouragement", "hint", "stimulus_text"):
                        if field not in presentation:
                            _issue(errors, canonical, step.order_index, f"learning presentation missing field {field}")
                    stimulus = str(presentation.get("stimulus_text") or "")
                else:
                    for field in ("question_text", "instruction_text", "encouragement", "skill", "interaction_type"):
                        if not str(presentation.get(field) or "").strip():
                            _issue(errors, canonical, step.order_index, f"assessment presentation missing field {field}")
                    stimulus = str((presentation.get("stimulus") or {}).get("text") or "")

                if any(marker in stimulus for marker in SERIALIZED_MARKERS):
                    _issue(errors, canonical, step.order_index, f"stimulus leaks serialized source content: {stimulus!r}")

                if item.kind in {"pretest_question", "posttest_question"}:
                    payload = _clean_payload(item, step)
                    raw = str(payload)
                    if "prompt_text" in raw or "template_data" in raw:
                        _issue(errors, canonical, step.order_index, "student assessment payload exposes legacy raw fields")
                    required = int(payload["steps"][0]["required_selection_count"])
                    if interaction in SINGLE and required != 1:
                        _issue(errors, canonical, step.order_index, f"single-choice required_selection_count={required}")
                    if interaction in MULTI and required != len(correct):
                        _issue(errors, canonical, step.order_index, f"multi-choice required_selection_count={required}, correct={len(correct)}")

        if counts != {"pretest_question": 30, "posttest_question": 30, "core_activity": 30, "reinforcement_activity": 35}:
            errors.append(f"kind counts mismatch: {counts}")

        for level in (1, 2, 3):
            core_orders = sorted(order_groups.get(("core_activity", level), []))
            if core_orders != list(range(1, 11)):
                errors.append(f"level {level} core orders invalid: {core_orders}")
            rein_orders = order_groups.get(("reinforcement_activity", level), [])
            if len(rein_orders) != len(set(rein_orders)):
                errors.append(f"level {level} reinforcement order indices contain duplicates: {sorted(rein_orders)}")

        assert not errors, "Full student-content integrity violations:\n- " + "\n- ".join(errors)
    finally:
        db.close()
