---
name: whatsapp-send-via-playwright
description: "Sending large files to the engineer's WhatsApp when he is away from the PC - Playwright window linked by phone-number code; Claude in Chrome cannot (10 MB cap, often not connected)"
metadata:
  node_type: memory
  type: project
  originSessionId: dacc1452-7243-4d99-a7ca-492275e413da
  modified: 2026-10-03T08:35:52.462Z
---

Worked 2026-10-03: report docx/pdf, deck and a 255 MB zip sent to his contact "Me MCI" from his own
WhatsApp account (ask him for the account's number each time; never write it into a file - the memory
snapshot in the repo is public).

**Why this route:** the Claude in Chrome upload tool caps each file at 10 MB and was not connected;
Playwright cannot attach to his running Chrome (Chrome 136+ refuses remote debugging of the default
profile); away from the PC he cannot scan a QR on the same phone.

**How to apply:** Playwright `launch_persistent_context(channel="chrome", headless=False)` with a
SHORT profile path (`%LOCALAPPDATA%\wa_pw`; a deep Temp path breaks WhatsApp's IndexedDB: "database
error, relink your device") → web.whatsapp.com → "Log in with phone number" → he enters the 8-character
code (it rotates every ~3 min; he gets no request, he starts it in Linked devices → Link a device → Link
with phone number instead) → close the "What's new" dialog → search the chat, check the header → Attach
→ Document via `expect_file_chooser` + `set_files` (no size cap) → button `aria-label="Send 4 selected"`
→ wait for "Forward media" on every message → Menu → Log out → delete the profile with
`rd /s /q "\\?\<path>"`. Get his yes for the device link and the send first. Script pattern kept in the
session scratchpad `wa/pw_server.py` (command files executed in a live window).
