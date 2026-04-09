#!/usr/bin/env python3
"""Small static frontend server with no-cache headers.

Why this file exists:
- Safari may aggressively reuse cached HTML or old DOM snapshots for local
  HTTP pages.
- The default `python -m http.server` is convenient but does not let this
  project control cache headers.
- The launcher needs a tiny, reviewable static server that always serves the
  latest frontend shell and assets during local play.
"""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class NoStoreFrontendHandler(SimpleHTTPRequestHandler):
    """Serve frontend files while telling the browser not to cache responses."""

    server_version = "LiteTRPGSimFrontend/1.0"

    def end_headers(self) -> None:
        """Attach cache-busting headers before the response is finalized."""
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def build_parser() -> argparse.ArgumentParser:
    """Expose a tiny CLI so the launcher can control host, port, and directory."""
    parser = argparse.ArgumentParser(description="Lite TRPG Sim frontend static server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=5173, help="Port to bind")
    parser.add_argument("--directory", default="frontend", help="Directory to serve")
    return parser


def main() -> int:
    """Start the no-cache static server and block forever."""
    args = build_parser().parse_args()
    directory = Path(args.directory).resolve()
    handler = partial(NoStoreFrontendHandler, directory=str(directory))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"[LiteTRPGSim] Frontend static server running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
