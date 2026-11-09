"""Tests for the Curve Number runoff functions. Only numpy is needed."""

import numpy as np
import pytest

from floodrisk.runoff import (
    CN_TABLE,
    DEFAULT_CN,
    cn_from_landcover,
    cumulative_runoff_mm,
    hourly_runoff_mm,
    retention_s,
)


def test_retention_known_value():
    # CN 80 -> S = 25400/80 - 254 = 63.5 mm
    assert retention_s(80) == pytest.approx(63.5)


def test_runoff_hand_calculation():
    # CN 80, P = 100 mm: S = 63.5, Ia = 12.7, Q = 87.3^2 / (87.3 + 63.5) = 50.54 mm
    assert cumulative_runoff_mm(100.0, 80) == pytest.approx(50.54, abs=0.01)


def test_no_runoff_below_initial_abstraction():
    # Ia = 12.7 mm for CN 80
    assert cumulative_runoff_mm(10.0, 80) == 0.0


def test_open_water_all_rain_runs_off():
    assert cumulative_runoff_mm(25.0, 100) == pytest.approx(25.0)


def test_more_impervious_means_more_runoff():
    p = 60.0
    assert cumulative_runoff_mm(p, 60) < cumulative_runoff_mm(p, 80) < cumulative_runoff_mm(p, 95)


def test_runoff_never_exceeds_rain():
    p = np.linspace(0, 300, 50)
    q = cumulative_runoff_mm(p, 90)
    assert np.all(q <= p + 1e-9)


def test_hourly_runoff_sums_to_cumulative():
    rain = np.array([2.0, 10.0, 30.0, 25.0, 5.0, 0.0])
    q_hourly = hourly_runoff_mm(rain, 80)
    assert q_hourly.sum() == pytest.approx(cumulative_runoff_mm(rain.sum(), 80))
    assert np.all(q_hourly >= 0)


def test_cn_from_landcover():
    classes = np.array(["forest", "paved", "unknown_thing"])
    cn = cn_from_landcover(classes)
    assert cn.tolist() == [CN_TABLE["forest"], CN_TABLE["paved"], DEFAULT_CN]


def test_invalid_cn_rejected():
    with pytest.raises(ValueError):
        retention_s(0)
    with pytest.raises(ValueError):
        retention_s(120)
