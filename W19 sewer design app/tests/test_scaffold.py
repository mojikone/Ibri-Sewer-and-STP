import os
import sewerapp

W19 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_version():
    assert sewerapp.__version__ == "0.1.0"


def test_readme_states_the_clean_room_rule():
    text = open(os.path.join(W19, "README.md"), encoding="utf-8").read()
    assert "Clean-room" in text and "never decompiled" in text
