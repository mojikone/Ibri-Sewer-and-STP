"""Manhole spacing along a straight run: the engineer's rule of 2026-08-18, ported unchanged from W13
(`W13/py/sewnet/stages/chambers.py` ChamberPlacer.split_lengths, tests `W13/py/tests/test_geometry.py`).

Fewest reaches that keep every one within the maximum, then ROUND lengths rather than an exact equal division, never a
short stub: 330 m at a 100 m maximum is 80/80/80/90, not 4 x 82.5 and not 100/100/100/30; 230 m is 80/80/70.
The default maximum is PAM-GUD-203 Table 12 (p30) for the pipe's size."""
import math

ROUND_STEP, ROUND_FALLBACK = 10.0, 5.0             # W13 criteria MH_ROUND_STEP / MH_ROUND_FALLBACK (user rule 2026-08-18)
# G203 p30 Table 12, maximum manhole spacing by nominal size: up to DN315 100 m, 350-900 120 m, 1000-1400 150 m, over 200 m
TABLE12 = [(315, 100.0), (900, 120.0), (1400, 150.0), (10 ** 9, 200.0)]


def table12(dn_mm):
    dn = float(dn_mm or 0)
    return next(m for upto, m in TABLE12 if dn <= upto)


def split_lengths(L, max_len, round_spacing=True):
    """Reach lengths covering L: fewest pieces, rounded, remainder on one piece."""
    n = max(1, int(math.ceil(L / max_len - 1e-9)))
    if n == 1:
        return [L]
    if not round_spacing:
        return [L / n] * n
    for step in (ROUND_STEP, ROUND_FALLBACK):
        base = math.floor((L / n) / step) * step
        if base <= 0:
            continue
        rem = L - base * n
        k = int(round(rem / step))
        if base + step > max_len + 1e-9:
            k = 0
        lens = [base + step if i < k else base for i in range(n)]
        odd = L - sum(lens)
        if abs(odd) > 1e-9:
            # the odd metres go on the reach with the most headroom, never on the last one blindly
            lens[lens.index(min(lens))] += odd
        if all(x > 0 for x in lens) and max(lens) <= max_len + 1e-6:
            return lens
    return [L / n] * n
