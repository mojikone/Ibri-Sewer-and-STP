"""Talk to the QGIS MCP plugin's own socket directly, without the MCP relay.

The plugin (qgis_mcp_plugin 0.14) listens on localhost:9876 and speaks length-prefixed
JSON: a 4-byte big-endian length, then {"type": <command>, "params": {...}}; the reply
is framed the same way. This is exactly what the relay does; it is used here when the
relay in the chat session has hung (2026-09-14) and the maps still have to be exported.

    python qgis_direct.py ping
    python qgis_direct.py exec "print(QgsProject.instance().fileName())"
    python qgis_direct.py file some_script.py          # exec the file's text in QGIS
"""
import json
import os
import socket
import struct
import sys

HOST, PORT = "localhost", 9876
HEADER = struct.Struct(">I")


def call(cmd_type, params=None, timeout=900.0):
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    try:
        payload = json.dumps({"type": cmd_type, "params": params or {}}).encode("utf-8")
        s.sendall(HEADER.pack(len(payload)) + payload)
        head = b""
        while len(head) < 4:
            chunk = s.recv(4 - len(head))
            if not chunk:
                raise ConnectionError("closed before the reply header")
            head += chunk
        n = HEADER.unpack(head)[0]
        body = bytearray()
        while len(body) < n:
            chunk = s.recv(min(65536, n - len(body)))
            if not chunk:
                raise ConnectionError("closed mid-reply")
            body.extend(chunk)
        return json.loads(bytes(body).decode("utf-8"))
    finally:
        s.close()


def exec_code(code, timeout=900.0):
    r = call("execute_code", {"code": code}, timeout=timeout)
    out = r.get("result", r)
    if isinstance(out, dict):
        if out.get("stdout"):
            print(out["stdout"], end="" if out["stdout"].endswith("\n") else "\n")
        if out.get("stderr"):
            print("STDERR:", out["stderr"])
        if out.get("error") or out.get("traceback"):
            print("ERROR:", out.get("error"), out.get("traceback", ""))
    else:
        print(out)
    return r


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "ping"
    if what == "ping":
        print(call("ping"))
    elif what == "exec":
        exec_code(sys.argv[2])
    elif what == "file":
        exec_code(open(sys.argv[2], encoding="utf-8").read())
