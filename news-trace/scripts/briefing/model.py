"""Small shared contracts. No network or publication side effects."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

INPUTS = ('edition.json', 'evidence/input.json', 'evidence/selection-ledger.json', 'evidence/claims.json')
LEVELS = {'primary_document', 'verified_full_article', 'official_summary', 'feed_summary', 'title_only'}
SECTIONS = ('Core Developments', 'Other Notable Developments', 'Personal Focus', 'Widely Discussed', 'Worth Reading', 'Actionable Insight', 'Unconfirmed but Important', 'Corrections / Clarifications', 'What to Watch', 'Preference Update', 'Weekend Reading')


def read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path.name}: expected a JSON object')
    return data


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timezone is required')
    return dt


def web_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {'https', 'http'} and bool(parsed.hostname) and not parsed.username


def digest(folder: Path) -> str:
    result = hashlib.sha256()
    for name in INPUTS:
        result.update(name.encode() + b'\0' + (folder / name).read_bytes() + b'\0')
    return result.hexdigest()


def initialize(folder: Path, day: str) -> None:
    datetime.strptime(day, '%Y-%m-%d')
    if folder.exists():
        raise ValueError('edition directory already exists; refusing to overwrite')
    folder.mkdir(parents=True)
    write(folder / 'edition.json', {
        'schema_version': 1, 'issue_date': day, 'cutoff': '', 'overview': '', 'overview_en': '', 'events': []})
    write(folder / 'evidence/selection-ledger.json', {
        'schema_version': 2, 'issue_date': day, 'input_snapshot': 'evidence/input.json',
        'coverage_review': [], 'candidates': []})
    write(folder / 'evidence/claims.json', {'schema_version': 1, 'evidence': [], 'claims': []})
    (folder / 'README.md').write_text(
        '# Draft edition\n\nCollect into `evidence/input.json`, then fill `edition.json`, '
        '`evidence/selection-ledger.json` and `evidence/claims.json`. '
        'This empty workspace is not a published issue.\n', encoding='utf-8')
