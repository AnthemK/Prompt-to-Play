# Access and evidence levels

Read this reference when an article is restricted, incomplete, or technically ambiguous.

The BPC-derived process is pinned to `Lunatic16/paywall-bypass-skill` commit `77a32379b39ddfb56cd646d5563755bc768287fc`. Treat its provider patterns as diagnostics, not proof of access or completeness.

## Access levels

- `authorization_or_request_blocked`: the article returned 401, 402, or 403. Use official feed metadata or an authorized interface.
- `public_page_restricted_or_uncertain`: HTML was returned but subscription markers or `isAccessibleForFree=false` were present. Do not infer complete text.
- `public_body_candidate`: structured article text was visible without a restriction marker. Verify title, byline, publication time, ending, and length before treating it as full article evidence.
- `public_page_unverified`: the page responded but no reliable body signal was found.
- `article_page_unavailable` or `request_error`: retain discovery metadata and record the failure.

## Evidence levels

Use one label per claim: `primary_document`, `verified_full_article`, `official_summary`, `feed_summary`, or `title_only`. A stronger label requires direct inspection. Authorized subscription reading may be recorded as `verified_full_article`, but the run record must state the access route without storing credentials.

Run `python3 -B scripts/inspect_access.py --report INPUT.json` (from `news-trace/`) to create a dated diagnostic report. Keep only the final access classification, observed markers, response status, sample hash, and checked time; do not store unnecessary page content.
