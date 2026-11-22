"""The AI assistant: Claude through the Messages API with tool use, the loop on this PC. The key is read from the
ANTHROPIC_API_KEY environment variable only (the SDK reads it); it is never written anywhere.

Model claude-opus-5-5 by default (claude-sonnet-5-5 for speed), effort high, adaptive thinking (always on for Opus
5.5), server-side fallback on refusal. Manual loop rather than the beta tool runner, so tests can swap in a stand-in
client (W19_ASSISTANT_STUB=1) and no test spends tokens. The assistant never edits the base model or an existing
scenario: a what-if is a new scenario."""
import json, os
from types import SimpleNamespace
from sewerapp.assistant import tools as T

MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
SYSTEM = """You are the design assistant inside a sewer design application for the Ibri sanitary network (Oman, Nama Water Services guidelines PAM-GUD-201/202/203). The engineer is a hydraulic design engineer: answer concisely, bullets and tables, technical register, no fundamentals explained.

Rules:
- Every number you give comes from a tool result in this conversation. Never estimate a flow, velocity, depth or gradient yourself.
- Cite the guideline page for every rule you apply (e.g. PAM-GUD-203 p26 for 0.75 m/s self-cleansing). Use lookup_criterion when unsure of a value or page; never quote a value from memory.
- The 12 W18 cases (SC1-SC4 x 2051/2056/2061) are read only. To test a fix, call make_whatif, which creates a NEW scenario; say which scenario you created.
- Analysis after an edit holds the inverts and the laid gradient: pipes flagged needs_relay need the design chain before their depths can be trusted. Say so when it matters.
- Pipe labels look like P1-P151 (pipe), manholes P1-M151; P# is a pump system, P#L# a lift system.

The design basis of these designs (W18, the engineer's and client's decisions of November 2026; these govern over any older register line lookup_criterion returns):
- Flows: unit loads peaked by the model's Peltier/Merrimack table, 720 L/day per km infiltration (G201 p71-72); design years 2051/2056/2061, 2056 adopted.
- Gradients: the Table 11 minimum of each size (G203 p29), then pipes ABOVE DN200 are STEEPENED, one gradient per street run, up to a 0.75 % limit, to reach 0.75 m/s at the 2031 peak. Steepening is the adopted design, not a forbidden option. DN200 pipes are not steepened.
- Self-cleansing test: pipes above DN200 at 0.75 m/s at the 2031 peak, rechecked at 2036; the rest go on a flushing list (G203 4.2.6).
- Tractive force is NOT used to set gradients (dropped by the engineer for this basis; record it as a departure from G203 4.2.2.1). Do not propose it as the first fix, and never use Q_2030 x 0.61 or tau = 1 Pa: those are superseded.
- Depth: 12 m to an outfall as a hard limit, up to 14.65 m for a station or outfall where that saves a station, 16.5 m for any manhole (engineer's caps); cover 1.3 m (G203 p33).
- The km above DN200 under 0.75 m/s is judged with velocity at two decimals (as the SewerGEMS comparison); the report's 9.29 km for SC1-2056 uses the unrounded laid gradients."""


def _key():
    """The key from this process's environment, else from the Windows USER environment (a user variable set after the
    app or its shell was started never reaches the process). Read only; never written or logged."""
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k or os.name != "nt": return k
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            return winreg.QueryValueEx(h, "ANTHROPIC_API_KEY")[0] or None
    except OSError:
        return None


def available():
    if os.environ.get("W19_ASSISTANT_STUB") == "1": return dict(available=True, model="stub", reason="stand-in client (tests)")
    if not _key():
        return dict(available=False, model=MODELS["opus"],
                    reason="ANTHROPIC_API_KEY is not set. Set it as a user environment variable and restart the app.")
    return dict(available=True, model=MODELS["opus"], reason="")


def _client():
    if os.environ.get("W19_ASSISTANT_STUB") == "1": return StubClient()
    import anthropic
    return anthropic.Anthropic(api_key=_key())


SYSTEM_GENERAL = """You are the design assistant inside a general sewer and stormwater modelling application (a clean-room tool that works like SewerGEMS, with EPA SWMM 5 for stormwater). The engineer is a hydraulic design engineer: answer concisely, bullets and tables, technical register, no fundamentals explained.

Rules:
- Every number you give comes from a tool result in this conversation; never estimate a flow, velocity, depth or gradient yourself.
- The project's own settings (friction, peaking, design limits, units) govern; quote them from project_summary. Cite the guideline page for a rule you apply (PAM-GUD-203 / -201 pages through lookup_criterion); never quote a value from memory.
- Never change an existing scenario: make_scenario, design_scenario and storm testing work in NEW scenarios; say which one you created.
- Units: a project imported from SWMM may be in US units (ft, cfs, acres); say the units with every number.
- For the Ibri sample projects the W18 basis applies: steepening above DN200 to 0.75 m/s at the 2031 peak up to 0.75 % is the adopted design; tractive force is not used for gradients."""


def ask(project, sid, message, history=None, model="opus", max_turns=12, toolset=None, system=None, context=None):
    """One user message, answered with as many tool calls as the model needs. Returns reply, tool_calls, usage."""
    toolset = toolset or T; client = _client(); tools = toolset.definitions()
    ctx = context or f"active scenario: {sid}"
    messages = [*(history or []), {"role": "user", "content": f"[{ctx}]\n{message}"}]
    calls, usage = [], dict(input_tokens=0, output_tokens=0, cache_write_tokens=0, cache_read_tokens=0)
    for _ in range(max_turns):
        r = client.beta.messages.create(
            model=MODELS.get(model, model), max_tokens=16000, system=system or SYSTEM, tools=tools, messages=messages,
            output_config={"effort": "high"}, cache_control={"type": "ephemeral"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        usage["input_tokens"] += r.usage.input_tokens; usage["output_tokens"] += r.usage.output_tokens
        usage["cache_write_tokens"] += getattr(r.usage, "cache_creation_input_tokens", 0) or 0   # cached prompt parts are
        usage["cache_read_tokens"] += getattr(r.usage, "cache_read_input_tokens", 0) or 0       # billed outside input_tokens
        if r.stop_reason == "refusal":
            return dict(reply="The request was declined by the model's safety checks.", tool_calls=calls, usage=usage)
        messages.append({"role": "assistant", "content": r.content})
        if r.stop_reason == "pause_turn": continue
        uses = [b for b in r.content if b.type == "tool_use"]
        if r.stop_reason != "tool_use" or not uses:
            text = "\n".join(b.text for b in r.content if b.type == "text")
            if r.stop_reason == "max_tokens": text += "\n\n(answer cut at the output limit)"
            return dict(reply=text, tool_calls=calls, usage=usage)
        results = []
        for b in uses:
            try:
                out = toolset.call(project, b.name, b.input); ok = True
            except Exception as e:                       # the model sees the error and can correct itself
                out = dict(error=f"{type(e).__name__}: {e}"); ok = False
            calls.append(dict(name=b.name, input=b.input, ok=ok))
            results.append(dict(type="tool_result", tool_use_id=b.id, content=json.dumps(out, default=str)[:60000],
                                is_error=not ok))
        messages.append({"role": "user", "content": results})
    return dict(reply="Stopped after the maximum number of tool rounds.", tool_calls=calls, usage=usage)


class StubClient:
    """Deterministic stand-in for tests: first asks for the scenario summary, then answers from it."""

    def __init__(self):
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        last = kw["messages"][-1]["content"]
        u = SimpleNamespace(input_tokens=10, output_tokens=5)
        names = {t["name"] for t in kw["tools"]}
        if isinstance(last, str):
            ctx = last.split("]")[0].lstrip("[")
            if "project_summary" in names:      # general app: "[active project: p1, scenario: base]"
                kv = dict(x.strip().split(": ") for x in ctx.replace("active ", "").split(","))
                block = SimpleNamespace(type="tool_use", id="t1", name="project_summary", input={"project": kv["project"], "scenario": kv["scenario"]})
            else:
                block = SimpleNamespace(type="tool_use", id="t1", name="get_summary", input={"scenario": ctx.split(": ")[1]})
            return SimpleNamespace(stop_reason="tool_use", content=[block], usage=u)
        s = json.loads(last[0]["content"]); s = s.get("summary", s)
        text = (f"Stub answer: {s.get('pipes')} pipes, {s.get('km_under075_2031')} km above DN200 under 0.75 m/s at "
                f"2031 (PAM-GUD-203 p26), {s.get('over_limit')} over the d/D limit.")
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)], usage=u)
