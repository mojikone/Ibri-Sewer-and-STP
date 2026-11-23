"""Tests never touch the engineer's own assistant files (folder list, spending limits, ledger): they get a temporary
folder, set before any sewerapp module reads the paths. The e2e server inherits these through its environment."""
import os, tempfile

_D = tempfile.mkdtemp(prefix="w19_tests_")
os.environ.setdefault("W19_AGENT_FOLDERS", os.path.join(_D, "agent_folders.json"))
os.environ.setdefault("W19_ASSISTANT_LIMITS", os.path.join(_D, "assistant_limits.json"))
os.environ.setdefault("W19_ASSISTANT_LEDGER", os.path.join(_D, "assistant_usage.json"))
