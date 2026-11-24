"""v7 (2026-11-24), the engineer: "I reconnected a pipe to a manhole and reran the model. It did not design to lower the
manholes' invert levels, and simply sent the flow to the next manhole." A pipe that arrives below the pipe leaving its
structure is an error in Validate; a design of the selected pipes drops the pipes below them as far as needed."""
from sewerapp.engine import validate
from sewerapp.model.general import Project
from sewerapp.model import workspace as W


def _net():
    """A main line N0-N1-N2-O, and a deep branch N4 whose pipe is reconnected from N5 to N1, arriving 6 m below it."""
    p = Project("r", crs=32640)
    for i, (x, y, g, inv) in enumerate([(0, 0, 360, 357), (100, 0, 359, 356.5), (200, 0, 358, 356), (300, 0, 357, 355), (0, 100, 356, 351), (100, 100, 355, 350.5)]):
        W.apply(p, dict(op="add_node", id=f"N{i}", x=x, y=y, ground=g, invert=inv, kind="outfall" if i == 3 else "manhole"))
    for a, b in (("N0", "N1"), ("N1", "N2"), ("N2", "N3"), ("N4", "N5")): W.apply(p, dict(op="add_link", from_node=a, to_node=b, dn_mm=200))
    p.load_sets["design"] = {"N0": 50.0, "N4": 50.0}
    W.apply(p, dict(op="reconnect", id="P-4", end="to", node="N1", invert=350.5))     # as dragged: the pipe keeps its low end
    return p


def test_validate_flags_a_pipe_arriving_below_the_one_leaving():
    p = _net()
    m = [x for x in validate.run(p) if x["id"] == "P-4" and "cannot leave" in x["message"]]
    assert len(m) == 1 and m[0]["level"] == "error" and "6.00 m below" in m[0]["message"]


def test_design_of_the_reconnected_pipe_drops_the_pipes_below():
    p = _net()
    W.apply(p, dict(op="design", only=["P-4"]))
    L = p.links
    assert L.up_inv["P-2"] <= L.dn_inv["P-4"] + 1e-9                     # the pipe leaving N1 now starts at or below the arrival
    assert abs((L.up_inv["P-2"] - L.dn_inv["P-2"]) - 0.5) < 1e-9          # it kept its fall (0.5 m over 100 m)
    assert L.up_inv["P-3"] <= L.dn_inv["P-2"] + 1e-9 and p.nodes.invert["N1"] <= L.dn_inv["P-4"] + 1e-9
    assert L.dn_mm["P-2"] == 200                                          # kept its size: it was not selected
    assert not [x for x in validate.run(p) if "cannot leave" in x["message"]]


def test_a_locked_pipe_below_keeps_its_levels():
    p = _net(); W.apply(p, dict(op="lock", ids=["P-2"], locked=True))
    before = p.links.up_inv["P-2"]
    W.apply(p, dict(op="design", only=["P-4"]))
    assert p.links.up_inv["P-2"] == before
    assert [x for x in validate.run(p) if x["id"] == "P-4" and "cannot leave" in x["message"]]


def test_the_ibri_design_raises_no_false_drop():
    """W18's final design keeps levels to the centimetre: its 19,060 joins differ by 1.03 cm at most, none flagged."""
    from sewerapp.io import ibri_sample
    p = ibri_sample.build("SC1-2056")
    assert not [x for x in validate.run(p) if "cannot leave" in x["message"]]
