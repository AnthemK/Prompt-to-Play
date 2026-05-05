#!/usr/bin/env python3
"""Local launcher for the Bead Pattern Converter static app."""

from __future__ import annotations

import argparse
import contextlib
import http.server
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_PORT = 8765
DEFAULT_BIND_HOST = "127.0.0.1"
DEFAULT_LAUNCH_HOST = "localhost"
SAFARI_PRIME_DELAY_SECONDS = 0.2
SAFARI_AUTORELOAD_DELAY_SECONDS = 0.28


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class ToolRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(TOOL_DIR), **kwargs)

    def end_headers(self) -> None:
        # Safari can aggressively reuse cached local JS/CSS. Force fresh reads
        # so palette and export fixes are visible immediately after restart.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self) -> None:
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, format: str, *args) -> None:
        # Keep launcher output focused on startup information.
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the Bead Pattern Converter local web app."
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_BIND_HOST,
        help="Host interface for the local server. Default: 127.0.0.1",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Preferred port for the local server. Default: {DEFAULT_PORT}",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the server without opening a browser tab.",
    )
    parser.add_argument(
        "--smoke-test-seconds",
        type=float,
        default=0.0,
        help="For local verification only: stop automatically after N seconds.",
    )
    parser.add_argument(
        "--allow-port-fallback",
        action="store_true",
        help="If the preferred port is busy, pick another port automatically.",
    )
    return parser.parse_args()


def is_port_open(host: str, port: int) -> bool:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def can_bind_port(host: str, port: int) -> bool:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def pick_fallback_port(host: str) -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_port(host: str, port: int, timeout_seconds: float) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_port_open(host, port):
            return True
        time.sleep(0.05)
    return False


def build_launch_url(bind_host: str, port: int) -> str:
    launch_host = bind_host
    if bind_host == DEFAULT_BIND_HOST:
        # Safari can reject explicit loopback IP URLs under some privacy and
        # HTTPS-only configurations. `localhost` is the safer launch target.
        launch_host = DEFAULT_LAUNCH_HOST

    return f"http://{launch_host}:{port}"


def open_browser_url(url: str) -> bool:
    try:
        completed = subprocess.run(
            ["open", url],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return completed.returncode == 0
    except Exception:
        return False


def _prime_browser_app_macos() -> bool:
    try:
        completed = subprocess.run(
            ["open", "-a", "Safari"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return completed.returncode == 0
    except Exception:
        return False


def _open_blank_safari_tab() -> bool:
    script_lines = [
        'tell application "Safari"',
        "  activate",
        "  if (count of windows) = 0 then",
        "    make new document",
        "  else",
        "    tell window 1",
        "      set newTab to make new tab at end of tabs",
        "      set current tab to newTab",
        "    end tell",
        "  end if",
        "end tell",
    ]
    cmd = ["osascript"]
    for line in script_lines:
        cmd.extend(["-e", line])
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return completed.returncode == 0
    except Exception:
        return False


def _reload_frontmost_safari_tab() -> bool:
    script_lines = [
        'tell application "Safari" to activate',
        "delay 0.08",
        'tell application "System Events"',
        '  tell process "Safari"',
        '    keystroke "r" using {command down}',
        "  end tell",
        "end tell",
    ]
    cmd = ["osascript"]
    for line in script_lines:
        cmd.extend(["-e", line])
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return completed.returncode == 0
    except Exception:
        return False


def _type_url_in_safari_address_bar(url: str) -> bool:
    script_lines = [
        "on run argv",
        "set targetURL to item 1 of argv",
        'tell application "Safari" to activate',
        "delay 0.15",
        'tell application "System Events"',
        '  tell process "Safari"',
    ]
    script_lines.extend(
        [
            '    keystroke "l" using {command down}',
            "    delay 0.08",
            "    set the clipboard to targetURL",
            '    keystroke "v" using {command down}',
            "    delay 0.05",
            "    key code 36",
            "  end tell",
            "end tell",
            "end run",
        ]
    )
    cmd = ["osascript"]
    for line in script_lines:
        cmd.extend(["-e", line])
    cmd.append(url)
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return completed.returncode == 0
    except Exception:
        return False


def open_tool_url(url: str) -> bool:
    if sys.platform == "darwin":
        if _prime_browser_app_macos():
            time.sleep(SAFARI_PRIME_DELAY_SECONDS)

        if _open_blank_safari_tab():
            time.sleep(0.12)
            if _type_url_in_safari_address_bar(url):
                time.sleep(SAFARI_AUTORELOAD_DELAY_SECONDS)
                _reload_frontmost_safari_tab()
                print("[Launcher] Browser open strategy: safari-blank-tab+address-bar")
                return True

        opened = open_browser_url(url)
        if opened:
            print("[Launcher] Browser open strategy: direct-open fallback")
        return opened

    return open_browser_url(url)


def main() -> int:
    args = parse_args()
    os.chdir(TOOL_DIR)

    port = args.port
    if not can_bind_port(args.host, port):
        if args.allow_port_fallback:
            port = pick_fallback_port(args.host)
            print(
                f"Preferred port {args.port} is busy. Falling back to {port}."
            )
        else:
            print(f"Preferred port {args.port} is already in use.")
            print("Close the process using that port, or rerun with:")
            print("  python3 launcher.py --allow-port-fallback")
            return 1

    with ReusableTCPServer((args.host, port), ToolRequestHandler) as httpd:
        bind_url = f"http://{args.host}:{port}"
        launch_stamp = int(time.time() * 1000)
        launch_query = urllib.parse.urlencode({"launch": str(launch_stamp)})
        launch_url = f"{build_launch_url(args.host, port)}/index.html?{launch_query}"
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        if not wait_for_port(args.host, port, timeout_seconds=2.0):
            print("Server failed to become ready in time.")
            return 1

        print("Bead Pattern Converter is running.")
        print(f"Tool folder: {TOOL_DIR}")
        print(f"Bind URL: {bind_url}")
        print(f"Open URL: {launch_url}")
        print("Press Ctrl+C to stop the server.")

        if not args.no_browser:
            opened = open_tool_url(launch_url)
            if not opened:
                print("[Launcher] Automatic browser open failed. Please open the URL above manually.")

        try:
            if args.smoke_test_seconds > 0:
                time.sleep(args.smoke_test_seconds)
            else:
                while thread.is_alive():
                    thread.join(timeout=0.5)
        except KeyboardInterrupt:
            print("\nStopping server...")
        finally:
            httpd.shutdown()
            thread.join(timeout=1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
