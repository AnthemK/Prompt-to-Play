# Compact run record

Keep four artifact groups for each issue:

1. **Input snapshot:** collector output with hashes, one `snapshot_as_of`, source health, contribution status, and limit warnings.
2. **Editorial evidence:** save structured `edition.json`, claim-level `evidence/claims.json` and hash-bound `evidence/review.json` according to the [contracts](../../../docs/contracts/edition-v1.md). The **selection ledger** has one row per serious event candidate with `event_id`, tier, confidence, evidence level, source independence, decision, and one-sentence reason. Do not retain routine discarded headlines.
3. **Published brief:** about ten distinct events with original links and visible limitations or corrections.
4. **Persistent state:** update only facts reported, story status, unresolved claims, attention, and information gain.

Use severity consistently:

- `P0`: factual conflict, missing source, invalid time, duplicate event, or unsupported major claim. Resolve before publication.
- `P1`: incomplete coverage, single-source high-impact claim, paywall-limited evidence, or unresolved material ambiguity. Resolve or disclose before publication.
- `P2`: source improvement, automation, interface, or research backlog. Record in `memory/TODO.md`; do not clutter the brief.

Run `python3 -B scripts/validate_snapshot.py REPORT.json` after collection. A `P0` fails validation. A `P1` requires an explicit editorial decision. `P2` does not block the issue.

Paths in commands are relative to `news-trace/`. Keep the four artifacts under the edition directory and `memory/` as specified by the [lifecycle rules](../../../docs/maintenance/file-lifecycle.md).
