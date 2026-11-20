---
name: wa-link-one-sender-at-a-time
description: "The WhatsApp linked sender (wa.js) takes one connection at a time; a send from another session on the same link fails both with \"connection closed (440)\""
metadata:
  node_type: memory
  type: reference
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-19T14:56:31.177Z
---

`C:\Users\mojtaba\wa_link\wa.js` holds a single linked-device session. If two `wa.js` processes run at once, WhatsApp closes the older connection with code 440 and that send fails. This happens when another Claude session, such as the Batinah Block 2 work, sends at the same time.

**How to apply:**
- Before a send, list the running `node.exe` processes whose command line contains `wa.js`. If one belongs to another session, wait for it to exit, never kill it, and then send.
- A send that reports "no acknowledgement" during a clash may not have arrived. Resend it once the link is free.
- Seen on 2026-11-19 with R12: the Word send failed twice with 440 while a Block 2 package was uploading.

Related: [[w18-r11-report-brief]].
