/* W19 v8 (2026-11-24): accounts. Over the shared address the sign-in is Cloudflare Access's (Google, an emailed code...);
   the app shows who is signed in with Sign out, keeps each account's projects on the server (My projects, from any
   device), and gives the administrator the Users list. On this computer nothing changes. Server: api/accounts.py. */

state.me = { mode: "local" };

/* an expired sign-in: Cloudflare answers the app's requests with a redirect to its sign-in page, which a request cannot
   follow; say so plainly instead of "the server cannot be reached" */
(function signInExpiry() {
  const f0 = window.fetch.bind(window);
  window.fetch = async function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    if (!(state.me && state.me.mode === "user" && url.startsWith(API))) return f0(input, init);
    const r = await f0(input, Object.assign({}, init || {}, { redirect: "manual" }));
    if (r.type !== "opaqueredirect") return r;
    const msg = "Your sign-in has expired: reload the page to sign in again.";
    return new Response(JSON.stringify({ detail: msg }), { status: 401, headers: { "Content-Type": "application/json" } });
  };
})();

const _when = t => t ? new Date(t * 1000).toLocaleString() : "";

async function loadMe() {
  try { state.me = await jget("/me"); } catch (e) { return; }
  const m = state.me, right = $("#rb-right");
  document.body.dataset.me = m.mode;
  if (!right || $("#me-box")) return;
  let h = "";
  if (m.mode === "user") h = `<span id="me-chip" data-testid="me-chip" title="Signed in as ${esc(m.email)}">${esc(m.email)}</span>` +
      (m.admin ? `<button id="me-users" data-testid="me-users" class="small" title="Everyone who has signed in, their projects and today's assistant spending">Users</button>` : "") +
      `<a id="me-out" data-testid="sign-out" href="${esc(m.logout)}" title="Sign out of this site on this device">Sign out</a>`;
  else if (m.mode === "local" && m.accounts) h = `<span id="me-chip" data-testid="me-chip" title="Opened on this computer: no sign-in needed">This computer</span>` +
      `<button id="me-users" data-testid="me-users" class="small" title="Everyone who has signed in through the site's address">Users</button>`;
  if (!h) return;
  const box = document.createElement("div"); box.id = "me-box"; box.innerHTML = h; right.prepend(box);
  const u = $("#me-users"); if (u) u.onclick = () => openUsers();
  const rb = $("#rb-recent");
  if (rb && m.mode === "user") { rb.querySelector("span").textContent = "My projects"; rb.title = "Your projects, kept on the server under your account: open them from any device"; }
}

/* My projects: a signed-in account's projects from the server (the browser's own list stays for this computer and for
   visitors when accounts are off) */
const _openRecentBrowser = openRecent;
openRecent = async function () {
  if (!state.me || state.me.mode !== "user") return _openRecentBrowser();
  const d = dlg("dlg-mine", "My projects", false), b = d.querySelector(".body");
  d.querySelector("[data-act=ok]").hidden = true;
  const draw = async () => {
    let L = [];
    try { L = await jget("/projects"); } catch (e) { b.innerHTML = `<p class="err">${esc(e.message)}</p>`; return; }
    b.innerHTML = `<p class="muted">Kept on the server under ${esc(state.me.email)}: open them from any device. Only you, and the app's administrator, can open them.</p>` +
      (L.length ? L.map(r => `<div class="rec"><button data-id="${esc(r.id)}" data-testid="mine-${esc(r.id)}">${esc(r.name || r.id)}</button> <span class="muted">${_when(r.t)}</span> ` +
        `<button class="small mine-del" data-del="${esc(r.id)}" data-testid="mine-del-${esc(r.id)}" title="Remove it from the server">Remove</button></div>`).join("")
        : `<p class="muted">None yet: each project you make, open or import is kept here.</p>`);
  };
  await draw(); d.hidden = false;
  d.onclick = e => {
    if (e.target.dataset.act === "close") { d.hidden = true; return; }
    const del = e.target.closest("button[data-del]");
    if (del) {
      if (!del.dataset.armed) { del.dataset.armed = "1"; del.textContent = "Click again to remove"; return; }
      const id = del.dataset.del;
      enqueue(async () => {
        await jpost(`/projects/${encodeURIComponent(id)}/delete`);
        if (state.pid === id) { try { localStorage.removeItem(SESS_KEY); } catch (x) { /* */ } location.replace(location.pathname); return; }
        await draw(); toast("Removed from the server.", "info");
      });
      return;
    }
    const x = e.target.closest("button[data-id]"); if (!x) return; d.hidden = true;
    enqueue(() => withBusy("Opening...", async () => { await openProject(await jget(`/projects/${encodeURIComponent(x.dataset.id)}`)); }));
  };
};

async function openUsers() {
  const d = dlg("dlg-users", "Users", true), b = d.querySelector(".body");
  d.querySelector("[data-act=ok]").hidden = true;
  let U = [];
  try { U = await jget("/admin/users"); } catch (e) { toast(e.message); return; }
  b.innerHTML = `<p class="muted">Everyone who has signed in through the site's address. Who may sign in, and how (Google, an emailed code...), is set in Cloudflare Access.</p>` +
    (U.length ? `<table class="tbl users-tbl" data-testid="users-table"><thead><tr><th>Email</th><th>First seen</th><th>Last seen</th><th>Projects</th><th>Assistant today (USD)</th></tr></thead><tbody>` +
      U.map(u => `<tr><td>${esc(u.email)}</td><td>${_when(u.first)}</td><td>${_when(u.last)}</td><td>${u.projects.map(p => `<button class="small" data-id="${esc(p.id)}">${esc(p.name || p.id)}</button>`).join(" ") || "-"}</td><td>${(u.spent_today_usd || 0).toFixed(2)}</td></tr>`).join("") +
      `</tbody></table>` : `<p class="muted">No one has signed in yet.</p>`);
  d.hidden = false;
  d.onclick = e => {
    if (e.target.dataset.act === "close") { d.hidden = true; return; }
    const x = e.target.closest("button[data-id]"); if (!x) return; d.hidden = true;
    enqueue(() => withBusy("Opening...", async () => { await openProject(await jget(`/projects/${encodeURIComponent(x.dataset.id)}`)); }));
  };
}

(function wireAccounts() {
  const go = () => setTimeout(loadMe, 0);
  if (document.readyState === "complete") go(); else addEventListener("load", go);
})();
