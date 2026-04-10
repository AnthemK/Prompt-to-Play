"""Helpers for the engine's unified action-resolution payload.

The long-term goal is for checks, encounters, utility use, damage, and other
system results to share a single explainable structure. The frontend only needs
to learn one payload shape to render outcomes consistently.
"""

from __future__ import annotations

from typing import Any, TypedDict


class BreakdownEntry(TypedDict):
    """One modifier or impact component in resolution breakdown output."""

    value: int
    source: str


class ExplainFragment(TypedDict, total=False):
    """One human-readable explanation fragment for resolution rendering."""

    code: str
    text: str
    data: dict[str, Any]


class ResolutionExplain(TypedDict):
    """Top-level explain block merged into every resolution payload."""

    summary: str
    fragments: list[ExplainFragment]


class ResolutionEffect(TypedDict, total=False):
    """Normalized effect payload shared by state/resource/status/item updates."""

    kind: str
    source: str
    resource: str
    label: str
    delta: int
    mode: str
    status_id: str
    name: str
    duration_turns: int
    item_id: str
    qty: int
    flag: str
    value: bool
    title: str
    amount: int
    applied: int
    mitigated: int
    amplified: int
    shield_absorbed: int
    shield_before: int
    shield_after: int
    impact_kind: str
    damage_type: str
    target: str
    target_label: str
    penetration: int
    resistance_flat: int
    resistance_percent: int


class ResolutionPayload(TypedDict, total=False):
    """Unified resolution object used by check/combat/utility/story actions."""

    kind: str
    label: str
    success: bool | None
    stat: str | None
    stat_label: str | None
    skill: str | None
    skill_label: str | None
    dc: int | None
    roll: int | None
    modifier: int | None
    total: int | None
    tags: list[str]
    breakdown: list[BreakdownEntry]
    dc_breakdown: list[BreakdownEntry]
    amount: int | None
    applied: int | None
    mitigated: int | None
    amplified: int | None
    shield_absorbed: int | None
    shield_before: int | None
    shield_after: int | None
    impact_kind: str | None
    drain_recovered: int | None
    damage_type: str | None
    target: str | None
    target_label: str | None
    penetration: int | None
    resistance_flat: int | None
    resistance_percent: int | None
    opponent_label: str | None
    opponent_roll: int | None
    opponent_modifier: int | None
    opponent_total: int | None
    active_side: str | None
    passive_side: str | None
    tie: bool | None
    tie_policy: str | None
    margin: int | None
    explain: ResolutionExplain
    system: dict[str, Any]
    effects: list[ResolutionEffect]

_RESOURCE_LABELS = {
    "hp": "生命",
    "shield": "护盾",
    "corruption": "腐化",
    "doom": "末日进度",
    "shillings": "先令",
}


def default_resource_label(resource: str) -> str:
    """Return the generic fallback label for one resource identifier."""
    return _RESOURCE_LABELS.get(resource, resource)


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert unknown values to int without raising on None/invalid input."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def build_resolution(
    *,
    kind: str,
    label: str,
    success: bool | None = None,
    stat: str | None = None,
    stat_label: str | None = None,
    skill: str | None = None,
    skill_label: str | None = None,
    dc: int | None = None,
    roll: int | None = None,
    modifier: int | None = None,
    total: int | None = None,
    tags: list[str] | None = None,
    breakdown: list[BreakdownEntry] | None = None,
) -> ResolutionPayload:
    """Create the canonical resolution payload skeleton."""
    return {
        "kind": kind,
        "label": label,
        "success": success,
        "stat": stat,
        "stat_label": stat_label,
        "skill": skill,
        "skill_label": skill_label,
        "dc": dc,
        "roll": roll,
        "modifier": modifier,
        "total": total,
        "tags": list(tags or []),
        "breakdown": list(breakdown or []),
        "dc_breakdown": [],
        "amount": None,
        "applied": None,
        "mitigated": None,
        "amplified": None,
        "shield_absorbed": None,
        "shield_before": None,
        "shield_after": None,
        "impact_kind": None,
        "drain_recovered": None,
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
        "active_side": None,
        "passive_side": None,
        "tie": None,
        "tie_policy": None,
        "margin": None,
        "explain": {"summary": "", "fragments": []},
        "effects": [],
    }


def ensure_resolution(resolution: ResolutionPayload | None) -> ResolutionPayload | None:
    """Backfill optional fields so downstream renderers can rely on them."""
    if not isinstance(resolution, dict):
        return None
    resolution.setdefault("kind", "action")
    resolution.setdefault("label", "")
    resolution.setdefault("success", None)
    resolution.setdefault("stat", None)
    resolution.setdefault("stat_label", None)
    resolution.setdefault("skill", None)
    resolution.setdefault("skill_label", None)
    resolution.setdefault("dc", None)
    resolution.setdefault("roll", None)
    resolution.setdefault("modifier", None)
    resolution.setdefault("total", None)
    resolution.setdefault("tags", [])
    resolution.setdefault("breakdown", [])
    resolution.setdefault("dc_breakdown", [])
    resolution.setdefault("amount", None)
    resolution.setdefault("applied", None)
    resolution.setdefault("mitigated", None)
    resolution.setdefault("amplified", None)
    resolution.setdefault("shield_absorbed", None)
    resolution.setdefault("shield_before", None)
    resolution.setdefault("shield_after", None)
    resolution.setdefault("impact_kind", None)
    resolution.setdefault("drain_recovered", None)
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
    resolution.setdefault("active_side", None)
    resolution.setdefault("passive_side", None)
    resolution.setdefault("tie", None)
    resolution.setdefault("tie_policy", None)
    resolution.setdefault("margin", None)
    resolution.setdefault("explain", {"summary": "", "fragments": []})
    resolution.setdefault("effects", [])
    explain = resolution.get("explain")
    if not isinstance(explain, dict):
        explain = {"summary": "", "fragments": []}
        resolution["explain"] = explain
    explain.setdefault("summary", "")
    fragments = explain.get("fragments")
    if not isinstance(fragments, list):
        explain["fragments"] = []
    else:
        explain["fragments"] = [entry for entry in fragments if isinstance(entry, dict)]
    return resolution


def push_resolution_effect(resolution: ResolutionPayload | None, payload: ResolutionEffect) -> None:
    """Append one normalized effect entry to a resolution payload."""
    active = ensure_resolution(resolution)
    if active is None:
        return
    active["effects"].append(payload)


def add_resource_effect(
    resolution: ResolutionPayload | None,
    resource: str,
    delta: int,
    source: str,
    *,
    label: str | None = None,
) -> None:
    """Record a resource delta such as HP, corruption, or currency."""
    if int(delta) == 0:
        return
    push_resolution_effect(
        resolution,
        {
            "kind": "resource",
            "resource": resource,
            "label": str(label or default_resource_label(resource)),
            "delta": int(delta),
            "source": source,
        },
    )


def push_explain_fragment(
    resolution: ResolutionPayload | None,
    *,
    code: str,
    text: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Append one normalized explanation fragment to a resolution payload."""
    active = ensure_resolution(resolution)
    if active is None:
        return
    explain = active.get("explain", {})
    if not isinstance(explain, dict):
        explain = {"summary": "", "fragments": []}
        active["explain"] = explain
    fragments = explain.get("fragments")
    if not isinstance(fragments, list):
        fragments = []
        explain["fragments"] = fragments

    clean_text = str(text or "").strip()
    clean_code = str(code or "").strip() or "detail"
    if not clean_text:
        return
    if any(str(entry.get("text", "")) == clean_text for entry in fragments if isinstance(entry, dict)):
        return

    payload: ExplainFragment = {"code": clean_code, "text": clean_text}
    if isinstance(data, dict) and data:
        payload["data"] = data
    fragments.append(payload)


def _build_status_summary(active: ResolutionPayload) -> str:
    """Build a concise status summary for the top of explanation output."""
    label = str(active.get("label", "")).strip() or "结算"
    kind = str(active.get("kind", "")).strip().lower()
    stat_label = str(active.get("stat_label", "")).strip()
    skill_label = str(active.get("skill_label", "")).strip()
    roll_context = ""
    if skill_label:
        roll_context = " + ".join([part for part in (stat_label, skill_label) if part])
    if roll_context and kind in {"check", "save", "contest"}:
        label = f"{label}（{roll_context}）"
    success = active.get("success")
    if success is True:
        return f"{label}：成功"
    if success is False:
        return f"{label}：失败"
    return f"{label}：完成"


def _append_breakdown_fragments(active: ResolutionPayload) -> None:
    """Mirror modifier/impact breakdown entries into explain fragments."""
    for entry in active.get("breakdown", []):
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source", "")).strip()
        value = _safe_int(entry.get("value", 0))
        if not source:
            continue
        sign = "+" if value >= 0 else ""
        push_explain_fragment(
            active,
            code="breakdown",
            text=f"{source} {sign}{value}",
            data={"source": source, "value": value},
        )


def _append_dc_breakdown_fragments(active: ResolutionPayload) -> None:
    """Mirror DC-building entries into explain fragments for debugging and review."""
    for entry in active.get("dc_breakdown", []):
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source", "")).strip()
        value = _safe_int(entry.get("value", 0))
        if not source:
            continue
        if source == "基础DC":
            text = f"{source} {value}"
        else:
            sign = "+" if value >= 0 else ""
            text = f"DC修正：{source} {sign}{value}"
        push_explain_fragment(
            active,
            code="dc.breakdown",
            text=text,
            data={"source": source, "value": value},
        )


def _append_resolution_specific_fragments(active: ResolutionPayload) -> None:
    """Append kind-specific explanation lines derived from structured fields."""
    kind = str(active.get("kind", "")).strip().lower()

    if kind in {"check", "save"}:
        roll = active.get("roll")
        modifier = active.get("modifier")
        total = active.get("total")
        dc = active.get("dc")
        if all(isinstance(value, int) for value in (roll, modifier, total, dc)):
            sign = "+" if _safe_int(modifier) >= 0 else ""
            push_explain_fragment(
                active,
                code="roll",
                text=f"d20={roll} + 修正{sign}{modifier} = {total} / DC {dc}",
                data={
                    "roll": _safe_int(roll),
                    "modifier": _safe_int(modifier),
                    "total": _safe_int(total),
                    "dc": _safe_int(dc),
                },
            )
        return

    if kind == "contest":
        roll = active.get("roll")
        modifier = active.get("modifier")
        total = active.get("total")
        opponent_roll = active.get("opponent_roll")
        opponent_modifier = active.get("opponent_modifier")
        opponent_total = active.get("opponent_total")
        opponent_label = str(active.get("opponent_label", "对手"))
        if all(
            isinstance(value, int)
            for value in (roll, modifier, total, opponent_roll, opponent_modifier, opponent_total)
        ):
            sign = "+" if _safe_int(modifier) >= 0 else ""
            opponent_sign = "+" if _safe_int(opponent_modifier) >= 0 else ""
            push_explain_fragment(
                active,
                code="contest.player",
                text=f"你：d20={roll} + 修正{sign}{modifier} = {total}",
                data={"roll": _safe_int(roll), "modifier": _safe_int(modifier), "total": _safe_int(total)},
            )
            push_explain_fragment(
                active,
                code="contest.opponent",
                text=f"{opponent_label}：d20={opponent_roll} + 修正{opponent_sign}{opponent_modifier} = {opponent_total}",
                data={
                    "label": opponent_label,
                    "roll": _safe_int(opponent_roll),
                    "modifier": _safe_int(opponent_modifier),
                    "total": _safe_int(opponent_total),
                },
            )
        tie = active.get("tie")
        if tie is True:
            push_explain_fragment(
                active,
                code="contest.tie",
                text=f"平局判定：{str(active.get('tie_policy', 'player_wins'))} · 结果边际 {_safe_int(active.get('margin', 0))}",
                data={
                    "tie_policy": str(active.get("tie_policy", "player_wins")),
                    "margin": _safe_int(active.get("margin", 0)),
                },
            )
        return

    if kind in {"damage", "healing", "drain"}:
        impact_kind = str(active.get("impact_kind", kind)).strip() or kind
        damage_type = str(active.get("damage_type", "physical")).strip() or "physical"
        target = str(active.get("target", "player")).strip().lower() or "player"
        target_label = str(active.get("target_label", "")).strip() if target == "enemy" else "你"
        title_map = {"damage": "伤害", "healing": "治疗", "drain": "吸取"}
        push_explain_fragment(
            active,
            code="impact.summary",
            text=(
                f"{title_map.get(impact_kind, '结算')}类型：{damage_type} · "
                f"目标：{target_label or '敌方'} · 宣告：{_safe_int(active.get('amount', 0))} · "
                f"减伤：{_safe_int(active.get('mitigated', 0))} · 易伤增幅：{_safe_int(active.get('amplified', 0))} · "
                f"护盾吸收：{_safe_int(active.get('shield_absorbed', 0))} · 生效：{_safe_int(active.get('applied', 0))}"
            ),
            data={
                "impact_kind": impact_kind,
                "damage_type": damage_type,
                "target": target,
                "target_label": target_label or "敌方",
                "amount": _safe_int(active.get("amount", 0)),
                "mitigated": _safe_int(active.get("mitigated", 0)),
                "amplified": _safe_int(active.get("amplified", 0)),
                "shield_absorbed": _safe_int(active.get("shield_absorbed", 0)),
                "applied": _safe_int(active.get("applied", 0)),
            },
        )
        if kind == "drain":
            push_explain_fragment(
                active,
                code="impact.drain_recovered",
                text=f"吸取回复：{_safe_int(active.get('drain_recovered', 0))}",
                data={"drain_recovered": _safe_int(active.get("drain_recovered", 0))},
            )
        return


def refresh_resolution_explain(resolution: ResolutionPayload | None) -> ResolutionPayload | None:
    """Rebuild explain summary/fragments from structured resolution fields.

    This keeps the output in a dual-track shape:
    1) Structured machine fields (`dc`, `roll`, `effects`, ...)
    2) Human-readable explain fragments (`explain.summary/fragments`)
    """
    active = ensure_resolution(resolution)
    if active is None:
        return None

    explain = active.get("explain", {})
    if not isinstance(explain, dict):
        explain = {"summary": "", "fragments": []}
        active["explain"] = explain
    explain["summary"] = _build_status_summary(active)
    explain["fragments"] = []

    push_explain_fragment(active, code="summary", text=str(explain["summary"]))
    _append_resolution_specific_fragments(active)
    _append_dc_breakdown_fragments(active)
    _append_breakdown_fragments(active)

    for line in resolution_change_lines(active):
        push_explain_fragment(active, code="change", text=line)

    return active


def add_status_effect(
    resolution: ResolutionPayload | None,
    *,
    mode: str,
    status_id: str,
    name: str,
    source: str,
    duration_turns: int | None = None,
) -> None:
    """Record a status add/remove event."""
    payload: ResolutionEffect = {
        "kind": "status",
        "mode": mode,
        "status_id": status_id,
        "name": name,
        "source": source,
    }
    if duration_turns is not None:
        payload["duration_turns"] = int(duration_turns)
    push_resolution_effect(
        resolution,
        payload,
    )


def add_item_effect(
    resolution: ResolutionPayload | None,
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


def add_flag_effect(resolution: ResolutionPayload | None, *, flag: str, value: bool, source: str) -> None:
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
    resolution: ResolutionPayload | None,
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
    resolution: ResolutionPayload | None,
    *,
    resource: str,
    amount: int,
    applied: int,
    mitigated: int,
    amplified: int = 0,
    shield_absorbed: int = 0,
    shield_before: int = 0,
    shield_after: int = 0,
    impact_kind: str = "damage",
    damage_type: str,
    target: str,
    target_label: str,
    penetration: int,
    resistance_flat: int,
    resistance_percent: int,
    source: str,
    label: str | None = None,
) -> None:
    """Record one normalized impact effect (damage/healing/drain)."""
    push_resolution_effect(
        resolution,
        {
            "kind": "damage",
            "resource": resource,
            "label": str(label or default_resource_label(resource)),
            "amount": int(amount),
            "applied": int(applied),
            "mitigated": int(mitigated),
            "amplified": int(amplified),
            "shield_absorbed": int(shield_absorbed),
            "shield_before": int(shield_before),
            "shield_after": int(shield_after),
            "impact_kind": impact_kind,
            "damage_type": damage_type,
            "target": target,
            "target_label": target_label,
            "penetration": int(penetration),
            "resistance_flat": int(resistance_flat),
            "resistance_percent": int(resistance_percent),
            "source": source,
        },
    )


def resolution_change_lines(resolution: ResolutionPayload | None) -> list[str]:
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
            source = str(effect.get("source", "")).strip()
            duration_turns = effect.get("duration_turns")
            duration_suffix = ""
            if isinstance(duration_turns, int) and duration_turns > 0 and mode == "add":
                duration_suffix = f"（{duration_turns} 回合）"
            if mode == "add":
                lines.append(f"获得状态：{name}{duration_suffix}")
            elif mode == "remove":
                remove_suffix = "（持续结束）" if source == "状态持续结束" else ""
                lines.append(f"移除状态：{name}{remove_suffix}")
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
            elif mode == "exit_unlock":
                label = str(effect.get("label", "遭遇出口已解锁"))
                lines.append(label)
            elif mode == "phase":
                label = str(effect.get("label", "阶段切换"))
                lines.append(f"遭遇阶段：{label}")
            elif mode == "enemy_behavior":
                label = str(effect.get("label", "敌方行动"))
                lines.append(f"敌方行动：{label}")
            elif mode == "pressure":
                delta = int(effect.get("delta", 0))
                if delta != 0:
                    sign = "+" if delta > 0 else ""
                    label = str(effect.get("label", "压力"))
                    lines.append(f"{label} {sign}{delta}")
            elif mode == "environment":
                label = str(effect.get("label", "环境变化"))
                delta = effect.get("delta")
                if isinstance(delta, int) and delta != 0:
                    sign = "+" if delta > 0 else ""
                    lines.append(f"{label} ({sign}{delta})")
                else:
                    lines.append(label)
            continue

        if kind == "damage":
            label = str(effect.get("label", effect.get("resource", "资源")))
            amount = abs(int(effect.get("applied", effect.get("amount", 0))))
            if amount <= 0:
                continue
            impact_kind = str(effect.get("impact_kind", "damage")).strip() or "damage"
            target = str(effect.get("target", "player"))
            target_label = str(effect.get("target_label", "")).strip()
            damage_type = str(effect.get("damage_type", "")).strip()
            type_suffix = f"（{damage_type}）" if damage_type else ""
            if impact_kind == "healing":
                if target and target != "player" and target_label:
                    lines.append(f"{target_label}{type_suffix} {label} +{amount}")
                else:
                    lines.append(f"{label}{type_suffix} +{amount}")
            else:
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


def merge_change_lines(explicit_changes: list[str] | None, resolution: ResolutionPayload | None) -> list[str]:
    """Merge manual change text with normalized effect-derived lines."""
    merged = [str(item) for item in (explicit_changes or []) if str(item)]
    for line in resolution_change_lines(resolution):
        if line not in merged:
            merged.append(line)
    return merged


def legacy_roll_payload(resolution: ResolutionPayload | None) -> dict[str, Any] | None:
    """Expose the old roll shape while the frontend migrates to `resolution`."""
    active = ensure_resolution(resolution)
    if active is None or str(active.get("kind", "")) != "check":
        return None
    return {
        "label": active.get("label", ""),
        "stat": active.get("stat"),
        "stat_label": active.get("stat_label"),
        "skill": active.get("skill"),
        "skill_label": active.get("skill_label"),
        "dc": active.get("dc"),
        "roll": active.get("roll"),
        "modifier": active.get("modifier"),
        "total": active.get("total"),
        "success": active.get("success"),
        "breakdown": active.get("breakdown", []),
        "dc_breakdown": active.get("dc_breakdown", []),
    }
