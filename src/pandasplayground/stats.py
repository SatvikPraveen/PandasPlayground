"""Inferential statistics helpers: interval estimates, resampling tests and effect sizes.

The emphasis is on reporting *uncertainty and magnitude* rather than bare p-values:
every test result carries an effect size, and interval estimates carry their method and level.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy import stats as sps

from pandasplayground.config import DEFAULT_SEED

ArrayLike = Sequence[float] | np.ndarray | pd.Series
Alternative = Literal["two-sided", "less", "greater"]


def _clean(x: ArrayLike) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    return arr[~np.isnan(arr)]


@dataclass(frozen=True)
class Estimate:
    """A point estimate with a confidence interval."""

    point: float
    low: float
    high: float
    level: float
    method: str

    def __str__(self) -> str:
        return f"{self.point:.4g} [{self.level:.0%} CI {self.low:.4g}, {self.high:.4g}; {self.method}]"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TestResult:
    """Outcome of a hypothesis test, always paired with an effect size."""

    test: str
    statistic: float
    p_value: float
    effect_size: float
    effect_size_name: str
    extra: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Interval estimation
# ---------------------------------------------------------------------------


def bootstrap_ci(
    data: ArrayLike,
    statistic: Callable[[np.ndarray], float] = np.mean,
    n_resamples: int = 9_999,
    level: float = 0.95,
    method: Literal["percentile", "basic", "BCa"] = "BCa",
    seed: int | None = DEFAULT_SEED,
) -> Estimate:
    """Non-parametric bootstrap confidence interval for a one-sample statistic.

    Defaults to the bias-corrected and accelerated (BCa) interval (Efron, 1987), which has
    better coverage than the percentile interval for skewed statistics.
    """
    x = _clean(data)
    if x.size < 2:
        raise ValueError("bootstrap_ci needs at least two non-missing observations")
    res = sps.bootstrap(
        (x,),
        lambda s, axis: np.apply_along_axis(statistic, axis, s),
        n_resamples=n_resamples,
        confidence_level=level,
        method=method,
        random_state=np.random.default_rng(seed),
    )
    return Estimate(
        float(statistic(x)),
        float(res.confidence_interval.low),
        float(res.confidence_interval.high),
        level,
        f"bootstrap-{method}",
    )


def mean_ci(data: ArrayLike, level: float = 0.95) -> Estimate:
    """Student-t confidence interval for the mean."""
    x = _clean(data)
    if x.size < 2:
        raise ValueError("mean_ci needs at least two non-missing observations")
    m, se = x.mean(), sps.sem(x)
    low, high = sps.t.interval(level, df=x.size - 1, loc=m, scale=se)
    return Estimate(float(m), float(low), float(high), level, "student-t")


def proportion_ci(successes: int, n: int, level: float = 0.95) -> Estimate:
    """Wilson score interval for a binomial proportion (well-behaved near 0 and 1, unlike Wald)."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= successes <= n:
        raise ValueError("successes must be in [0, n]")
    z = sps.norm.ppf(0.5 + level / 2)
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return Estimate(p, float(max(0.0, centre - half)), float(min(1.0, centre + half)), level, "wilson")


def correlation_ci(
    x: ArrayLike, y: ArrayLike, method: Literal["pearson", "spearman"] = "pearson", level: float = 0.95
) -> Estimate:
    """Correlation coefficient with a Fisher z-transform confidence interval (pairwise-complete)."""
    a, b = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mask = ~(np.isnan(a) | np.isnan(b))
    a, b = a[mask], b[mask]
    n = a.size
    if n < 4:
        raise ValueError("correlation_ci needs at least four complete pairs")
    r = float(sps.pearsonr(a, b)[0] if method == "pearson" else sps.spearmanr(a, b)[0])
    z, se = np.arctanh(np.clip(r, -0.999999, 0.999999)), 1 / np.sqrt(n - 3)
    crit = sps.norm.ppf(0.5 + level / 2)
    return Estimate(r, float(np.tanh(z - crit * se)), float(np.tanh(z + crit * se)), level, f"{method}-fisher-z")


# ---------------------------------------------------------------------------
# Effect sizes
# ---------------------------------------------------------------------------


def cohens_d(a: ArrayLike, b: ArrayLike, hedges_correction: bool = True) -> float:
    """Standardised mean difference ``(mean(a) - mean(b)) / pooled_sd``.

    With ``hedges_correction`` the small-sample bias correction (Hedges' g) is applied.
    """
    x, y = _clean(a), _clean(b)
    nx, ny = x.size, y.size
    if nx < 2 or ny < 2:
        raise ValueError("each group needs at least two observations")
    pooled = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / (nx + ny - 2))
    if pooled == 0:
        return 0.0 if x.mean() == y.mean() else float(np.sign(x.mean() - y.mean()) * np.inf)
    d = (x.mean() - y.mean()) / pooled
    if hedges_correction:
        d *= 1 - 3 / (4 * (nx + ny) - 9)
    return float(d)


def cramers_v(table: pd.DataFrame | np.ndarray, bias_correction: bool = True) -> float:
    """Cramér's V for a contingency table, with Bergsma (2013) bias correction by default."""
    obs = np.asarray(table, dtype=float)
    n = obs.sum()
    if n == 0 or min(obs.shape) < 2:
        return float("nan")
    chi2 = sps.chi2_contingency(obs, correction=False)[0]
    phi2 = chi2 / n
    r, k = obs.shape
    if bias_correction:
        phi2 = max(0.0, phi2 - (k - 1) * (r - 1) / (n - 1))
        r = r - (r - 1) ** 2 / (n - 1)
        k = k - (k - 1) ** 2 / (n - 1)
    denom = min(k - 1, r - 1)
    return float(np.sqrt(phi2 / denom)) if denom > 0 else float("nan")


# ---------------------------------------------------------------------------
# Hypothesis tests
# ---------------------------------------------------------------------------


def permutation_test_means(
    a: ArrayLike,
    b: ArrayLike,
    n_resamples: int = 9_999,
    alternative: Alternative = "two-sided",
    seed: int | None = DEFAULT_SEED,
) -> TestResult:
    """Two-sample permutation test on the difference in means (no normality assumption)."""
    x, y = _clean(a), _clean(b)
    res = sps.permutation_test(
        (x, y),
        lambda u, v, axis: np.mean(u, axis=axis) - np.mean(v, axis=axis),
        permutation_type="independent",
        vectorized=True,
        n_resamples=n_resamples,
        alternative=alternative,
        random_state=np.random.default_rng(seed),
    )
    return TestResult(
        "permutation (difference in means)",
        float(res.statistic),
        float(res.pvalue),
        cohens_d(x, y),
        "hedges_g",
        {"n_a": int(x.size), "n_b": int(y.size), "n_resamples": n_resamples},
    )


def welch_t_test(a: ArrayLike, b: ArrayLike, alternative: Alternative = "two-sided") -> TestResult:
    """Welch's unequal-variance t-test with Hedges' g effect size."""
    x, y = _clean(a), _clean(b)
    res = sps.ttest_ind(x, y, equal_var=False, alternative=alternative)
    return TestResult(
        "welch t-test",
        float(res.statistic),
        float(res.pvalue),
        cohens_d(x, y),
        "hedges_g",
        {"df": float(res.df), "n_a": int(x.size), "n_b": int(y.size)},
    )


def chi2_independence(df: pd.DataFrame, col_a: str, col_b: str) -> TestResult:
    """Pearson chi-square test of independence between two categorical columns, with Cramér's V."""
    table = pd.crosstab(df[col_a], df[col_b])
    chi2, p, dof, expected = sps.chi2_contingency(table.to_numpy(), correction=False)
    return TestResult(
        f"chi-square independence ({col_a} x {col_b})",
        float(chi2),
        float(p),
        cramers_v(table),
        "cramers_v",
        {"dof": int(dof), "n": int(table.to_numpy().sum()), "min_expected": float(expected.min())},
    )


def kruskal_by_group(df: pd.DataFrame, value_col: str, group_col: str) -> TestResult:
    """Kruskal-Wallis H-test across groups, with epsilon-squared effect size (Tomczak & Tomczak, 2014)."""
    groups = [g[value_col].dropna().to_numpy(dtype=float) for _, g in df.groupby(group_col, observed=True)]
    h, p = sps.kruskal(*groups)
    n = sum(len(g) for g in groups)
    eps2 = float(h * (n + 1) / (n**2 - 1)) if n > 1 else float("nan")
    return TestResult(
        f"kruskal-wallis ({value_col} by {group_col})",
        float(h),
        float(p),
        eps2,
        "epsilon_squared",
        {"k": len(groups), "n": n},
    )


def adjust_pvalues(pvalues: ArrayLike, method: Literal["bh", "by", "bonferroni", "holm"] = "bh") -> np.ndarray:
    """Multiple-comparison correction.

    ``bh`` = Benjamini-Hochberg false discovery rate (FDR), ``by`` = Benjamini-Yekutieli,
    ``bonferroni`` and ``holm`` control the family-wise error rate.
    """
    p = np.asarray(pvalues, dtype=float)
    if method in ("bh", "by"):
        return np.asarray(sps.false_discovery_control(p, method=method))
    m = p.size
    if method == "bonferroni":
        return np.minimum(p * m, 1.0)
    if method == "holm":
        order = np.argsort(p)
        adjusted = np.empty(m)
        running = 0.0
        for rank, idx in enumerate(order):
            running = max(running, (m - rank) * p[idx])
            adjusted[idx] = min(running, 1.0)
        return adjusted
    raise ValueError(f"Unknown method {method!r}")


# ---------------------------------------------------------------------------
# Time series
# ---------------------------------------------------------------------------


def differenced_correlation(
    x: ArrayLike, y: ArrayLike, lag: int = 1, method: Literal["pearson", "spearman"] = "pearson", level: float = 0.95
) -> Estimate:
    """Correlation of ``lag``-differenced series.

    Two trending series correlate strongly even when unrelated (spurious regression; Granger & Newbold, 1974).
    Correlating first differences removes shared deterministic trends and is a basic sanity check before
    interpreting a correlation between time series.
    """
    dx = pd.Series(np.asarray(x, dtype=float)).diff(lag)
    dy = pd.Series(np.asarray(y, dtype=float)).diff(lag)
    return correlation_ci(dx, dy, method=method, level=level)
