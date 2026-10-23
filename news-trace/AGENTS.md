# NewsTrace agent entry point

First classify the product: daily briefing or thematic tracker. For thematic work, read the [editorial charter](docs/standards/editorial-charter.md), [topic workflow](docs/workflows/topic-tracking.md), [record contract](docs/contracts/topic-records-v1.md), and the relevant [topic hub](topics/README.md). Daily event quotas and `edition.py` gates do not certify thematic reports. Topic reports, email bodies and reading guides are in English unless the user says otherwise. Use Special Report / Topic Tracker titles. Preserve historical sent files; use links to legacy locations instead of silently moving them.

Start with [README.md](README.md) for navigation and [file lifecycle](docs/maintenance/file-lifecycle.md) before creating or cleaning files. Temporary work belongs in `tmp/`; persistent memory in `memory/`; rules in `docs/standards/`, `docs/workflows/`, `docs/maintenance/` and `skills/`.

For each briefing, read the [original standard](docs/standards/NEWS_BRIEFING_STANDARD.md), [briefing skill](skills/news-briefing/SKILL.md), [daily workflow](docs/workflows/daily-brief.md), prior issue in `editions/`, and `memory/`. The user-supplied standard and original design document must remain unchanged; propose revisions as separate versions. Skill-relative paths are relative to its own directory.

Collect with a per-source limit of 15. Count about 10 distinct events, not articles or outlets. Use `scripts/validate_snapshot.py` and `scripts/validate_state.py`; follow [source verification](docs/workflows/source-verification.md) for BBC/Xinhua. Preserve initial inputs and consequential rechecks as distinct files. Disclose evidence levels. `P0` blocks publication, `P1` requires resolution or disclosure, and deferred `P2` belongs in [memory/TODO.md](memory/TODO.md).

Save each issue under `editions/YYYY/MM/DD/`: `brief.md`, `evidence/input.json`, `evidence/selection-ledger.json`, optional `evidence/rechecks/` and `delivery/`. Independent source diagnostics go under `diagnostics/YYYY/MM/DD/`. Update the edition index after publication. Use the [email workflow](docs/workflows/email-delivery.md) for authorized delivery.

After moving files, run `python3 -B scripts/check_layout.py` from the project directory. After code changes, also run `python3 -B -m unittest discover -s tests -q`. Review and remove only temporary outputs. Historical facts and original snapshot hashes must not be silently rewritten; use visible corrections for editorial changes.

For new editions, follow the [edition pipeline](docs/workflows/edition-pipeline.md). `scripts/edition.py build` requires claim-level evidence and a current editorial review; a structural pass is not factual verification. Never auto-approve a review or fabricate missing evidence for legacy editions. The build prepares files only; actual sending still follows explicit user authorization.
