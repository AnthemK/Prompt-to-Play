#!/usr/bin/env python3
"""Local launcher for the lightweight TRPG simulator.

This script exists to keep the project's startup path lightweight: it starts the
Python backend and a static frontend server, then optionally opens the browser.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
# These ports are intentionally fixed so the frontend can call the backend
# without a runtime discovery step.
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8787
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5173
# Browser launch should prefer localhost to avoid browser-specific restrictions
# that sometimes treat raw loopback IP URLs less consistently.
FRONTEND_LAUNCH_HOST = "localhost"
# Safari startup timings are tuned for responsiveness while keeping reliability.
SAFARI_PRIME_DELAY_SECONDS = 0.2
SAFARI_AUTORELOAD_DELAY_SECONDS = 0.28


def is_port_in_use(host: str, port: int) -> bool:
    """Return whether a TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def wait_for_port(host: str, port: int, timeout_seconds: float) -> bool:
    """Poll a TCP port until it becomes available or times out."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_port_in_use(host, port):
            return True
        time.sleep(0.1)
    return False


def terminate_process(process: subprocess.Popen[bytes], name: str) -> None:
    """Terminate a child process gracefully, then force kill as a fallback."""
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        print(f"[Launcher] {name} 未在 3 秒内退出，执行强制结束。")
        process.kill()
        process.wait(timeout=2)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI for launcher and smoke-test usage."""
    parser = argparse.ArgumentParser(description="轻量级跑团模拟器 一键启动器")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="启动后不自动打开浏览器",
    )
    parser.add_argument(
        "--smoke-test-seconds",
        type=float,
        default=0.0,
        help="仅用于自检：启动后运行 N 秒自动退出",
    )
    return parser


def open_browser_url(url: str) -> bool:
    """Open one URL through the native OS launcher.

    Why this helper exists:
    - `open <url>` is the native LaunchServices path on macOS and tends to be
      more reliable for explicit `http://...` links.
    """
    try:
        completed = subprocess.run(
            ["open", url],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if completed.returncode == 0:
            return True
    except Exception:
        return False

    return False


def _prime_browser_app_macos() -> bool:
    """Prime Safari app first to avoid URL interception splash on cold launch.

    We intentionally avoid `about:blank` here because some environments reject
    non-http(s) external URLs and generate noisy AppleScript/webbrowser errors.
    """
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


def _open_url_in_new_safari_tab(url: str) -> bool:
    """Open URL in a brand-new Safari tab instead of overwriting current tab.

    Why this helper exists:
    - Users may keep important tabs open; startup should not replace them.
    - Safari AppleScript can create a new tab directly, avoiding manual-like
      address bar replacement behavior.
    """
    script_lines = [
        "on run argv",
        "set targetURL to item 1 of argv",
        'tell application "Safari"',
        "  activate",
        "  if (count of windows) = 0 then",
        "    make new document",
        "  end if",
        "  tell window 1",
        "    set newTab to make new tab at end of tabs with properties {URL:targetURL}",
        "    set current tab to newTab",
        "  end tell",
        "end tell",
        "end run",
    ]
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


def _reload_frontmost_safari_tab() -> bool:
    """Trigger one Safari reload to recover from HTTPS-only first-hop blocks.

    Why this helper exists:
    - In some Safari setups, first external navigation to local HTTP may be
      blocked, while a manual refresh succeeds immediately.
    - This helper emulates that manual refresh step so users do not need to do
      it themselves.
    """
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


def _frontmost_app_name_macos() -> str:
    """Return the frontmost macOS app name used for guarded URL retype fallback."""
    script = (
        'tell application "System Events" '
        "to get name of first application process whose frontmost is true"
    )
    try:
        completed = subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""

    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _retype_url_in_frontmost_browser(url: str) -> bool:
    """Retype URL in the frontmost browser address bar (macOS compatibility path).

    Why this exists:
    - Some Safari setups block externally-triggered local HTTP navigations
      (`WebKitErrorDomain:305`) while still allowing manual address-bar input.
    - This fallback intentionally mimics manual `Cmd+L -> paste URL -> Enter`,
      but only when a known browser is frontmost so we do not type into Terminal
      or Finder by accident.
    """
    frontmost_app = _frontmost_app_name_macos()
    browser_allowlist = {
        "Safari",
        "Google Chrome",
        "Chromium",
        "Brave Browser",
        "Arc",
        "Microsoft Edge",
        "Firefox",
    }
    if frontmost_app not in browser_allowlist:
        return False

    script_lines = [
        "on run argv",
        "set targetURL to item 1 of argv",
        "set targetApp to item 2 of argv",
        "set the clipboard to targetURL",
        'tell application targetApp to activate',
        "delay 0.15",
        'tell application "System Events"',
        "  tell process targetApp",
        '    keystroke "t" using {command down}',
        "    delay 0.05",
        '    keystroke "l" using {command down}',
        "    delay 0.05",
        '    keystroke "v" using {command down}',
        "    key code 36",
        "  end tell",
        "end tell",
        "end run",
    ]
    cmd = ["osascript"]
    for line in script_lines:
        cmd.extend(["-e", line])
    cmd.append(url)
    cmd.append(frontmost_app)
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


def open_game_url(url: str) -> bool:
    """Open game URL with macOS fallback for HTTPS-only local-nav edge cases."""
    if sys.platform == "darwin":
        # First activate Safari app so address-bar fallback can mimic manual
        # typing without showing temporary HTTPS-only interception pages.
        primed = _prime_browser_app_macos()
        if primed:
            # Give LaunchServices time to bring the app to foreground.
            time.sleep(SAFARI_PRIME_DELAY_SECONDS)

        # Prefer opening in a dedicated Safari tab, so existing tabs are never
        # overwritten by launcher startup navigation.
        if _open_url_in_new_safari_tab(url):
            # Safari may block the very first external local-http navigation in
            # strict HTTPS-only environments; one reload usually resolves it.
            time.sleep(SAFARI_AUTORELOAD_DELAY_SECONDS)
            auto_refreshed = _reload_frontmost_safari_tab()
            mode = "safari-new-tab+auto-reload" if auto_refreshed else "safari-new-tab"
            print(f"[Launcher] 浏览器打开策略：{mode}")
            return True

        # Try one "manual-like" retype fallback on macOS. This path mimics
        # what users do successfully by hand (`Cmd+T -> Cmd+L -> paste -> Enter`).
        if _retype_url_in_frontmost_browser(url):
            mode = "safari-prime-address-bar fallback" if primed else "address-bar fallback"
            print(f"[Launcher] 浏览器打开策略：{mode}")
            return True

        # Final fallback: direct URL open.
        opened = open_browser_url(url)
        if not opened:
            print("[Launcher] 浏览器打开失败，且地址栏回退也失败。")
        return opened
    return open_browser_url(url)


def main() -> int:
    """Start backend + frontend and block until shutdown."""
    args = build_parser().parse_args()

    backend_port_busy = is_port_in_use(BACKEND_HOST, BACKEND_PORT)
    frontend_port_busy = is_port_in_use(FRONTEND_HOST, FRONTEND_PORT)

    if backend_port_busy or frontend_port_busy:
        print("[Launcher] 端口冲突，无法启动。")
        if backend_port_busy:
            print(f"  - 后端端口占用：{BACKEND_HOST}:{BACKEND_PORT}")
        if frontend_port_busy:
            print(f"  - 前端端口占用：{FRONTEND_HOST}:{FRONTEND_PORT}")
        print("[Launcher] 请先关闭占用进程后重试。")
        return 1

    # The launcher keeps startup logic explicit so it is easy to review and
    # debug in a local VS Code workflow.
    backend_cmd = [sys.executable, str(PROJECT_ROOT / "backend" / "server.py")]
    frontend_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "frontend_server.py"),
        "--host",
        FRONTEND_HOST,
        "--port",
        str(FRONTEND_PORT),
        "--directory",
        str(PROJECT_ROOT / "frontend"),
    ]

    env = os.environ.copy()
    env["PYTHONPYCACHEPREFIX"] = str(PROJECT_ROOT / ".pycache")

    print("[Launcher] 正在启动后端服务...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(PROJECT_ROOT), env=env)

    try:
        if not wait_for_port(BACKEND_HOST, BACKEND_PORT, timeout_seconds=6):
            print("[Launcher] 后端启动超时。")
            terminate_process(backend_proc, "后端")
            return 1

        print("[Launcher] 正在启动前端静态服务...")
        frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(PROJECT_ROOT), env=env)

        if not wait_for_port(FRONTEND_HOST, FRONTEND_PORT, timeout_seconds=6):
            print("[Launcher] 前端启动超时。")
            terminate_process(frontend_proc, "前端")
            terminate_process(backend_proc, "后端")
            return 1

        # Use localhost for browser launch. The frontend server still binds on
        # the fixed port and backend API keeps its own explicit loopback URL.
        # Add a per-launch query so Safari is less likely to reuse a stale
        # cached index page or an old DOM snapshot.
        launch_stamp = int(time.time() * 1000)
        launch_query = urllib.parse.urlencode({"launch": str(launch_stamp)})
        game_url = f"http://{FRONTEND_LAUNCH_HOST}:{FRONTEND_PORT}/index.html?{launch_query}"
        print("[Launcher] 启动成功。")
        print(f"[Launcher] 游戏地址：{game_url}")
        print(f"[Launcher] 备用地址：http://{FRONTEND_HOST}:{FRONTEND_PORT}/index.html")
        print("[Launcher] 按 Ctrl+C 可关闭所有服务。")

        if not args.no_browser:
            opened = open_game_url(game_url)
            if not opened:
                print("[Launcher] 自动打开浏览器失败，请手动复制上方游戏地址访问。")

        if args.smoke_test_seconds > 0:
            time.sleep(args.smoke_test_seconds)
            print("[Launcher] smoke-test 模式结束，准备退出。")
            terminate_process(frontend_proc, "前端")
            terminate_process(backend_proc, "后端")
            return 0

        while True:
            if backend_proc.poll() is not None:
                print("[Launcher] 后端进程已退出，准备清理并结束。")
                terminate_process(frontend_proc, "前端")
                return 1
            if frontend_proc.poll() is not None:
                print("[Launcher] 前端进程已退出，准备清理并结束。")
                terminate_process(backend_proc, "后端")
                return 1
            time.sleep(0.4)

    except KeyboardInterrupt:
        print("\n[Launcher] 收到中断，正在关闭服务...")
        try:
            terminate_process(frontend_proc, "前端")
        except UnboundLocalError:
            pass
        terminate_process(backend_proc, "后端")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
