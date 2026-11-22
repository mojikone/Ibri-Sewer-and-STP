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
- Pipe labels look like P1-P151 (pipe), manholes P1-M151; P# is a pump system, P#L# a lift system."""


def available():
    if os.environ.get("W19_ASSISTANT_STUB") == "1": return dict(available=True, model="stub", reason="stand-in client (tests)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return dict(available=False, model=MODELS["opus"],
                    reason="ANTHROPIC_API_KEY is not set. Set it as a user environment variable and restart the app.")
    return dict(available=True, model=MODELS["opus"], reason="")


def _client():
    if os.environ.get("W19_ASSISTANT_STUB") == "1": return StubClient()
    import anthropic
    return anthropic.Anthropic()


def ask(project, sid, message, history=None, model="opus", max_turns=12):
    """One user message, answered with as many tool calls as the model needs. Returns reply, tool_calls, usage."""
    client = _client(); tools = T.definitions()
    messages = [*(history or []), {"role": "user", "content": f"[active scenario: {sid}]\n{message}"}]
    calls, usage = [], dict(input_tokens=0, output_tokens=0)
    for _ in range(max_turns):
        r = client.beta.messages.create(
            model=MODELS.get(model, model), max_tokens=16000, system=SYSTEM, tools=tools, messages=messages,
            output_config={"effort": "high"}, cache_control={"type": "ephemeral"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        usage["input_tokens"] += r.usage.input_tokens; usage["output_tokens"] += r.usage.output_tokens
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
                out = T.call(project, b.name, b.input); ok = True
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
        if isinstance(last, str):
            sid = last.split("]")[0].split(": ")[1]
            block = SimpleNamespace(type="tool_use", id="t1", name="get_summary", input={"scenario": sid})
            return SimpleNamespace(stop_reason="tool_use", content=[block], usage=u)
        s = json.loads(last[0]["content"])
        text = (f"Stub answer: {s.get('pipes')} pipes, {s.get('km_under075_2031')} km above DN200 under 0.75 m/s at "
                f"2031 (PAM-GUD-203 p26), {s.get('over_limit')} over the d/D limit.")
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)], usage=u)
