"""
zwalker - Automated walkthrough generator for Z-machine games
"""

import os as _os
from pathlib import Path as _Path


def _load_dotenv_file():
    """Load the repo's .env (e.g. ANTHROPIC_API_KEY) so runs don't need it
    pre-exported. Prefers python-dotenv; falls back to a tiny parser so the
    .env still loads without the dependency. Existing env vars win."""
    env_path = _Path(__file__).resolve().parent.parent / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except Exception:
        pass
    try:
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            if key.startswith("export "):
                key = key[len("export "):].strip()
            _os.environ.setdefault(key, val.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


_load_dotenv_file()

from .zmachine import ZMachine
from .walker import GameWalker

__version__ = "0.1.0"
__all__ = ["ZMachine", "GameWalker"]
