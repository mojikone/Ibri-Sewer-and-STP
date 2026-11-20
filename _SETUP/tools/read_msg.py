"""Read an Outlook .msg file without Outlook (2026-11-19: the team's report-structure email arrived as .msg).

    python read_msg.py "<file.msg>" [--save-attachments DIR]

Prints subject, sender, recipients, date and the plain-text body, and lists the attachments; with --save-attachments it writes them
to DIR. Needs olefile (pip install olefile). A .msg is an OLE compound file: each property is a stream named __substg1.0_<tag><type>,
type 001F = UTF-16 text, 0102 = binary; attachments sit in __attach_version1.0_#n storages."""
import argparse, os, re
import olefile

TAGS = {"subject": "0037001F", "from": "0C1A001F", "from_email": "0C1F001F", "to": "0E04001F", "cc": "0E03001F", "body": "1000001F", "headers": "007D001F"}


def read(path):
    o = olefile.OleFileIO(path)

    def s(tag, parent=None):
        for n in o.listdir():
            if n[-1].upper() == "__SUBSTG1.0_" + tag and ((parent is None and len(n) == 1) or (parent and n[0] == parent)):
                b = o.openstream(n).read(); return b.decode("utf-16-le", "replace") if tag.endswith("1F") else b
        return None
    out = {k: s(v) for k, v in TAGS.items()}
    m = re.search(r"^Date: (.*)$", out.get("headers") or "", re.M); out["date"] = m.group(1).strip() if m else None
    out["attachments"] = []
    for a in sorted({n[0] for n in o.listdir() if n[0].startswith("__attach")}):
        name = s("3707001F", a) or s("3704001F", a) or a; data = s("37010102", a) or b""
        out["attachments"].append((name, data))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("msg"); ap.add_argument("--save-attachments"); a = ap.parse_args()
    m = read(a.msg)
    for k in ("subject", "from", "from_email", "to", "cc", "date"): print(f"{k.upper():<11}", m.get(k))
    print("ATTACHMENTS", [(n, len(d)) for n, d in m["attachments"]]); print("\n" + (m.get("body") or ""))
    if a.save_attachments:
        os.makedirs(a.save_attachments, exist_ok=True)
        for n, d in m["attachments"]: open(os.path.join(a.save_attachments, os.path.basename(n)), "wb").write(d); print("saved", n)
