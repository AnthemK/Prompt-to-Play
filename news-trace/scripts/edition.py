"""One entry point for edition setup, checking, review preparation and packaging."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from briefing.model import initialize, write
from briefing.render import build
from briefing.validate import check


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='Create an empty edition without overwriting existing files')
    init.add_argument('folder', type=Path)
    init.add_argument('--date', required=True)
    validate = commands.add_parser('check', help='Print P0/P1 and coverage findings')
    validate.add_argument('folder', type=Path)
    validate.add_argument('--content-only', action='store_true', help='Pre-review check; does not authorize publication')
    validate.add_argument('--output', type=Path)
    review = commands.add_parser('review-template', help='Create a pending, hash-bound editorial checklist')
    review.add_argument('folder', type=Path)
    publish = commands.add_parser('build', help='Build Markdown and English email attachments; does not send')
    publish.add_argument('folder', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            initialize(args.folder, args.date)
            print('Draft created:', args.folder)
        elif args.command == 'check':
            result = check(args.folder, require_review=not args.content_only)
            if args.output:
                # Findings must not overwrite an input, review, or historical artifact.
                if args.output.exists() or args.output.resolve() in {(args.folder / name).resolve() for name in ('edition.json','evidence/input.json','evidence/claims.json','evidence/selection-ledger.json','evidence/review.json')}:
                    raise ValueError('Output exists or is a reserved input path')
                write(args.output, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            raise SystemExit(0 if result['passed'] else 1)
        elif args.command == 'review-template':
            result = check(args.folder, require_review=False)
            if not result['passed']:
                raise ValueError('Resolve structural P0 findings before preparing editorial review')
            target = args.folder / 'evidence/review.json'
            if target.exists():
                raise ValueError('Review already exists; revise it explicitly after checking changed content')
            write(target, {'schema_version': 1, 'decision': 'pending', 'input_sha256': result['input_sha256'],
                           'reviewed_by': '', 'reviewed_at': '', 'checks_completed': [],
                           'disclosures': {row['code']: '' for row in result['findings'] if row['severity'] == 'P1'}})
            print('Pending review created:', target)
        elif args.command == 'build':
            print(json.dumps(build(args.folder), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
