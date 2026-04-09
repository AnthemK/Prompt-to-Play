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
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
# These ports are intentionally fixed so the frontend can call the backend
# without a runtime discovery step.
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8787
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5173


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
        "-m",
        "http.server",
        str(FRONTEND_PORT),
        "-d",
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

        game_url = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}/index.html"
        print("[Launcher] 启动成功。")
        print(f"[Launcher] 游戏地址：{game_url}")
        print("[Launcher] 按 Ctrl+C 可关闭所有服务。")

        if not args.no_browser:
            webbrowser.open(game_url)

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
