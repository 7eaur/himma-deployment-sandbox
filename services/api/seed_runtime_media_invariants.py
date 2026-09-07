"""Normalize the DB-only media contract after all content overlays.

The student runtime consumes the ``db_runtime`` snapshot, so image-choice mapping
must be one-to-one there as well as in the UI.  Legacy imports sometimes marked
an ordinary illustration as if it were a choice, or left more than one image
mapped to the same option.  This pass keeps contextual illustrations contextual
and guarantees at most one choice image per current active option.
"""
from __future__ import annotations

from copy import deepcopy

from content_runtime import semantic_key
from db.database import SessionLocal
from db.models import ContentItem

VERSION = "HIMMA-MEDIA-OPTION-INVARIANTS-1.0"
IMAGE_ORDER = {"sequence", "memory_sequence", "path_sequence"}
IMAGE_CHOICE = {"choose_image", "listen_choose_image"}


def _interaction(item: ContentItem) -> str:
    return str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type)


def _match_order(step, semantic: str | None, used: set[int]) -> int | None:
    key = semantic_key(str(semantic or ""))
    if key:
        for option in step.options:
            order = int(option.order_index)
            if order in used:
                continue
            option_key = semantic_key(option.text)
            if option_key == key or option_key in key or key in option_key:
                return order
    return None


def _normalize_round(item: ContentItem, step, runtime_round: dict) -> tuple[dict, int]:
    interaction = _interaction(item)
    updated = deepcopy(runtime_round)
    assets = [deepcopy(value) for value in updated.get("assets", [])]
    valid_orders = {int(option.order_index) for option in step.options}
    used_orders: set[int] = set()
    changes = 0

    for asset in assets:
        if str(asset.get("asset_type") or "") != "image":
            continue
        usage = str(asset.get("usage") or "")
        may_be_option = usage == "choice" or (usage == "illustration" and interaction in IMAGE_ORDER)
        old_order = asset.get("option_order_index")
        new_order: int | None = None
        if may_be_option:
            try:
                candidate = int(old_order) if old_order is not None else None
            except (TypeError, ValueError):
                candidate = None
            if candidate in valid_orders and candidate not in used_orders:
                new_order = candidate
            else:
                new_order = _match_order(step, asset.get("semantic_text"), used_orders)
                if new_order is None and usage == "choice":
                    new_order = next((order for order in sorted(valid_orders) if order not in used_orders), None)
        if new_order is not None:
            used_orders.add(new_order)
        if old_order != new_order:
            asset["option_order_index"] = new_order
            changes += 1

    updated["assets"] = assets

    # A declared image-choice interaction is invalid if the current visible
    # choices cannot each resolve to exactly one image.  Media gaps remain an
    # explicit exception and are already surfaced as blocked content.
    has_declared_gap = bool(updated.get("media_gaps"))
    image_option_assets = [
        asset for asset in assets
        if str(asset.get("asset_type") or "") == "image" and asset.get("option_order_index") is not None
    ]
    if interaction in IMAGE_CHOICE and step.options and not has_declared_gap:
        mapped_orders = {int(asset["option_order_index"]) for asset in image_option_assets}
        if mapped_orders != valid_orders:
            raise RuntimeError(
                f"{(item.template_data or {}).get('canonical_id') or item.stable_key} "
                f"round {step.order_index}: image choices do not map 1:1 to active options "
                f"(options={sorted(valid_orders)}, images={sorted(mapped_orders)})"
            )
    return updated, changes


def run_seed() -> dict[str, int]:
    db = SessionLocal()
    changed_items = 0
    mapping_changes = 0
    try:
        for item in db.query(ContentItem).all():
            data = dict(item.template_data or {})
            runtime = deepcopy(data.get("db_runtime") or {})
            rounds = list(runtime.get("rounds") or [])
            by_order = {int(step.order_index): step for step in item.steps}
            new_rounds = []
            item_changed = False
            for value in rounds:
                order = int(value.get("order_index") or 0)
                step = by_order.get(order)
                if step is None:
                    new_rounds.append(value)
                    continue
                normalized, changes = _normalize_round(item, step, value)
                new_rounds.append(normalized)
                mapping_changes += changes
                item_changed = item_changed or changes > 0
            runtime["rounds"] = new_rounds
            if data.get("media_option_contract_version") != VERSION:
                data["media_option_contract_version"] = VERSION
                item_changed = True
            if runtime != data.get("db_runtime"):
                data["db_runtime"] = runtime
                item_changed = True
            if item_changed:
                item.template_data = data
                changed_items += 1
        db.commit()
        return {"changed_items": changed_items, "mapping_changes": mapping_changes}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Runtime media invariants applied: {run_seed()}")
