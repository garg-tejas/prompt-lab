import math
from typing import List


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function."""
    max_iter = 200
    eps = 3e-14
    fpmin = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log(1.0 - x) - ln_beta)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def student_t_two_tailed_p(t_stat: float, df: int) -> float:
    if df <= 0:
        return 1.0
    x = df / (df + t_stat * t_stat)
    p = regularized_incomplete_beta(df / 2.0, 0.5, x)
    return max(0.0, min(1.0, p))


def t_critical_95(df: int) -> float:
    """Two-sided 95% critical value via bisection on the t survival function."""
    if df <= 0:
        return 1.96
    lo, hi = 0.0, 30.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if student_t_two_tailed_p(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def paired_stats(diffs: List[float]) -> dict:
    """Paired t-test. Significance is a two-sided p-value under 0.05."""
    n = len(diffs)
    if n < 2:
        return {
            "mean_diff": 0.0,
            "std_dev": 0.0,
            "std_error": 0.0,
            "n": n,
            "t_stat": 0.0,
            "p_value": None,
            "significant": False,
            "winner": "tie",
            "ci_95": [0.0, 0.0],
        }

    mean_diff = sum(diffs) / n
    variance = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
    std_dev = variance ** 0.5
    std_error = std_dev / (n ** 0.5)
    df = n - 1

    if std_error == 0:
        significant = mean_diff != 0
        p_value = 0.0 if significant else 1.0
        t_stat = math.inf if significant else 0.0
    else:
        t_stat = mean_diff / std_error
        p_value = student_t_two_tailed_p(t_stat, df)
        significant = p_value < 0.05

    if significant:
        winner = "a" if mean_diff > 0 else "b"
    else:
        winner = "tie"

    crit = t_critical_95(df)
    ci_lower = mean_diff - crit * std_error
    ci_upper = mean_diff + crit * std_error
    t_out = None if t_stat == math.inf else round(t_stat, 4)

    return {
        "mean_diff": round(mean_diff, 4),
        "std_dev": round(std_dev, 4),
        "std_error": round(std_error, 4),
        "n": n,
        "t_stat": t_out,
        "p_value": round(p_value, 6),
        "significant": significant,
        "winner": winner,
        "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
    }
