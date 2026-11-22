"""Gravity pipe hydraulics for circular pipes, vectorised. Colebrook-White with ks 1.5 mm for all sizes and nu
1.141e-6 m2/s at 15 degC (PAM-GUD-203 p24, p25, p28). Same arithmetic as W18's scalar functions."""
import numpy as np

G, NU, KS = 9.81, 1.141e-6, 1.5e-3


def section(D, y):
    """Flow area and hydraulic radius of a circular pipe of inside diameter D at depth y."""
    D = np.asarray(D, float); y = np.asarray(y, float)
    th = 2 * np.arccos(1 - 2 * y / D)
    A = D * D / 8 * (th - np.sin(th))
    return A, A / (D * th / 2)


def v_colebrook(R, S, ks=KS, nu=NU):
    a = np.sqrt(8 * G * R * S)
    return -2 * a * np.log10(ks / (14.8 * R) + 2.51 * nu / (4 * R * a))


def q_capacity(D, S, ratio, ks=KS, nu=NU):
    """Flow at depth ratio x D, at gradient S."""
    D = np.asarray(D, float)
    A, R = section(D, np.asarray(ratio, float) * D)
    return A * v_colebrook(R, S, ks, nu)


def normal_depth(Q, D, S, ks=KS, nu=NU, iters=50):
    """Depth ratio y/D and velocity at normal depth, by bisection as W18 (50 halvings between 1e-6 D and 0.999 D)."""
    Q, D, S = np.broadcast_arrays(np.asarray(Q, float), np.asarray(D, float), np.asarray(S, float))
    lo, hi = 1e-6 * D, 0.999 * D
    with np.errstate(invalid="ignore", divide="ignore"):
        for _ in range(iters):
            y = (lo + hi) / 2
            A, R = section(D, y)
            over = A * v_colebrook(R, S, ks, nu) > Q
            hi = np.where(over, y, hi); lo = np.where(over, lo, y)
        y = (lo + hi) / 2
        A, _ = section(D, y)
    pos = (Q > 0) & (S > 0)
    return np.where(pos, y / D, 0.0), np.where(pos, Q / np.where(pos, A, 1.0), 0.0)
