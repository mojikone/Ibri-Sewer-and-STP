"""Long sections along any route: down to the outfall (no end), between two manholes or pipes in either direction,
through via points; links walked against the flow are reversed (levels read at the route's ends), chainage runs on."""
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app

C = TestClient(app)


def ed(pid, **e):
    r = C.post(f"/api/g/projects/{pid}/scenarios/base/edit", json=e); assert r.status_code == 200, r.text


@pytest.fixture(scope="module")
def net():
    """MH1 -> MH2 -> MH3 -> OUT (P-1, P-2, P-3) with a lateral MH4 -> MH2 (P-4) and a lone manhole MH9."""
    pid = C.post("/api/g/projects/new", json=dict(name="Routes")).json()["id"]
    for i, (x, y, g) in enumerate([(0, 0, 100.0), (100, 0, 99.5), (200, 0, 99.0), (100, 80, 100.2)]):
        ed(pid, op="add_node", id=f"MH{i+1}", kind="manhole", x=x, y=y, ground=g, invert=g - 2.0)
    ed(pid, op="add_node", id="OUT", kind="outfall", x=300, y=0, ground=98.5, invert=96.5)
    ed(pid, op="add_node", id="MH9", kind="manhole", x=500, y=500, ground=97.0, invert=95.0)
    for a, b in (("MH1", "MH2"), ("MH2", "MH3"), ("MH3", "OUT"), ("MH4", "MH2")):
        ed(pid, op="add_link", from_node=a, to_node=b, dn_mm=200)
    ed(pid, op="set_load", set="design", node="MH1", value=86.4)
    return pid


def prof(pid, code=200, **q):
    r = C.get(f"/api/g/projects/{pid}/scenarios/base/profile", params=q); assert r.status_code == code, r.text; return r.json()


def walk(rows): return [(r["link"], r["reversed"]) for r in rows]


def test_no_end_runs_down_to_the_outfall(net):
    rows = prof(net, start="MH1")
    assert walk(rows) == [("P-1", False), ("P-2", False), ("P-3", False)]
    assert rows[-1]["to_node"] == "OUT" and rows[-1]["ch1"] == pytest.approx(300, abs=0.01)
    assert rows[0]["q_ls"] > 0 and rows[0]["slope_pc"] == pytest.approx(0.5, abs=1e-6)


def test_between_two_manholes_against_the_flow(net):
    rows = prof(net, start="MH4", end="MH1")                  # up the lateral's flow, then back up P-1
    assert walk(rows) == [("P-4", False), ("P-1", True)]
    p1 = rows[1]
    assert p1["from_node"] == "MH2" and p1["to_node"] == "MH1"
    assert p1["inv0"] == pytest.approx(97.5) and p1["inv1"] == pytest.approx(98.0)   # levels at the route's own ends
    assert p1["slope_pc"] == pytest.approx(0.5, abs=1e-6)      # the gradient stays in the flow direction
    assert rows[1]["ch0"] == pytest.approx(rows[0]["ch1"])


def test_pipes_as_route_ends_and_via_points(net):
    assert walk(prof(net, start="P-2", end="OUT")) == [("P-2", False), ("P-3", False)]
    assert walk(prof(net, start="MH3", end="P-1")) == [("P-2", True), ("P-1", True)]   # arrives at P-1 by the short side
    assert walk(prof(net, start="MH1", end="MH3", via="MH4")) == [("P-1", False), ("P-4", True), ("P-4", False), ("P-2", False)]
    assert walk(prof(net, start="P-4")) == [("P-4", False), ("P-2", False), ("P-3", False)]


def test_pipes_joining_each_manhole_are_listed(net):
    rows = prof(net, start="MH1")                             # the lateral P-4 joins at MH2; nothing else meets the route
    assert rows[0]["joins0"] == [] and rows[0]["node_inv0"] == pytest.approx(98.0)
    j = rows[0]["joins1"]
    assert [(x["link"], x["dir"], x["other"]) for x in j] == [("P-4", "in", "MH4")]
    assert j[0]["invert"] == pytest.approx(C.get(f"/api/g/projects/{net}/scenarios/base/model").json()["links"]["features"][3]["properties"]["dn_inv"])
    assert j[0]["inside_mm"] > 0 and rows[0]["kind1"] == "manhole" and rows[1]["joins1"] == [] and rows[2]["kind1"] == "outfall"
    side = prof(net, start="MH4", end="MH1")                  # walking up P-1, the main line itself joins MH2 from both sides
    assert sorted((x["link"], x["dir"]) for x in side[0]["joins1"]) == [("P-2", "out")]


def test_no_route_says_so(net):
    assert "no route" in prof(net, code=400, start="MH1", end="MH9")["detail"]
    assert "no node or pipe" in prof(net, code=400, start="XX")["detail"]
