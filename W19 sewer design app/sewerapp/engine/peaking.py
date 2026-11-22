"""Peaking of sanitary flow. The model's Extreme Flow Setup table is applied to each pipe's cumulative upstream unit
load in L/s, linear between rows (SewerGEMS's way, read off and proved on Ibri SC1-2056)."""
import numpy as np

# Ibri's 'Peltier100-Merriamck' (the model's spelling): Peltier to 1 L/s, Merrimack above, step row 1.001 -> 3.56
IBRI_PELTIER100_MERRIMACK = (
    (0.1, 4.66), (0.15, 4.08), (0.2, 3.74), (0.3, 3.33), (0.5, 2.91), (0.75, 2.65), (1, 2.5), (1.001, 3.56),
    (1.5, 3.39), (2, 3.28), (3, 3.12), (5, 2.93), (7.5, 2.79), (10, 2.7), (15, 2.57), (20, 2.48), (30, 2.36),
    (50, 2.22), (75, 2.11), (100, 2.04), (150, 1.94), (200, 1.88), (300, 1.79), (500, 1.68), (750, 1.6), (1000, 1.54))


class PeakingTable:
    def __init__(self, rows):
        rows = sorted(rows)
        self.q = np.array([r[0] for r in rows], float)
        self.f = np.array([r[1] for r in rows], float)

    def factor(self, q_ls):
        r = np.interp(q_ls, self.q, self.f)
        return float(r) if np.ndim(r) == 0 else r


def peltier(q_ls):
    """PAM-GUD-201 p72: PF = 1.5 + 1 / sqrt(Qm), Qm the average flow in L/s."""
    return 1.5 + 1.0 / np.sqrt(q_ls)


def merrimack(q_ls):
    """PAM-GUD-201 p71 7.4.2: Qpdf = 2.65 Qadf^0.879, flows in Ml/d; returned as the factor Qpdf / Qadf."""
    qadf = np.asarray(q_ls, float) * 86.4 / 1000.0
    return 2.65 * qadf ** -0.121
