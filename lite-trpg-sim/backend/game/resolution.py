"""Helpers for the engine's unified action-resolution payload.

The long-term goal is for checks, encounters, utility use, damage, and other
system results to share a single explainable structure. The frontend only needs
to learn one payload shape to render outcomes consistently.
"""

from __future__ import annotations

from typing import Any

_RESOURCE_LABELS = {
    "hp": "生命",
    "corruption": "腐化",
    "doom": "末日进度",
    "shillings": "先令",
}


def build_resolution(
    *,
    kind: str,
    label: str,
    success: bool | None = None,
    stat: str | None = None,
    dc: int | None = None,
    roll: int | None = None,
    modifier: int | None = None,
    total: int | None = None,
    tags: list[str] | None = None,
    breakdown: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create the canonical resolution payload skeleton."""
    return {
        "kind": kind,
        "label": label,
        "success": success,
        "stat": stat,
        "dc": dc,
        "roll": roll,
        "modifier": modifier,
        "total": total,
        "tags": list(tags or []),
        "breakdown": list(breakdown or []),
        "amount": None,
        "applied": None,
        "mitigated": None,
        "damage_type": None,
        "target": None,
        "target_label": None,
        "penetration": None,
        "resistance_flat": None,
        "resistance_percent": None,
        "opponent_label": None,
        "opponent_roll": None,
        "opponent_modifier": None,
        "opponent_total": None,
        "effects": [],
    }


def ensure_resolution(resolution: dict[str, Any] | None) -> dict[str, Any] | None:
    """Backfill optional fields so downstream renderers can rely on them."""
    if not isinstance(resolution, dict):
        return None
    resolution.setdefault("kind", "action")
    resolution.setdefault("label", "")
    resolution.setdefault("success", None)
    resolution.setdefault("stat", None)
    resolution.setdefault("dc", None)
    resolution.setdefault("roll", None)
    resolution.setdefault("modifier", None)
    resolution.setdefault("total", None)
    resolution.setdefault("tags", [])
    resolution.setdefault("breakdown", [])
    resolution.setdefault("amount", None)
    resolution.setdefault("applied", None)
    resolution.setdefault("mitigated", None)
    resolution.setdefault("damage_type", None)
    resolution.setdefault("target", None)
    resolution.setdefault("target_label", None)
    resolution.setdefault("penetration", None)
    resolution.setdefault("resistance_flat", None)
    resolution.setdefault("resistance_percent", None)
    resolution.setdefault("opponent_label", None)
    resolution.setdefault("opponent_roll", None)
    resolution.setdefault("opponent_modifier", None)
    resolution.setdefault("opponent_total", None)
    resolution.setdefault("effects", [])
    return resolution


def push_resolution_effect(resolution: dict[str, Any] | None, payload: dict[str, Any]) -> None:
    """Append one normalized effect entry to a resolution payload."""
    active = ensure_resolution(resolution)
    if active is None:
        return
    active["effects"].append(payload)


def add_resource_effect(resolution: dict[str, Any] | None, resource: str, delta: int, source: str) -> None:
    """Record a resource delta such as HP, corruption, or currency."""
    if int(delta) == 0:
        return
    push_resolution_effect(
        resolution,
        {
            "kind": "resource",
            "resource": resource,
            "label": _RESOURCE_LABELS.get(resource, resource),
            "delta": int(delta),
            "source": source,
        },
    )


def add_status_effect(
    resolution: dict[str, Any] | None,
    *,
    mode: str,
    status_id: str,
    name: str,
    source: str,
) -> None:
    """Record a status add/remove event."""
    push_resolution_effect(
        resolution,
        {
            "kind": "status",
            "mode": mode,
            "status_id": status_id,
            "name": name,
            "source": source,
        },
    )


def add_item_effect(
    resolution: dict[str, Any] | None,
    *,
    mode: str,
    item_id: str,
    name: str,
    qty: int,
    source: str,
) -> None:
    """Record item gain, loss, or spend events."""
    push_resolution_effect(
        resolution,
        {
            "kind": "item",
            "mode": mode,
            "item_id": item_id,
            "name": name,
            "qty": int(qty),
            "source": source,
        },
    )


def add_flag_effect(resolution: dict[str, Any] | None, *, flag: str, value: bool, source: str) -> None:
    """Record a progress-flag mutation."""
    push_resolution_effect(
        resolution,
        {
            "kind": "flag",
            "flag": flag,
            "value": bool(value),
            "source": source,
        },
    )


def add_encounter_effect(
    resolution: dict[str, Any] | None,
    *,
    mode: str,
    title: str,
    delta: int | None = None,
    label: str | None = None,
    source: str,
) -> None:
    """Record entering, leaving, or adjusting an encounter."""
    push_resolution_effect(
        resolution,
        {
            "kind": "encounter",
            "mode": mode,
            "title": title,
            "delta": delta,
            "label": label,
            "source": source,
        },
    )


def add_damage_effect(
    resolution: dict[str, Any] | None,
    *,
    resource: str,
    amount: int,
    applied: int,
    mitigated: int,
    damage_type: str,
    target: str,
    target_label: str,
    penetration: int,
    resistance_flat: int,
    resistance_percent: int,
    source: str,
) -> None:
    """Record a normalized damage or healing effect."""
    push_resolution_effect(
        resolution,
        {
            "kind": "damage",
            "resource": resource,
            "label": _RESOURCE_LABELS.get(resource, resource),
            "amount": int(amount),
            "applied": int(applied),
            "mitigated": int(mitigated),
            "damage_type": damage_type,
            "target": target,
            "target_label": target_label,
            "penetration": int(penetration),
            "resistance_flat": int(resistance_flat),
            "resistance_percent": int(resistance_percent),
            "source": source,
        },
    )


def resolution_change_lines(resolution: dict[str, Any] | None) -> list[str]:
    """Project resolution effects into short player-facing summary lines."""
    active = ensure_resolution(resolution)
    if active is None:
        return []

    lines: list[str] = []
    for effect in active.get("effects", []):
        if not isinstance(effect, dict):
            continue

        kind = str(effect.get("kind", ""))
        if kind == "resource":
            delta = int(effect.get("delta", 0))
            if delta == 0:
                continue
            sign = "+" if delta > 0 else ""
            label = str(effect.get("label", effect.get("resource", "资源")))
            lines.append(f"{label} {sign}{delta}")
            continue

        if kind == "status":
            mode = str(effect.get("mode", ""))
            name = str(effect.get("name", effect.get("status_id", "状态")))
            if mode == "add":
                lines.append(f"获得状态：{name}")
            elif mode == "remove":
                lines.append(f"移除状态：{name}")
            continue

        if kind == "item":
            mode = str(effect.get("mode", ""))
            name = str(effect.get("name", effect.get("item_id", "物品")))
            qty = max(1, int(effect.get("qty", 1)))
            suffix = f" ×{qty}" if qty > 1 else ""
            if mode == "add":
                lines.append(f"获得物品：{name}{suffix}")
            elif mode == "remove":
                lines.append(f"移除物品：{name}{suffix}")
            elif mode == "spend":
                lines.append(f"消耗物品：{name}{suffix}")

        if kind == "encounter":
            mode = str(effect.get("mode", ""))
            title = str(effect.get("title", "遭遇"))
            if mode == "enter":
                lines.append(f"进入遭遇：{title}")
            elif mode == "leave":
                lines.append(f"离开遭遇：{title}")
            elif mode == "phase":
                label = str(effect.get("label", "阶段切换"))
                lines.append(f"遭遇阶段：{label}")
            elif mode == "pressure":
                delta = int(effect.get("delta", 0))
                if delta != 0:
                    sign = "+" if delta > 0 else ""
                    label = str(effect.get("label", "压力"))
                    lines.append(f"{label} {sign}{delta}")
            continue

        if kind == "damage":
            label = str(effect.get("label", effect.get("resource", "资源")))
            amount = abs(int(effect.get("applied", effect.get("amount", 0))))
            if amount <= 0:
                continue
            target = str(effect.get("target", "player"))
            target_label = str(effect.get("target_label", "")).strip()
            damage_type = str(effect.get("damage_type", "")).strip()
            type_suffix = f"（{damage_type}）" if damage_type else ""
            if target and target != "player" and target_label:
                lines.append(f"{target_label}{type_suffix} {label} -{amount}")
            else:
                lines.append(f"{label}{type_suffix} -{amount}")
            continue

    # Deduplicate while preserving order so repeat effects do not spam the UI.
    unique_lines: list[str] = []
    for line in lines:
        if line not in unique_lines:
            unique_lines.append(line)
    return unique_lines


def merge_change_lines(explicit_changes: list[str] | None, resolution: dict[str, Any] | None) -> list[str]:
    """Merge manual change text with normalized effect-derived lines."""
    merged = [str(item) for item in (explicit_changes or []) if str(item)]
    for line in resolution_change_lines(resolution):
        if line not in merged:
            merged.append(line)
    return merged


def legacy_roll_payload(resolution: dict[str, Any] | None) -> dict[str, Any] | None:
    """Expose the old roll shape while the frontend migrates to `resolution`."""
    active = ensure_resolution(resolution)
    if active is None or str(active.get("kind", "")) != "check":
        return None
    return {
        "label": active.get("label", ""),
        "stat": active.get("stat"),
        "dc": active.get("dc"),
        "roll": active.get("roll"),
        "modifier": active.get("modifier"),
        "total": active.get("total"),
        "success": active.get("success"),
        "breakdown": active.get("breakdown", []),
    }
