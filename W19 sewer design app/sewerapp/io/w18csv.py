"""Readers of the bridge's SewerGEMS export format (as W18 used it)."""
import pandas as pd


def start_sizes(path, labels):
    """The modeller's sizes (R4 flow-check export), nominal mm, in the order of `labels`."""
    s = pd.read_csv(path).set_index("label").size_label
    return s.reindex(labels).str.extract(r"(\d+)")[0].astype(int).values
