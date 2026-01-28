"""Tests for Beer-Lambert light attenuation and depth-averaged irradiance.

Tests validate:
- Beer-Lambert law: I(z) = I0 * exp(-(sigma_x * X + k_bg) * z)
- Depth-averaged irradiance: I_avg = I0 / (K*D) * (1 - exp(-K*D))
- Behavioral properties: deeper/denser = less light, bounds, edge cases

Reference values hand-calculated from:
- Razzak et al. (2024) Eq. 18-19
- Schediwy et al. (2019) Eq. 3, 10
"""

import math

import pytest

from src.simulation.light import beer_lambert, depth_averaged_irradiance


# --- Beer-Lambert tests ---


class TestBeerLambert:
    """Tests for the beer_lambert() function."""

    def test_beer_lambert_surface(self):
        """At depth=0, irradiance equals surface irradiance regardless of attenuation."""
        result = beer_lambert(500.0, 0.2, 1.0, 0.0)
        assert result == 500.0

    def test_beer_lambert_known_values(self):
        """Verify against hand-calculated values for known inputs."""
        # Case 1: I0=500, sigma_x=0.2, X=1.0, depth=0.3, k_bg=0.5
        # K = 0.2*1.0 + 0.5 = 0.7, I = 500 * exp(-0.7*0.3) = 500 * exp(-0.21)
        expected_1 = 500.0 * math.exp(-0.21)
        result_1 = beer_lambert(500.0, 0.2, 1.0, 0.3, 0.5)
        assert result_1 == pytest.approx(expected_1, rel=1e-3)

        # Case 2: I0=500, sigma_x=0.2, X=1.0, depth=1.0, k_bg=0.5
        # K = 0.7, I = 500 * exp(-0.7) ~ 248.4
        expected_2 = 500.0 * math.exp(-0.7)
        result_2 = beer_lambert(500.0, 0.2, 1.0, 1.0, 0.5)
        assert result_2 == pytest.approx(expected_2, rel=1e-3)

    def test_beer_lambert_no_biomass(self):
        """With zero biomass and zero background turbidity, no attenuation occurs."""
        result = beer_lambert(500.0, 0.2, 0.0, 0.3, 0.0)
        assert result == 500.0

    def test_beer_lambert_no_light(self):
        """With zero incoming irradiance, output is always zero."""
        result = beer_lambert(0.0, 0.2, 1.0, 0.3)
        assert result == 0.0


# --- Depth-averaged irradiance tests ---


class TestDepthAveragedIrradiance:
    """Tests for the depth_averaged_irradiance() function."""

    def test_depth_avg_known_values(self):
        """Verify against hand-calculated analytical formula results."""
        # Case 1: I0=500, sigma_x=0.2, X=1.0, depth=0.3, k_bg=0.5
        # K = 0.7, K*D = 0.21
        # I_avg = 500 / (0.7*0.3) * (1 - exp(-0.21)) = 500/0.21 * (1 - exp(-0.21))
        K = 0.7
        D = 0.3
        expected_1 = 500.0 / (K * D) * (1.0 - math.exp(-K * D))
        result_1 = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.3, 0.5)
        assert result_1 == pytest.approx(expected_1, rel=1e-3)

        # Case 2: deeper pond -> less average light
        # I0=500, sigma_x=0.2, X=1.0, depth=0.5, k_bg=0.5
        # K = 0.7, K*D = 0.35
        K2, D2 = 0.7, 0.5
        expected_2 = 500.0 / (K2 * D2) * (1.0 - math.exp(-K2 * D2))
        result_2 = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.5, 0.5)
        assert result_2 == pytest.approx(expected_2, rel=1e-3)

        # Case 3: denser culture -> less average light
        # I0=500, sigma_x=0.2, X=5.0, depth=0.3, k_bg=0.5
        # K = 0.2*5.0 + 0.5 = 1.5, K*D = 0.45
        K3, D3 = 1.5, 0.3
        expected_3 = 500.0 / (K3 * D3) * (1.0 - math.exp(-K3 * D3))
        result_3 = depth_averaged_irradiance(500.0, 0.2, 5.0, 0.3, 0.5)
        assert result_3 == pytest.approx(expected_3, rel=1e-3)

    def test_depth_avg_deeper_is_darker(self):
        """Deeper ponds get less average light than shallow ponds (same biomass)."""
        shallow = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.1, 0.5)
        deep = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.5, 0.5)
        assert deep < shallow

    def test_depth_avg_denser_is_darker(self):
        """Denser cultures get less average light than dilute cultures (same depth)."""
        dilute = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.3, 0.5)
        dense = depth_averaged_irradiance(500.0, 0.2, 5.0, 0.3, 0.5)
        assert dense < dilute

    def test_depth_avg_between_surface_and_bottom(self):
        """Depth-averaged irradiance is bounded: bottom <= avg <= surface."""
        I0 = 500.0
        sigma_x = 0.2
        X = 1.0
        depth = 0.3
        k_bg = 0.5

        I_surface = beer_lambert(I0, sigma_x, X, 0.0, k_bg)
        I_bottom = beer_lambert(I0, sigma_x, X, depth, k_bg)
        I_avg = depth_averaged_irradiance(I0, sigma_x, X, depth, k_bg)

        assert I_bottom <= I_avg <= I_surface

    def test_depth_avg_no_extinction(self):
        """With zero extinction coefficient (K=0), returns I0."""
        result = depth_averaged_irradiance(500.0, 0.0, 0.0, 0.3, 0.0)
        assert result == pytest.approx(500.0, rel=1e-3)

    def test_depth_avg_no_light(self):
        """With zero incoming irradiance, output is always zero."""
        result = depth_averaged_irradiance(0.0, 0.2, 1.0, 0.3)
        assert result == 0.0

    def test_depth_attenuation_visible_above_03m(self):
        """Measurable attenuation difference between 0.1m and >0.3m depth.

        Phase 1 success criterion: deeper ponds (>0.3m) show measurable
        attenuation compared to shallow ponds.
        """
        shallow = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.1, 0.5)
        medium = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.3, 0.5)
        deep = depth_averaged_irradiance(500.0, 0.2, 1.0, 0.5, 0.5)

        # Each step deeper should show measurably less light
        assert medium < shallow, "0.3m should have less light than 0.1m"
        assert deep < medium, "0.5m should have less light than 0.3m"

        # The attenuation should be meaningful (at least 1% difference)
        attenuation_01_to_03 = (shallow - medium) / shallow
        attenuation_03_to_05 = (medium - deep) / medium
        assert attenuation_01_to_03 > 0.01, "At least 1% attenuation from 0.1m to 0.3m"
        assert attenuation_03_to_05 > 0.01, "At least 1% attenuation from 0.3m to 0.5m"
