"""Fail if the live documents have fallen behind the work.

`_BRAIN/07_PROJECT_STATE.md` and `README.md` are what a new session reads to
learn current truth. They go stale quietly: nothing breaks, the build still
passes, and the next instance starts from a picture that is days old.

This compares the newest commit touching the work folders against the newest
commit touching each live document, and reports the lag.

    python _SETUP/check_live_docs.py          report, exit 1 if behind
    python _SETUP/check_live_docs.py --warn   report, always exit 0

Tag a commit subject with [minor] when it changes nothing a new session needs
to know — a layout tweak, a rename, a rebuild — and the check will not ask for
a live-document row on account of it.
"""
import subprocess
import sys

def _work_folders():
    """Every iteration folder that EXISTS, found rather than listed.

    This was a hardcoded list. It ended at "W9", then at "W11", and each time a new
    folder appeared the check went blind to it on the day it mattered most. A list of
    folders goes stale exactly when a new folder is created.
    """
    import os
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = sorted((d for d in os.listdir(root)
                    if re.fullmatch(r"W[0-9]+[a-z]?", d)
                    and os.path.isdir(os.path.join(root, d))),
                   key=lambda d: (len(d), d))
    return found + ["TUTORIALS"]


WORK = _work_folders()
LIVE = ["_BRAIN/00_CURRENT.md", "_BRAIN/07_PROJECT_STATE.md", "README.md"]


def _blob(commit, path):
    """The content hash of `path` at `commit`, or None."""
    out = subprocess.run(["git", "rev-parse", f"{commit}:{path}"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def rewound(path):
    """True when the newest commit touching `path` RESTORED CONTENT IT ALREADY HAD.

    THE FAILURE THIS EXISTS TO CATCH, 2026-09-07. The design line was reverted to a
    pre-W10 state, which rewrote all three live documents back to their content of
    seven days earlier. Every one of them then had a commit timestamp newer than the
    newest work commit, so this check printed "live documents are current" while a new
    session would have been told the design was W8/W9 with no mention that W10-W12 had
    ever existed.

    A check that measures WHEN a file was written, rather than WHAT IT SAYS, passes on a
    file that has been rewound. So: take the blob at the newest commit touching the file
    and look for that exact blob earlier in the file's own history. If it is there, the
    file was put back, not brought forward, and the commit does not count as an update.
    """
    log = subprocess.run(["git", "log", "-60", "--format=%H", "--", path],
                         capture_output=True, text=True).stdout.split()
    if len(log) < 2:
        return False
    now = _blob(log[0], path)
    if now is None:
        return False
    return any(_blob(c, path) == now for c in log[1:])


def last_commit(paths, skip_minor=False):
    """Newest commit touching `paths`.

    Rule 13 asks for an update on every SUBSTANTIVE change, and commit times
    alone cannot tell substantive from cosmetic. A commit whose subject
    carries [minor] says so explicitly and is skipped when looking for work
    that needs recording."""
    out = subprocess.run(
        ["git", "log", "-40", "--format=%H|%at|%ad|%s", "--date=short",
         "--"] + paths,
        capture_output=True, text=True).stdout.strip()
    for line in out.splitlines():
        h, ts, date, subject = line.split("|", 3)
        if skip_minor and "[minor]" in subject.lower():
            continue
        return dict(hash=h[:7], ts=int(ts), date=date, subject=subject)
    return None


def main(warn_only=False):
    work = last_commit(WORK, skip_minor=True)
    if work is None:
        print("no work commits found; nothing to check")
        return 0

    print(f"newest work commit   {work['hash']}  {work['date']}  "
          f"{work['subject'][:52]}")

    behind = []
    for doc in LIVE:
        live = last_commit([doc])
        if live is None:
            behind.append((doc, "never committed"))
            print(f"  {doc:<34} NEVER COMMITTED")
            continue
        lag = work["ts"] - live["ts"]
        if lag <= 0 and rewound(doc):
            # Fresh commit, rewound content. Treated as behind, and said out loud -
            # a silent pass here is the whole failure mode.
            state = "REWOUND - its newest commit restored older content"
            print(f"  {doc:<34} {live['hash']}  {live['date']}  {state}")
            behind.append((doc, state))
            continue
        if lag <= 0:
            state = "current"
        elif lag < 3600:
            state = f"BEHIND by {lag // 60} min"
        else:
            state = f"BEHIND by {lag // 3600} h"
        print(f"  {doc:<34} {live['hash']}  {live['date']}  {state}")
        if lag > 0:
            behind.append((doc, state))

    if not behind:
        print("\nlive documents are current")
        return 0

    print("\nA new session would read a stale picture. Update:")
    for doc, state in behind:
        print(f"  - {doc}  ({state})")
    print("Rule 12 in CLAUDE.md: update on every substantive change, and "
          "never end a session with these behind.")
    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main("--warn" in sys.argv))
