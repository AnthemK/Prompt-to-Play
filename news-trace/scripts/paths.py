"""Project locations anchored to this file, independent of the working directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CONFIG = ROOT / "config"
MEMORY = ROOT / "memory"
