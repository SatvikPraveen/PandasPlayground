from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps

from pandasplayground import stats


def test_mean_ci_matches_textbook():
    x = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    est = stats.mean_ci(x)
    half = sps.t.ppf(0.975, 7) * np.std(x, ddof=1) / np.sqrt(8)
    assert est.point == 5.0
    assert est.low == pytest.approx(5 - half)
    assert est.high == pytest.approx(5 + half)


def test_wilson_interval_reference_values():
    # Reference: Newcombe (1998), Table I, 81/263 -> 0.2553 to 0.3662
    est = stats.proportion_ci(81, 263)
    assert est.low == pytest.approx(0.2553, abs=1e-4)
    assert est.high == pytest.approx(0.3662, abs=1e-4)
    edge = stats.proportion_ci(0, 10)
    assert edge.low == 0.0 and 0 < edge.high < 0.35


@pytest.mark.parametrize(("successes", "n"), [(-1, 10), (11, 10)])
def test_proportion_ci_rejects_invalid(successes, n):
    with pytest.raises(ValueError):
        stats.proportion_ci(successes, n)


def test_bootstrap_ci_is_seeded_and_contains_point(rng):
    x = rng.exponential(2.0, 200)
    a = stats.bootstrap_ci(x, n_resamples=2000, seed=1)
    b = stats.bootstrap_ci(x, n_resamples=2000, seed=1)
    assert a == b
    assert a.low < a.point < a.high
    assert "BCa" in a.method


@pytest.mark.slow
def test_bootstrap_ci_coverage_is_near_nominal():
    """Empirical coverage of the 90% percentile interval for a normal mean should be close to 90%."""
    gen = np.random.default_rng(7)
    hits = 0
    trials = 200
    for i in range(trials):
        sample = gen.normal(10, 3, 50)
        est = stats.bootstrap_ci(sample, n_resamples=999, level=0.9, method="percentile", seed=i)
        hits += est.low <= 10 <= est.high
    assert 0.82 <= hits / trials <= 0.96


def test_correlation_ci_and_spurious_trend(rng):
    t = np.arange(200, dtype=float)
    a = t + rng.normal(0, 5, 200)
    b = t + rng.normal(0, 5, 200)  # independent noise around a shared trend
    raw = stats.correlation_ci(a, b)
    diffed = stats.differenced_correlation(a, b)
    assert raw.point > 0.95
    assert diffed.low < 0 < diffed.high
    assert stats.correlation_ci(a, b, method="spearman").point > 0.9


def test_hedges_g_known_value():
    a, b = [1.0, 2.0, 3.0, 4.0, 5.0], [3.0, 4.0, 5.0, 6.0, 7.0]
    d = -2 / np.sqrt(2.5)
    assert stats.cohens_d(a, b, hedges_correction=False) == pytest.approx(d)
    assert stats.cohens_d(a, b) == pytest.approx(d * (1 - 3 / (4 * 10 - 9)))
    assert stats.cohens_d([1, 1], [1, 1]) == 0.0


def test_cramers_v_bounds():
    perfect = np.array([[50, 0], [0, 50]])
    none = np.array([[25, 25], [25, 25]])
    assert stats.cramers_v(perfect, bias_correction=False) == pytest.approx(1.0)
    assert stats.cramers_v(none) == pytest.approx(0.0)


def test_permutation_and_welch_agree_on_clear_effect(rng):
    a, b = rng.normal(0, 1, 80), rng.normal(1, 1, 80)
    perm = stats.permutation_test_means(a, b, n_resamples=2000)
    welch = stats.welch_t_test(a, b)
    assert perm.p_value < 0.01 and welch.p_value < 0.01
    assert perm.effect_size == pytest.approx(welch.effect_size)
    assert perm.effect_size < -0.5


def test_chi2_and_kruskal():
    df = pd.DataFrame({"g": ["a"] * 50 + ["b"] * 50, "y": ["yes"] * 45 + ["no"] * 5 + ["yes"] * 5 + ["no"] * 45})
    res = stats.chi2_independence(df, "g", "y")
    assert res.p_value < 1e-10 and res.effect_size > 0.7
    num = pd.DataFrame({"g": ["a"] * 30 + ["b"] * 30, "v": list(range(30)) + list(range(100, 130))})
    kw = stats.kruskal_by_group(num, "v", "g")
    assert kw.p_value < 1e-6 and kw.extra == {"k": 2, "n": 60}


def test_adjust_pvalues():
    p = np.array([0.01, 0.04, 0.03, 0.5])
    np.testing.assert_allclose(stats.adjust_pvalues(p, "bonferroni"), [0.04, 0.16, 0.12, 1.0])
    np.testing.assert_allclose(stats.adjust_pvalues(p, "holm"), [0.04, 0.09, 0.09, 0.5])
    np.testing.assert_allclose(stats.adjust_pvalues(p, "bh"), [0.04, 0.0533333, 0.0533333, 0.5], rtol=1e-5)
    with pytest.raises(ValueError):
        stats.adjust_pvalues(p, "nope")  # type: ignore[arg-type]
