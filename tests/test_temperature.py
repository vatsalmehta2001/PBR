"""Tests for CTMI cardinal temperature model (Rosso et al. 1993).

Verifies temperature_response() behavior at critical temperature points
using Chlorella vulgaris defaults: T_min=8, T_opt=28, T_max=40.

Verification values computed from the CTMI equation:
    phi(T) = (T - T_max)(T - T_min)^2 /
             [(T_opt - T_min) * ((T_opt - T_min)(T - T_opt)
               - (T_opt - T_max)(T_opt + T_min - 2T))]

References:
    Rosso et al. (1993): CTMI original formulation
    Bernard & Remond (2012): Validation for microalgae
    02-RESEARCH.md: Verification values table
"""

import pytest

from src.climate.temperature import temperature_response

# Chlorella vulgaris cardinal temperatures
T_MIN = 8.0
T_OPT = 28.0
T_MAX = 40.0


# --- Boundary behavior ---


class TestBoundaryTemperatures:
    """CTMI returns exactly 0.0 at T_min and T_max boundaries."""

    def test_at_t_min_returns_zero(self):
        """Growth is exactly zero at the minimum cardinal temperature."""
        assert temperature_response(8.0, T_MIN, T_OPT, T_MAX) == 0.0

    def test_at_t_max_returns_zero(self):
        """Growth is exactly zero at the maximum cardinal temperature."""
        assert temperature_response(40.0, T_MIN, T_OPT, T_MAX) == 0.0

    def test_below_t_min_returns_zero(self):
        """Growth is zero below T_min (too cold for growth)."""
        assert temperature_response(5.0, T_MIN, T_OPT, T_MAX) == 0.0

    def test_above_t_max_returns_zero(self):
        """Growth is zero above T_max (lethal temperature)."""
        assert temperature_response(42.0, T_MIN, T_OPT, T_MAX) == 0.0

    def test_negative_temp_returns_zero(self):
        """Growth is zero at negative temperatures (well below T_min)."""
        assert temperature_response(-5.0, T_MIN, T_OPT, T_MAX) == 0.0


# --- Optimal temperature ---


class TestOptimalTemperature:
    """CTMI returns exactly 1.0 at T_opt."""

    def test_at_t_opt_returns_one(self):
        """Growth is exactly 1.0 (100%) at the optimal temperature."""
        assert temperature_response(28.0, T_MIN, T_OPT, T_MAX) == pytest.approx(
            1.0
        )


# --- Key verification points from RESEARCH.md ---


class TestVerificationPoints:
    """CTMI matches expected values at key temperature points.

    Values from 02-RESEARCH.md verification table, computed analytically.
    Tolerances are abs=0.02 (2% absolute) to account for rounding.
    """

    def test_cold_stress_15c(self):
        """At 15C, cold stress reduces growth to ~20% of optimal."""
        result = temperature_response(15.0, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(0.195, abs=0.02)

    def test_suboptimal_20c(self):
        """At 20C, growth is ~54% of optimal."""
        result = temperature_response(20.0, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(0.535, abs=0.02)

    def test_near_optimal_25c(self):
        """At 25C, growth is ~88% of optimal."""
        result = temperature_response(25.0, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(0.879, abs=0.02)

    def test_slight_decline_30c(self):
        """At 30C, growth declines slightly to ~94% of optimal."""
        result = temperature_response(30.0, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(0.938, abs=0.02)

    def test_heat_stress_35c(self):
        """At 35C, heat stress reduces growth to ~44% (>50% reduction from optimal).

        This is the KEY success criterion for Phase 2: growth drops >50%
        at temperatures exceeding 35C in Surat's pre-monsoon season.
        """
        result = temperature_response(35.0, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(0.439, abs=0.02)

    def test_severe_heat_38c(self):
        """At 38C, severe heat stress reduces growth to ~9%."""
        result = temperature_response(38.0, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(0.094, abs=0.02)

    def test_barely_growing_10c(self):
        """At 10C, barely any growth (~2%)."""
        result = temperature_response(10.0, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(0.021, abs=0.02)


# --- Monotonicity ---


class TestMonotonicity:
    """CTMI increases monotonically to T_opt, then decreases."""

    def test_monotonic_increase_to_optimum(self):
        """Growth increases monotonically from T_min toward T_opt."""
        f15 = temperature_response(15.0, T_MIN, T_OPT, T_MAX)
        f20 = temperature_response(20.0, T_MIN, T_OPT, T_MAX)
        f25 = temperature_response(25.0, T_MIN, T_OPT, T_MAX)
        f28 = temperature_response(28.0, T_MIN, T_OPT, T_MAX)
        assert f15 < f20 < f25 < f28

    def test_decline_above_optimum(self):
        """Growth declines monotonically above T_opt toward T_max."""
        f28 = temperature_response(28.0, T_MIN, T_OPT, T_MAX)
        f30 = temperature_response(30.0, T_MIN, T_OPT, T_MAX)
        f35 = temperature_response(35.0, T_MIN, T_OPT, T_MAX)
        f38 = temperature_response(38.0, T_MIN, T_OPT, T_MAX)
        assert f28 > f30 > f35 > f38


# --- Output clamping and numerical guards ---


class TestOutputClampingAndGuards:
    """CTMI output is always in [0, 1] and handles edge cases."""

    def test_output_always_in_unit_interval(self):
        """For all integer temperatures from -5 to 50, output is in [0, 1]."""
        for T in range(-5, 51):
            result = temperature_response(float(T), T_MIN, T_OPT, T_MAX)
            assert 0.0 <= result <= 1.0, (
                f"temperature_response({T}) = {result} outside [0, 1]"
            )

    def test_near_t_opt_numerical_guard(self):
        """Temperature very close to T_opt (within 1e-10) returns ~1.0.

        Guards against floating-point division issues near T_opt where
        both numerator and denominator approach special values.
        """
        result = temperature_response(28.0 + 1e-11, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(1.0, abs=0.001)

    def test_near_t_opt_just_below(self):
        """Temperature just below T_opt also handled by numerical guard."""
        result = temperature_response(28.0 - 1e-11, T_MIN, T_OPT, T_MAX)
        assert result == pytest.approx(1.0, abs=0.001)
