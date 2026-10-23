"""Render reviewed content into readable Markdown and an English email package."""
from __future__ import annotations

import hashlib
import html
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .model import INPUTS, SECTIONS, digest, read, write
from .validate import check


def render(folder: Path) -> tuple[str, str]:
    edition = read(folder / 'edition.json')
    records = read(folder / 'evidence/claims.json')
    claims = {row['id']: row for row in records['claims']}
    sources = {row['id']: row for row in records['evidence']}
    candidates = {row['event_id']: row for row in read(folder / 'evidence/selection-ledger.json')['candidates']}
    review = read(folder / 'evidence/review.json')
    day = edition['issue_date']
    md = [f'# Daily News Brief — {day}', '', f'Cutoff: {edition["cutoff"]}', '', '## Today in One Sentence', '', edition['overview'], '']
    esc = html.escape
    body = ['<!doctype html><html lang="en"><meta charset="utf-8"><body style="font-family:Arial,sans-serif;line-height:1.6;max-width:760px;margin:auto;padding:20px">',
            f'<h1>Daily News Brief — {esc(day)}</h1><p>Prepared by codeX · Cutoff: {esc(edition["cutoff"])}</p>',
            '<h2>Today in One Sentence</h2>', f'<p>{esc(edition["overview_en"])}</p>']
    for section in SECTIONS:
        events = [event for event in edition['events'] if event['section'] == section]
        if not events:
            continue
        md += ['## ' + section, '']
        body.append('<h2>' + esc(section) + '</h2>')
        for event in events:
            md += ['### ' + event['headline'], '', '**What happened:**', '']
            body.append('<h3>' + esc(event['headline_en']) + '</h3>')
            for cid in event['claim_ids']:
                claim = claims[cid]
                refs = [sources[ref] for ref in claim['evidence_ids']]
                md_links = ' · '.join(f'[{s["publisher"]}](<{s["url"]}>)' for s in refs)
                html_links = ' · '.join(f'<a href="{esc(s["url"], quote=True)}">{esc(s["publisher"])}</a>' for s in refs)
                label = f'{claim["kind"]}; {claim["status"]}'
                md += [f'{claim["text"]} ({label}) {md_links}', '']
                body.append(f'<p>{esc(claim["text_en"])} <small>({esc(label)})</small><br>{html_links}</p>')
            md += ['**Why it matters:** ' + event['why_it_matters'], '']
            body.append('<p><strong>Why it matters:</strong> ' + esc(event['why_it_matters_en']) + '</p>')
            if event.get('media_framing'):
                md += ['**Media framing:** ' + event['media_framing'], '']
                body.append('<p><strong>Media framing:</strong> ' + esc(event['media_framing_en']) + '</p>')
            confidence = candidates[event['id']]['confidence']
            md += ['**Confidence:** ' + confidence, '']
            body.append('<p><small>Confidence: ' + esc(confidence) + '</small></p>')
    disclosures = list(dict.fromkeys(review.get('disclosures', {}).values()))
    if disclosures:
        md += ['## Evidence and Coverage Notes', '']
        body.append('<h2>Evidence and Coverage Notes</h2>')
        for note in disclosures:
            md += [note, '']
            body.append('<p>' + esc(note) + '</p>')
    body.append('<p>Attachments: complete Markdown briefing and supporting evidence archive.</p></body></html>')
    return '\n'.join(md), '\n'.join(body)


def build(folder: Path) -> dict:
    report = check(folder)
    if not report['ready']:
        raise ValueError('Release blocked; run check and resolve P0 / record editorial review')
    brief = folder / 'brief.md'
    delivery = folder / 'delivery'
    if brief.exists() or delivery.exists():
        raise ValueError('Published output already exists; preserve it and create a separate correction edition')
    markdown, body = render(folder)
    if digest(folder) != report['input_sha256']:
        raise ValueError('Inputs changed during rendering; review again')
    delivery.mkdir()  # exclusive reservation; a second build cannot overwrite the package
    with brief.open('x', encoding='utf-8') as stream:
        stream.write(markdown)
    (delivery / 'brief-full.md').write_text(markdown, encoding='utf-8')
    (delivery / 'email.html').write_text(body, encoding='utf-8')
    write(delivery / 'checks.json', report)
    with ZipFile(delivery / 'supporting-materials.zip', 'x', ZIP_DEFLATED) as archive:
        for name in (*INPUTS, 'evidence/review.json'):
            archive.write(folder / name, name)
        archive.write(delivery / 'checks.json', 'checks.json')
        archive.writestr('README.txt', 'Evidence package. Input metadata is not proof of factual truth.\nReview records identify who checked claims and translations.\nSee checks.json for disclosed limitations.\n')
    files = ['email.html', 'brief-full.md', 'supporting-materials.zip', 'checks.json']
    manifest = {'schema_version': 1, 'status': 'prepared_not_sent',
                'subject': 'codeX整理的每日新闻简报｜' + read(folder / 'edition.json')['issue_date'],
                'input_sha256': report['input_sha256'],
                'body': 'email.html', 'attachments': ['brief-full.md', 'supporting-materials.zip'],
                'sha256': {name: hashlib.sha256((delivery / name).read_bytes()).hexdigest() for name in files}}
    write(delivery / 'manifest.json', manifest)
    return manifest
