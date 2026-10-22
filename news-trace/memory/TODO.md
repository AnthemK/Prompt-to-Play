# NewsTrace TODO

Only unresolved work belongs here. `P0` blocks publication, `P1` should be resolved or disclosed before publication, and `P2` is planned improvement.

## P1

- Align `verify_authoritative.py` with each report's `snapshot_as_of` and `run_args.max_age_hours`; it currently validates against `completed_at` and a fixed 72-hour window.
- Add claim-level evidence records linking each material statement to an original URL, evidence level, publication time, and quoted or located support. Event-level source lists remain insufficient for automated trace checks.
- Implement machine validation for the candidate/event selection ledger required by the Skill; the ledger records clustering decisions and concise reasons for selecting or rejecting serious candidates.

## P2

- Add the scheduled 08:00 Asia/Shanghai run, retries, failure notification, and incremental cursors after the manual workflow stabilizes.
- Add the project to Git and establish a reviewed baseline when the user is ready.
- Add an expandable reader after the Markdown format and evidence schema stabilize.
- Recheck subscription outlets when authenticated access or an official licensed API is available; current BPC-derived diagnostics do not establish full-text access.
