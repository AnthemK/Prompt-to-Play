"""HTTP boundary for the local lightweight TRPG simulator backend.

The server intentionally stays very small: routing, JSON parsing, and error
translation live here, while all game/state logic stays inside `game.engine`.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from game.engine import GameEngine

HOST = "127.0.0.1"
PORT = 8787

ENGINE = GameEngine()

GAME_VIEW_RE = re.compile(r"^/api/game/([a-zA-Z0-9]+)/view$")
GAME_DEBUG_RE = re.compile(r"^/api/game/([a-zA-Z0-9]+)/debug$")
GAME_ACTION_RE = re.compile(r"^/api/game/([a-zA-Z0-9]+)/action$")
GAME_SAVE_RE = re.compile(r"^/api/game/([a-zA-Z0-9]+)/save$")
GAME_DELETE_RE = re.compile(r"^/api/game/([a-zA-Z0-9]+)$")


class Handler(BaseHTTPRequestHandler):
    """Serve the small JSON API consumed by the browser frontend."""

    server_version = "LiteTRPGSimServer/1.2"

    def log_message(self, format: str, *args: Any) -> None:
        """Silence the default access log to keep local output readable."""
        return

    def _set_headers(self, status: int = 200) -> None:
        """Write shared CORS + JSON headers for every response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json_response(self, payload: dict[str, Any], status: int = 200) -> None:
        """Send a JSON body with the standard response headers."""
        self._set_headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _read_json(self) -> dict[str, Any]:
        """Read and validate a JSON object body from the request stream."""
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b"{}"
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("invalid_json")
        if not isinstance(parsed, dict):
            raise ValueError("invalid_json")
        return parsed

    def do_OPTIONS(self) -> None:
        """Handle the browser's CORS preflight requests."""
        self._set_headers(204)

    def do_GET(self) -> None:
        """Serve read-only API endpoints."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/meta":
            story_id = query.get("story_id", [None])[0]
            try:
                meta = ENGINE.meta(story_id=story_id)
            except KeyError:
                self._json_response({"ok": False, "error": "story_not_found"}, status=404)
                return
            self._json_response({"ok": True, "data": meta})
            return

        match = GAME_VIEW_RE.match(path)
        if match:
            session_id = match.group(1)
            try:
                view = ENGINE.view(session_id)
            except KeyError:
                self._json_response({"ok": False, "error": "session_not_found"}, status=404)
                return
            self._json_response({"ok": True, "data": view})
            return

        match = GAME_DEBUG_RE.match(path)
        if match:
            session_id = match.group(1)
            limit_raw = query.get("limit", ["200"])[0]
            try:
                limit = int(limit_raw)
            except (TypeError, ValueError):
                limit = 200
            try:
                debug_data = ENGINE.debug_trace(session_id, limit=limit)
            except KeyError:
                self._json_response({"ok": False, "error": "session_not_found"}, status=404)
                return
            self._json_response({"ok": True, "data": debug_data})
            return

        self._json_response({"ok": False, "error": "not_found"}, status=404)

    def do_POST(self) -> None:
        """Serve mutating endpoints such as new game, action, load, and save."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/game/new":
            try:
                body = self._read_json()
                player_name = str(body.get("player_name", ""))
                profession_id = str(body.get("profession_id", ""))
                story_id_raw = body.get("story_id")
                story_id = str(story_id_raw) if isinstance(story_id_raw, str) and story_id_raw.strip() else None
                view = ENGINE.new_game(player_name, profession_id, story_id=story_id)
                self._json_response({"ok": True, "data": view})
            except KeyError:
                self._json_response({"ok": False, "error": "story_not_found"}, status=404)
            except ValueError as exc:
                self._json_response({"ok": False, "error": str(exc)}, status=400)
            return

        if path == "/api/game/load":
            try:
                body = self._read_json()
                save_data = body.get("save_data")
                view = ENGINE.load(save_data)
                self._json_response({"ok": True, "data": view})
            except ValueError as exc:
                self._json_response({"ok": False, "error": str(exc)}, status=400)
            return

        match = GAME_ACTION_RE.match(path)
        if match:
            session_id = match.group(1)
            try:
                body = self._read_json()
                action_id = str(body.get("action_id", "")).strip()
                if not action_id:
                    self._json_response({"ok": False, "error": "missing_action_id"}, status=400)
                    return
                view = ENGINE.act(session_id, action_id)
                self._json_response({"ok": True, "data": view})
            except KeyError:
                self._json_response({"ok": False, "error": "session_not_found"}, status=404)
            except ValueError as exc:
                self._json_response({"ok": False, "error": str(exc)}, status=400)
            return

        match = GAME_SAVE_RE.match(path)
        if match:
            session_id = match.group(1)
            try:
                save_data = ENGINE.save(session_id)
            except KeyError:
                self._json_response({"ok": False, "error": "session_not_found"}, status=404)
                return
            self._json_response({"ok": True, "data": save_data})
            return

        self._json_response({"ok": False, "error": "not_found"}, status=404)

    def do_DELETE(self) -> None:
        """Delete an in-memory session without touching browser save slots."""
        parsed = urlparse(self.path)
        path = parsed.path
        match = GAME_DELETE_RE.match(path)
        if not match:
            self._json_response({"ok": False, "error": "not_found"}, status=404)
            return
        session_id = match.group(1)
        ENGINE.delete(session_id)
        self._json_response({"ok": True, "data": {"deleted": True}})


def run() -> None:
    """Start the threaded local HTTP server and keep it alive."""
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[LiteTRPGSim] Backend running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[LiteTRPGSim] Backend stopped")


if __name__ == "__main__":
    run()
