"""The frozen reference files (tests/fixtures/): W18's inputs and outputs and SewerGEMS's exports, copied once by
tools/freeze_fixtures.py. A file may be stored gzipped; callers name it without the .gz."""
import gzip, json, os, shutil
import pandas as pd

FIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "fixtures")


def path(rel):
    p = os.path.join(FIX, rel)
    return p if os.path.exists(p) else p + ".gz"


def read_csv(rel, **kw):
    return pd.read_csv(path(rel), **kw)


def materialize(rel, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    src = path(rel)
    if src.endswith(".gz"):
        with gzip.open(src, "rb") as f, open(dest, "wb") as g: shutil.copyfileobj(f, g)
    else:
        shutil.copyfile(src, dest)
    return dest


def manifest():
    return json.load(open(os.path.join(FIX, "MANIFEST.json"), encoding="utf-8"))
