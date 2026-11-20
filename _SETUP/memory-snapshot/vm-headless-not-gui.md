---
name: vm-headless-not-gui
description: "Drive the SewerGEMS VM from the host's command line (VBoxManage guestcontrol), never by clicking in its window; guest logon needs the engineer's password"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-16T14:46:14.569Z
---

To start or run anything inside the Win10 VM (the bridge watcher, a job), use `VBoxManage guestcontrol Win10 ...` from the host. Do not use computer use to click inside the VirtualBox window.

**Why:** on 2026-11-16 the engineer stopped a computer-use attempt on the VM window and said "go headless".

**How to apply:**
- The guest user is `Moji` (guest additions 7.2.6). Guest control refuses a logon without a password ("The specified user was not able to logon on guest"), and I must not type the password.
- So give the engineer the one-line `guestcontrol run` command to paste with his password into a host terminal, and he keeps that terminal open while jobs run.
- If the job fails on the SewerGEMS licence in that non-console logon, fall back to the in-VM PowerShell watcher.

**Traps paid for on 2026-11-16:**
- **The bridge's `out\<job>.txt` is UTF-16.** `grep "__EXIT__"` never matches it. A background wait built on that grep missed a job that failed after 5 minutes, and about 50 minutes were lost. Match the bytes `_\x00_\x00E\x00X\x00I\x00T` in Python instead.
- **The watcher does not refresh `_alive.txt` while a job runs**, so an old heartbeat during a job is normal.
- **Bringing the VM forward:** `open_application "Virtualboxvm"` starts a second VirtualBoxVM.exe with no VM named, which leaves harmless "You must specify a machine" boxes behind.
- **Typing into the VM:** the `type` action does not reach the guest; one `key` action per character does.

Related: the bridge description in the global CLAUDE.md, and [[long-runs-detached]].
