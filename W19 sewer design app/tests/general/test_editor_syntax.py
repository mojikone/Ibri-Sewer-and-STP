"""Every editor script parses (node --check): a stray character in one stops the whole interface (2026-11-23)."""
import glob, os, shutil, subprocess
import pytest

WEB = os.path.join(os.path.dirname(__file__), "..", "..", "web", "editor")


@pytest.mark.skipif(not shutil.which("node"), reason="node is not installed")
@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(WEB, "*.js"))), ids=os.path.basename)
def test_script_parses(path):
    r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[:400]
