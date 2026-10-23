---
name: news-briefing
description: Produce or revise a NewsTrace daily or weekend briefing from live reporting. Use for broad source discovery, event clustering, verification, cross-outlet framing, bilingual writing, corrections, and persistent story tracking.
---

# NewsTrace briefing

All `../../` paths below are relative to this `SKILL.md` file, not the shell’s current directory. Read `../../docs/standards/NEWS_BRIEFING_STANDARD.md` before every run. It is the governing editorial standard and must remain unchanged. This skill is its executable summary; if the two differ, follow the standard unless the user has given a newer, explicit instruction. The user's current target is **about 10 distinct news events per daily issue**, when enough substantive developments exist. Multiple outlets covering one event count as one event; one outlet may contribute several events. Never pad with weak or repeated stories to hit a quota.

## Inputs and window

1. Check `../../editions/`, `../../editions/YYYY/MM/DD/evidence/`, `../../config/sources.json`, `../../config/sources/`, and any `../../memory/` files. Record the prior issue's cutoff and already reported facts. Use `Asia/Shanghai` for display and UTC for machine timestamps.
2. For a scheduled morning issue, target 08:00 local and developments since the previous issue; a roughly 30-hour discovery lookback is acceptable, but do not present old facts as new. For a manual or late issue, state its actual cutoff and coverage window.
3. Collect broadly across working sources, including wires, major outlets, credible local reporting, and relevant primary material. The six selected outlets in `../../docs/research/core-six-selection.md` remain core inputs; supplemental outlets are welcome. Save a dated input snapshot in `../../editions/YYYY/MM/DD/evidence/`. Use its single `snapshot_as_of` time to check every article against the same window. Keep rechecks in separate files so the first snapshot remains auditable. Distinguish `health_status` from `contribution_status`: a reachable or active endpoint may be disabled, duplicated, or have no article in the issue window. Treat `retrieval_limit_reached` as incomplete-coverage evidence. Report source failures and gaps; a failed request is not evidence that the outlet has no news.

## Editorial pipeline

1. **Discover and cluster.** Treat a source item as an *article*, a discrete development as an *event*, and the continuing subject as a *story*. Cluster by actors, action, time, place, and result. Record source dependency; syndicated copies are not independent confirmation.
2. **Verify.** Open original articles or primary records where possible. For each claim, record `primary_document`, `verified_full_article`, `official_summary`, `feed_summary`, or `title_only`. A headline-only or paywalled item can support only visible text. For restricted pages, read [references/access-levels.md](references/access-levels.md) and use `scripts/inspect_access.py --report INPUT.json`; an HTTP 200 or embedded `articleBody` is not by itself proof of completeness. For a rotating “current release” URL, record its release ID, date, key figures, and an archive link once available. Attribute allegations and contested claims. Separate fact, reporting, analysis, opinion, and source statements. Mark confidence High/Medium/Low independently of importance. For a combined BBC/Xinhua report, run `python3 -B scripts/verify_authoritative.py REPORT.json`; resolve or exclude listing/article title mismatches.
3. **Rank.** Judge global significance using magnitude, surprise, breadth, systemic impact, duration, irreversibility, and propagation. Then ask what *new* information this event adds since the prior brief. Assign S/A/B/C/D priority and H/M/L attention without numerical pseudo-scores. Include globally important developments first; use user relevance only after significance. Keep a discovery slice across regions, topics, and perspectives; avoid manufactured balance.
4. **Select.** Aim for roughly 10 distinct, meaningful events across politics, economics, technology, science, culture, and other consequential fields as warranted by the day's evidence. Do not impose one item per outlet or one item per category. Join multiple source links under the same event. Reserve 1–2 strong analytical pieces for `Worth Reading` only when useful, and label opinion. Put consequential unresolved claims under `Unconfirmed but Important`, not as established core news.
5. **Compare framing.** State the common factual core first, then only documented differences in emphasis, attribution, evidence, uncertainty, or proposed implications. An outlet's presumed political position is never proof of its article's framing. Do not infer motives from omissions.
6. **Write.** Follow the section order and item template in standard §14; omit empty optional sections. Each core event has a neutral headline, `What happened`, `Why it matters`, `Media framing` when meaningful, and 2–4 original source links when available. Give publication/update times where material. Write reporting from English outlets in English, reporting from Chinese outlets in Chinese, and cross-media synthesis in English. Keep clear attribution and uncertainty. Put corrections or clarifications in a visible section rather than silently replacing prior text.
7. **Record by severity and lifecycle.** Read [references/run-record.md](references/run-record.md) and `../../docs/maintenance/file-lifecycle.md`. Keep the input snapshot, serious-candidate selection ledger, published brief, persistent state, and any cited evidence. Put trial and debugging outputs in `../../tmp/` and clear them after the run. `P0` blocks publication; `P1` must be resolved or disclosed; `P2` belongs in `../../memory/TODO.md`. Do not retain routine intermediate noise.
8. **Persist and review.** Save the issue as `../../editions/YYYY/MM/DD/brief.md`. Update event and story state so the next run can identify new facts. Keep source publication time distinct from the state edit time. Apply standard §22's checklist: every material claim supported, links point to originals, dates are accurate, confidence and opinion labels clear, repeat stories show information gain, meaningful perspectives represented, and reading time remains reasonable. State any collection or access limitations in the issue and add a dated, visible clarification if a later check changes them.

## Practical commands

From `news-trace/`, a broad manual snapshot can be made with:

```sh
python3 -B scripts/collect.py --limit 15 --max-age-hours 36 --output editions/YYYY/MM/DD/evidence/input.json
python3 -B scripts/validate_snapshot.py editions/YYYY/MM/DD/evidence/input.json
python3 -B scripts/validate_state.py
```

Inspect the resulting `sources` and `items` fields before writing; the command is discovery, not verification. Follow live links and verify high-impact items individually. Keep the original standard untouched; create a separate versioned copy if proposing editorial changes.

For authorized email delivery, read `../../docs/workflows/email-delivery.md`: the English briefing belongs in the email body, with the full edition and supporting materials attached. Archive delivery artifacts within that edition.

New editions use the [structured edition pipeline](../../docs/workflows/edition-pipeline.md) and [v1 contracts](../../docs/contracts/edition-v1.md). Run `python3 -B scripts/edition.py check ISSUE --content-only`, complete actual editorial review, then run `check ISSUE` and `build ISSUE`. A missing legacy evidence record remains a gap; do not manufacture it to pass a gate. Review hashes detect input changes but do not prove factual correctness.
