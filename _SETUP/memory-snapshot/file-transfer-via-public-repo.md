---
name: file-transfer-via-public-repo
description: "User works remotely and transfers files via the public GitHub repo; accepts exposure after one warning — warn once, then push on confirmation"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 413b098f-38f9-4a93-9820-2b7c34af7f5e
  modified: 2026-08-14T18:03:47.531Z
---

When the user (working remotely) asks to push files to the project GitHub repo so they can download them, they use the public repo deliberately as a file-transfer channel — including client documents (`_CLIENT/` folder created 2026-08-14 for Inception R0 package, exposure explicitly accepted on record).

**Why:** SendUserFile chat attachments were not downloadable in their client; a private-repo alternative I proposed was rejected — they prefer the single existing repo.

**How to apply:** State the public-exposure risk once, concisely. If they confirm (e.g. "I am aware, push them"), push without further resistance to `_CLIENT/` (client docs) or the appropriate folder, add the README state row, and note the user-confirmed exposure in the commit message. Do not repeat the warning on later transfers of similar material.
