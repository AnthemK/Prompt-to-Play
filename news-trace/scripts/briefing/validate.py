"""Structural gates; source truth and translation fidelity require editorial review."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from validate_snapshot import validate as validate_snapshot
from paths import MEMORY
import json
from .model import INPUTS, LEVELS, SECTIONS, digest, read, timestamp, web_url


def check(folder: Path, require_review: bool = True) -> dict:
    findings = []

    def add(level, code, message):
        findings.append({'severity': level, 'code': code, 'message': message})

    def required(row, keys, label):
        for key in keys:
            if not isinstance(row.get(key), str) or not row[key].strip():
                add('P0', f'{label}.{key}', f'{label}: nonempty {key} required')

    def indexed(rows, label, key='id'):
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError(f'{label}: expected a list of objects')
        out = {}
        for row in rows:
            required(row, [key], label)
            identity = row.get(key)
            if not isinstance(identity, str):
                continue
            if identity in out:
                add('P0', f'{label}.duplicate.{identity}', f'Duplicate {label} ID: {identity}')
            out[identity] = row
        return out

    coverage = {}
    fingerprint = None
    try:
        missing = [name for name in INPUTS if not (folder / name).is_file()]
        if missing:
            for name in missing:
                add('P0', 'missing.' + name, f'Missing {name}; legacy material needs a real evidence review')
        else:
            edition, snapshot, ledger, record = [read(folder / name) for name in INPUTS]
            fingerprint = digest(folder)
            for name, data, version in [('edition', edition, 1), ('ledger', ledger, 2), ('claims', record, 1)]:
                if data.get('schema_version') != version:
                    add('P0', name + '.version', f'{name}: expected schema_version={version}')
            day = datetime.strptime(edition['issue_date'], '%Y-%m-%d').date()
            cutoff = timestamp(edition['cutoff'])
            from datetime import timedelta
            if cutoff.astimezone(timezone(timedelta(hours=8))).date() != day:
                add('P0', 'cutoff.date', 'Issue date must match cutoff in Asia/Shanghai')
            if cutoff != timestamp(snapshot['snapshot_as_of']):
                add('P0', 'cutoff.snapshot', 'Edition cutoff and input snapshot_as_of must match')
            if ledger.get('issue_date') != edition['issue_date'] or ledger.get('input_snapshot') != 'evidence/input.json':
                add('P0', 'ledger.input', 'Ledger date or edition-relative input_snapshot is incorrect')
            for number, (level, message) in enumerate(validate_snapshot(snapshot)):
                add(level, f'snapshot.{number}', message)
            required(edition, ['overview', 'overview_en'], 'edition')
            events = indexed(edition['events'], 'event')
            candidates = indexed(ledger['candidates'], 'candidate', 'event_id')
            claims = indexed(record['claims'], 'claim')
            evidence = indexed(record['evidence'], 'evidence')
            selected = set()
            clusters = set()
            history_path = MEMORY / 'event_history.jsonl'
            history = [json.loads(line) for line in history_path.read_text(encoding='utf-8').splitlines() if line.strip()]
            reported = {row['event_id'] for row in history if row.get('last_reported', '') < edition['issue_date']}
            for eid, candidate in candidates.items():
                required(candidate, ['reason', 'cluster_key', 'story_id', 'information_gain'], 'candidate.' + eid)
                for key, allowed in [('decision', {'selected', 'rejected', 'deferred'}), ('global_significance', set('SABCD')), ('briefing_priority', set('SABCD')), ('attention', {'High','Medium','Low'}), ('confidence', {'High','Medium','Low'})]:
                    if candidate.get(key) not in allowed:
                        add('P0', f'candidate.{eid}.{key}', f'{eid}: invalid {key}')
                if candidate.get('decision') == 'selected':
                    selected.add(eid)
                    if eid in reported and events.get(eid, {}).get('section') != 'Corrections / Clarifications':
                        add('P0', 'event.already-reported.' + eid, f'{eid}: already reported; a new development needs a new event ID and information gain')
                    cluster = candidate.get('cluster_key')
                    if cluster in clusters:
                        add('P0', 'duplicate.cluster.' + eid, 'Selected candidates share the same cluster_key')
                    clusters.add(cluster)
            if selected != set(events):
                add('P0', 'selection.mismatch', 'Rendered events must exactly match selected candidate IDs')
            news_sections = {'Core Developments', 'Other Notable Developments', 'Personal Focus', 'Widely Discussed', 'Unconfirmed but Important'}
            news_count = sum(event.get('section') in news_sections for event in events.values())
            if not 8 <= news_count <= 12:
                add('P1', 'event.count', f'{news_count} distinct news events; editorial target is about 10, not a quota')

            articles = {item['url']: item for item in snapshot['items']}
            origin_by_url = {}
            for sid, source in evidence.items():
                label = 'evidence.' + sid
                required(source, ['source_id', 'publisher', 'url', 'support', 'locator', 'dependency_group', 'checked_by'], label)
                if not web_url(source.get('url', '')):
                    add('P0', label + '.url', f'{sid}: valid HTTP(S) source URL required')
                if source.get('level') not in LEVELS:
                    add('P0', label + '.level', f'{sid}: invalid evidence level')
                url = source.get('url')
                if url in origin_by_url and origin_by_url[url] != source.get('dependency_group'):
                    add('P0', label + '.dependency', f'{sid}: the same URL cannot represent different independent chains')
                origin_by_url[url] = source.get('dependency_group')
                published, checked = timestamp(source['published_at']), timestamp(source['checked_at'])
                if published > cutoff or checked < published or checked > datetime.now(timezone.utc):
                    add('P0', label + '.time', f'{sid}: invalid publication/check chronology')
                article = articles.get(source.get('url'))
                if article is not None:
                    if source.get('source_id') != article.get('source_id') or source.get('publisher') != article.get('publisher') or published != timestamp(article['published_at']):
                        add('P0', label + '.snapshot', f'{sid}: source identity/time differs from input snapshot')
                elif source.get('discovery') != 'supplemental' or not source.get('discovery_reason'):
                    add('P0', label + '.discovery', f'{sid}: source absent from snapshot; document supplemental discovery')

            used_claims = set()
            claim_texts = set()
            topics, regions = Counter(), Counter()
            for eid, event in events.items():
                required(event, ['headline', 'headline_en', 'why_it_matters', 'why_it_matters_en', 'topic', 'region'], 'event.' + eid)
                topics[event.get('topic', '')] += 1
                regions[event.get('region', '')] += 1
                if event.get('section') not in SECTIONS:
                    add('P0', 'event.section.' + eid, f'{eid}: invalid section')
                if event.get('media_framing') and not event.get('media_framing_en'):
                    add('P0', 'event.translation.' + eid, f'{eid}: framing needs English email text')
                if candidates.get(eid, {}).get('confidence') == 'Low' and event.get('section') != 'Unconfirmed but Important':
                    add('P0', 'confidence.section.' + eid, f'{eid}: Low confidence belongs in Unconfirmed but Important')
                claim_ids = event.get('claim_ids')
                if not isinstance(claim_ids, list) or not claim_ids:
                    add('P0', 'event.claims.' + eid, f'{eid}: at least one claim is required')
                    continue
                groups = set()
                for cid in claim_ids:
                    if cid in used_claims:
                        add('P0', 'claim.reuse.' + cid, f'{cid}: rendered more than once')
                    used_claims.add(cid)
                    claim = claims.get(cid)
                    if not claim or claim.get('event_id') != eid:
                        add('P0', 'claim.reference.' + str(cid), f'{eid}: missing or mismatched claim {cid}')
                        continue
                    required(claim, ['text', 'text_en'], 'claim.' + cid)
                    normalized = ' '.join(claim.get('text_en', '').lower().split())
                    if normalized in claim_texts:
                        add('P0', 'claim.duplicate.' + cid, f'{cid}: duplicate claim text')
                    claim_texts.add(normalized)
                    if claim.get('kind') not in {'fact', 'reporting', 'analysis', 'opinion', 'primary_source'}:
                        add('P0', 'claim.kind.' + cid, f'{cid}: explicit content kind required')
                    if claim.get('status') not in {'verified', 'disputed', 'unconfirmed'}:
                        add('P0', 'claim.status.' + cid, f'{cid}: review status must be explicit')
                    refs = claim.get('evidence_ids')
                    if not isinstance(refs, list) or not refs:
                        add('P0', 'claim.evidence.' + cid, f'{cid}: evidence references required')
                        continue
                    claim_groups = set()
                    for ref in refs:
                        source = evidence.get(ref)
                        if not source:
                            add('P0', 'evidence.reference.' + str(ref), f'{cid}: evidence {ref} missing')
                            continue
                        group = source.get('dependency_group')
                        claim_groups.add(group)
                        groups.add(group)
                        if source.get('level') in {'feed_summary', 'title_only'}:
                            add('P1', 'limited.' + ref, f'{ref}: only {source["level"]}; details must stay within visible content')
                    if len(claim_groups) < 2:
                        add('P1', 'single-source.' + cid, f'{cid}: fewer than two independent information chains; attribution is required')
                    if claim.get('status') != 'verified':
                        add('P1', 'uncertain.' + cid, f'{cid}: {claim.get("status")}; retain uncertainty')
                        if candidates.get(eid, {}).get('confidence') == 'High':
                            add('P0', 'confidence.overstated.' + eid, f'{eid}: unresolved claims cannot carry High confidence')
                event['independent_chains_observed'] = len(groups)  # in-memory only
            if set(claims) != used_claims:
                add('P0', 'claims.orphans', 'Claims must belong to exactly one rendered event')
            checks = ledger.get('coverage_review')
            if not isinstance(checks, list) or not checks:
                add('P0', 'coverage.review', 'Record considered topic/region coverage and any gaps')
            else:
                for row in checks:
                    required(row, ['area', 'note'], 'coverage')
                    if row.get('status') not in {'covered', 'no_material_development', 'gap'}:
                        add('P0', 'coverage.status', 'Coverage status is invalid')
                    if row.get('status') == 'gap':
                        add('P1', 'coverage.gap.' + row.get('area', ''), row.get('note', 'Coverage gap'))
            health = Counter(row.get('health_status', row.get('status', 'unknown')) for row in snapshot['sources'])
            coverage = {'events': news_count, 'entries': len(events), 'topics': dict(topics), 'regions': dict(regions), 'publishers': sorted({row['publisher'] for row in evidence.values()}), 'source_health': dict(health)}
            if health.get('error'):
                add('P1', 'coverage.source-errors', f'{health["error"]} source endpoints failed; discovery may be incomplete')
            if len(topics) < 3 or len(regions) < 3:
                add('P1', 'coverage.concentration', 'Coverage is concentrated; review discovery breadth without padding stories')

            if require_review:
                review = read(folder / 'evidence/review.json')
                if review.get('schema_version') != 1:
                    add('P0', 'review.version', 'Expected review schema_version=1')
                required(review, ['reviewed_by', 'reviewed_at'], 'review')
                reviewed_at = timestamp(review['reviewed_at'])
                if reviewed_at < cutoff or reviewed_at > datetime.now(timezone.utc):
                    add('P0', 'review.time', 'Invalid editorial review time')
                if review.get('decision') != 'approved' or review.get('input_sha256') != fingerprint:
                    add('P0', 'review.stale', 'Editorial approval missing or content changed since review')
                required_checks = {'facts', 'translations', 'source_independence', 'coverage', 'prior_issue', 'headline_and_analysis'}
                if not required_checks.issubset(set(review.get('checks_completed', []))):
                    add('P0', 'review.checklist', 'Editorial checklist is incomplete')
                disclosures = review.get('disclosures', {})
                for item in list(findings):
                    if item['severity'] == 'P1' and not (isinstance(disclosures.get(item['code']), str) and disclosures[item['code']].strip()):
                        add('P0', 'undisclosed.' + item['code'], 'P1 requires a reader-facing English disclosure: ' + item['code'])
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        add('P0', 'invalid.input', f'Cannot validate edition: {exc}')
    # A source may be cited by several claims: show its limitation once.
    findings = list({(f['severity'], f['code']): f for f in findings}.values())
    passed = not any(f['severity'] == 'P0' for f in findings)
    return {'schema_version': 1, 'input_sha256': fingerprint, 'passed': passed, 'ready': require_review and passed, 'review_required': require_review, 'coverage': coverage, 'findings': findings}
