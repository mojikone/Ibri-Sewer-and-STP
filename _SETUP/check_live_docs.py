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

WORK = ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "TUTORIALS"]
LIVE = ["_BRAIN/07_PROJECT_STATE.md", "README.md"]


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
