import json, pytest
from sewerapp import fixtures
from sewerapp.engine import design_year

GOLD = json.load(open(fixtures.path("golden/design_year_check_2056.json")))


@pytest.mark.gate_p1a
@pytest.mark.parametrize("case", sorted(GOLD))
def test_equals_w18(case):
    assert design_year.check(case, case.split("-")[0] + "-2056") == GOLD[case]
