# SewerGEMS through its API (the offline VM bridge)

Reference: `scripts/sewergems_api/` (C# helpers in `lib/*.cs`, `load.ps1`, `watcher.ps1`, `compile_check.ps1`,
`lib/build_final.ps1`, example jobs). The machine set-up is in the user's global CLAUDE.md ("SewerGEMS through its API,
inside the offline virtual machine"); read it first.

## Contents
1. Where it runs and how a job travels
2. Writing a job
3. Loads in the model
4. The referee build of a design
5. Traps

## 1. Where it runs and how a job travels

- SewerGEMS CONNECT 10.4 runs in a VirtualBox Windows 10 guest with **no internet**. Never add an adapter or NAT, and never
  download anything inside the guest.
- Host `D:\VBOX` is the guest's `\\VBOXSVR\VBOX`.
  - Drive the VM headless (`VBoxManage guestcontrol`); never click in its window.
  - Logging on needs the engineer's password, so give them the command.
- The engineer starts `bridge\watcher.ps1` in the guest. It then:
  - runs every `bridge\jobs\*.ps1` in name order;
  - writes `bridge\out\<job>.txt`, ending `__EXIT__ <code>`;
  - moves the job to `done\`;
  - rewrites `out\_alive.txt` every 2 s.
- **Before dropping a job:**
  - check that heartbeat. It stops while a job runs, so treat a job as hung only after about 35 minutes with no output;
  - run `compile_check.ps1` on the host. It compiles `lib\*.cs` against copies of the DLLs in `refs\` and executes nothing.
  - The project repo's copy of `sewergems_api\` is the source of record. Copy it into the bridge.
- **Long jobs:** Colebrook-White runs about 8 times slower than Manning (about 44 minutes per design). Drop the job and watch
  `out\` with a monitor rather than waiting inside one command.

## 2. Writing a job

1. Check free space on C: and stop under 2 GB.
2. Set the case variables, then dot-source `\\VBOXSVR\VBOX\bridge\lib\load.ps1`. It resolves the OpenFlows/Haestad
   assemblies in the SewerGEMS folder and compiles the C# helpers with `Add-Type`. Nothing is installed.
3. `[OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession(...)`, then `Open` a **copy** under `C:\<Project>Work\...`.
4. Do the work, then `SaveAs` a **new** file (R0, R1 ...). Never overwrite the modeller's file; only ADD files to the model
   share.
5. Export CSVs to `\\VBOXSVR\VBOX\bridge\out\...`, where the host reads them.
6. Write job files with a file-writing tool, not through Python strings or a bash heredoc (`\f`, `\b` and leading
   backslashes get eaten). Grep each one for `\\VBOXSVR` before dropping it.

## 3. Loads in the model

- **Unit sanitary loads.** Use load definition 1: one unit load per unit, with units = the flow. Pattern loads are never
  peaked by the Extreme Flow Setup, so a pattern-loaded model under-sizes every pipe without any error (Ibri, W17 R2).
- **One sanitary load per manhole.** LoadBuilder writes 2–4 rows on about 2,000 manholes even with Override. Merge them into
  one after every reload, with the totals unchanged. The only second load on a manhole is a transfer.
- **Peaking:** the Extreme Flow Setup's table works on each pipe's cumulative upstream unit load. Ibri's
  "Peltier100-Merriamck" has Peltier to 1 L/s and Merrimack above. A row 1.001 L/s → 3.56 makes the switch a step instead of
  a ramp.
- **Infiltration:** 720 L/day per km on the conduits (G201 p72).
- **Years:**
  - one year alternative per model year. Ibri R4 held 13 years, 2031–2091 every five years;
  - **create each new year with `Copy(<loaded alternative id>)`.** `Add(parent)` breaks the second year: a new child could
    not be read once a sibling held records (Ibri jobs 060–065);
  - set every year from `manhole_loads.csv`, then check that stored = file. Ibri 2031: 22,391 m³/d carried; 2056: 37,892;
    14,989 manholes loaded.
- **Transfers between systems:** the outfall flow of a pumped system goes in as an *additional* load at the receiving
  manhole. It adds to the loads there and is not peaked again.
  - Export the outfall flows of every year, then turn them into transfer rows (`make_transfers.py`; `final_sg_inputs.py` for
    the final cases).

## 4. The referee build of a design

Reference: `lib/build_final.ps1` + `lib/FinalBuild.cs` (Ibri jobs 080–094).

- Inputs from `final_sg_inputs.py`, in the model's own element ids.
- Set every conduit's size and inverts.
- **Each lift** is built as station manhole → 1 m stub → outfall. Its pipe is switched off, and its flow is pumped to the
  next manhole as a transfer.
- **Gravity joins are carried as transfers** (see trap 5).
- Rename every element.
- Load the transfers of the design year and of the check years.
- Then run **analysis only**. There is no design run, because the sizes are the design. Export, read back, and compare with
  `final_sg_compare.py`.

## 5. Traps

1. **Set every scenario's alternatives and calculation options to LOCAL explicitly.** An inherited DESIGN option re-sized the
   pipes in every analysis year.
2. **Repeat a design until no pipe size changes, and fail the job if an analysis changes a size.**
3. **The typed API's diameter is stale for catalogue pipes.** Read the size reference.
4. **The 10.4 API refuses text user fields.** Use the element Notes.
5. **Joins can't be built as new sewers through the API.** SewerGEMS 10.4 solves join sewers created that way at 0.305 m
   depth and 5–7 m/s, with backwater upstream.
6. **Stored flows are cfs,** while the typed API returns display units.
7. **A conduit's start and stop need not follow the flow.** Check both end nodes when reconnecting.
8. **A load on a manhole without a load row fails the job** (Ibri jobs 060–066). Send orphan plots to the nearest loaded
   manhole before loading.
