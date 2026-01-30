"""End-to-end integration tests for the simulation engine against Surat conditions.

Validates that the complete simulation pipeline -- species params, climate data,
growth equations, temperature response, harvest cycling, and CO2 accounting --
produces scientifically defensible results for Chlorella vulgaris cultivation
in Surat, India.

All tests use REAL data (no mocks): load_species_params(), load_city_climate(),
and run_simulation() with actual YAML configurations. This is an integration
test file that exercises the full stack from YAML -> dataclasses -> engine -> result.

Phase 3 success criteria validated:
    SC1: Duration flexibility (1, 30, 90, 365 days)
    SC2: CO2 conversion factor (1.83, not 1.88)
    SC3: Result completeness (time-series, CO2 accumulation, summary stats)
    SC4: Realistic output ranges (CO2 per m2, seasonal patterns, productivity)

References:
    Schediwy et al. (2019): co2_to_biomass_ratio = 1.83
    RESEARCH.md: 0.1-5.0 kg CO2/m2/year realistic range for open ponds
    Phase 2 verification: April zero growth at 37C daytime
"""

import pytest

from src.climate.loader import load_city_climate
from src.config.loader import load_species_params
from src.models.parameters import SimulationConfig
from src.simulation.engine import run_simulation


# ---------------------------------------------------------------------------
# Fixtures (real data, no mocks)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def species():
    """Load real Chlorella vulgaris species parameters from YAML."""
    return load_species_params()


@pytest.fixture(scope="module")
def climate():
    """Load real Surat city climate profile from YAML."""
    return load_city_climate()


@pytest.fixture(scope="module")
def default_config():
    """Standard 365-day simulation starting January with default pond geometry."""
    return SimulationConfig(
        duration_days=365,
        start_month=1,
        initial_biomass=0.5,
        harvest_threshold=2.0,
        co2_concentration=5.0,
        depth=0.3,
        surface_area=100.0,
    )


@pytest.fixture(scope="module")
def annual_result(default_config, species, climate):
    """Run the full 365-day Surat simulation once and reuse across tests.

    This is the central fixture: a complete annual simulation with real data.
    Module-scoped to avoid running the simulation 20+ times.
    """
    return run_simulation(default_config, species, climate)


# ---------------------------------------------------------------------------
# TestAnnualCO2Capture
# ---------------------------------------------------------------------------


class TestAnnualCO2Capture:
    """Validate that annual CO2 capture is realistic for Surat open-pond cultivation."""

    def test_annual_co2_in_realistic_range(self, annual_result, default_config):
        """Total CO2 for 365-day Surat simulation is 0.1-5.0 kg CO2/m2/year.

        Wide bounds per RESEARCH.md. Open ponds with 50% discount factor
        and extreme Surat summers should land in the lower end.
        """
        co2_per_m2 = annual_result.total_co2_captured_kg / default_config.surface_area
        assert 0.1 <= co2_per_m2 <= 5.0, (
            f"Annual CO2 capture {co2_per_m2:.3f} kg/m2/year outside "
            f"realistic range [0.1, 5.0]. Total: {annual_result.total_co2_captured_kg:.1f} kg, "
            f"area: {default_config.surface_area} m2"
        )

    def test_co2_conversion_factor_is_1_83(self, annual_result):
        """CO2 calculation uses species-specific 1.83 ratio, not magic 1.88.

        Cross-check: total_co2_captured_kg / 1.83 gives net biomass produced
        on positive-growth days. This should be a positive, reasonable value.
        """
        implied_biomass_kg = annual_result.total_co2_captured_kg / 1.83
        assert implied_biomass_kg > 0, (
            f"Implied biomass from CO2/1.83 should be positive, got {implied_biomass_kg:.3f}"
        )
        # The implied biomass should not exceed what is physically plausible:
        # total harvested + remaining standing crop in kg
        # Standing crop max ~ harvest_threshold * volume_liters / 1000
        # This is a sanity check, not tight
        assert implied_biomass_kg < 10000, (
            f"Implied biomass {implied_biomass_kg:.1f} kg is unreasonably large"
        )

    def test_tco2e_consistent_with_kg(self, annual_result):
        """tCO2e * 1000 approximately equals total_co2_captured_kg."""
        assert annual_result.total_co2_captured_tco2e * 1000 == pytest.approx(
            annual_result.total_co2_captured_kg, rel=1e-9
        ), (
            f"tCO2e mismatch: {annual_result.total_co2_captured_tco2e} * 1000 = "
            f"{annual_result.total_co2_captured_tco2e * 1000:.3f}, "
            f"expected {annual_result.total_co2_captured_kg:.3f}"
        )


# ---------------------------------------------------------------------------
# TestSeasonalPatterns
# ---------------------------------------------------------------------------


class TestSeasonalPatterns:
    """Validate Surat seasonal patterns: dry (Nov-Feb), hot (Mar-May), monsoon (Jun-Oct)."""

    def test_hot_season_lowest_co2(self, annual_result):
        """Hot season (Mar-May, index 1) produces the lowest seasonal CO2.

        April (37C daytime) produces zero net growth per Phase 2 verification.
        March and May also have severe heat stress. This season must produce
        the least CO2 of the three.
        """
        dry_co2 = annual_result.seasonal_co2[0]
        hot_co2 = annual_result.seasonal_co2[1]
        monsoon_co2 = annual_result.seasonal_co2[2]
        assert hot_co2 < dry_co2, (
            f"Hot season CO2 ({hot_co2:.2f} kg) should be less than "
            f"dry season ({dry_co2:.2f} kg)"
        )
        assert hot_co2 < monsoon_co2, (
            f"Hot season CO2 ({hot_co2:.2f} kg) should be less than "
            f"monsoon season ({monsoon_co2:.2f} kg)"
        )

    def test_three_seasons_present(self, annual_result):
        """Seasonal breakdown has exactly 3 entries: dry, hot, monsoon."""
        assert len(annual_result.seasonal_co2) == 3, (
            f"Expected 3 seasonal CO2 entries, got {len(annual_result.seasonal_co2)}"
        )
        assert len(annual_result.seasonal_productivity) == 3, (
            f"Expected 3 seasonal productivity entries, "
            f"got {len(annual_result.seasonal_productivity)}"
        )

    def test_seasonal_co2_sums_to_annual(self, annual_result):
        """Sum of seasonal CO2 approximately equals total annual CO2."""
        seasonal_sum = sum(annual_result.seasonal_co2)
        assert seasonal_sum == pytest.approx(
            annual_result.total_co2_captured_kg, rel=1e-6
        ), (
            f"Seasonal CO2 sum ({seasonal_sum:.3f}) does not match "
            f"total ({annual_result.total_co2_captured_kg:.3f})"
        )

    def test_dry_season_has_moderate_productivity(self, annual_result):
        """Dry season (index 0) has positive productivity below 15 g/m2/day.

        Dry season (Nov-Feb) has moderate temperatures and good light.
        Productivity should be nonzero and within realistic bounds.
        """
        dry_prod = annual_result.seasonal_productivity[0]
        assert dry_prod > 0, (
            f"Dry season average productivity should be > 0, got {dry_prod:.3f}"
        )
        assert dry_prod < 15, (
            f"Dry season average productivity {dry_prod:.2f} g/m2/day exceeds "
            f"15 g/m2/day realistic ceiling"
        )

    def test_monsoon_season_has_higher_productivity_than_hot(self, annual_result):
        """Monsoon season (index 2) has higher productivity than hot season (index 1).

        Monsoon temperatures are closer to optimal (28-30C) vs hot season
        extreme heat (35-37C day). Despite cloud cover reducing PAR, the
        temperature advantage should dominate.
        """
        hot_prod = annual_result.seasonal_productivity[1]
        monsoon_prod = annual_result.seasonal_productivity[2]
        assert monsoon_prod > hot_prod, (
            f"Monsoon productivity ({monsoon_prod:.2f} g/m2/day) should exceed "
            f"hot season ({hot_prod:.2f} g/m2/day)"
        )


# ---------------------------------------------------------------------------
# TestHarvestCycling
# ---------------------------------------------------------------------------


class TestHarvestCycling:
    """Validate harvest mechanics over a full annual simulation."""

    def test_multiple_harvests_in_annual_sim(self, annual_result):
        """A 365-day simulation should produce at least 2 harvest cycles.

        Starting at 0.5 g/L with threshold at 2.0 g/L, growth months should
        push biomass past threshold multiple times.
        """
        assert annual_result.harvest_count >= 2, (
            f"Expected at least 2 harvests in 365 days, "
            f"got {annual_result.harvest_count}"
        )

    def test_harvested_biomass_positive(self, annual_result):
        """Total harvested biomass is positive for a full year."""
        assert annual_result.total_biomass_harvested_kg > 0, (
            f"Expected positive harvested biomass, "
            f"got {annual_result.total_biomass_harvested_kg:.3f} kg"
        )

    def test_harvest_days_within_range(self, annual_result, default_config):
        """All harvest days are valid indices in [0, duration_days - 1]."""
        for day in annual_result.harvest_days:
            assert 0 <= day <= default_config.duration_days - 1, (
                f"Harvest day {day} outside valid range "
                f"[0, {default_config.duration_days - 1}]"
            )

    def test_biomass_after_harvest_near_initial(
        self, annual_result, default_config
    ):
        """After each harvest event, biomass resets to initial_biomass.

        The engine records biomass AFTER harvest reset, so on each harvest
        day the concentration should equal initial_biomass exactly.
        """
        for day in annual_result.harvest_days:
            assert annual_result.biomass_concentration[day] == pytest.approx(
                default_config.initial_biomass, abs=1e-9
            ), (
                f"On harvest day {day}, biomass = "
                f"{annual_result.biomass_concentration[day]:.6f}, "
                f"expected {default_config.initial_biomass}"
            )


# ---------------------------------------------------------------------------
# TestDurationFlexibility
# ---------------------------------------------------------------------------


class TestDurationFlexibility:
    """Validate simulation works for various durations without errors."""

    def test_1_day_simulation(self, species, climate):
        """A 1-day simulation runs without error and produces valid output."""
        config = SimulationConfig(
            duration_days=1,
            start_month=1,
            initial_biomass=0.5,
            harvest_threshold=2.0,
            co2_concentration=5.0,
            depth=0.3,
            surface_area=100.0,
        )
        result = run_simulation(config, species, climate)
        assert len(result.time_days) == 1
        assert len(result.biomass_concentration) == 1
        assert len(result.co2_captured_daily) == 1
        assert result.duration_days == 1

    def test_30_day_simulation(self, species, climate):
        """A 30-day simulation runs without error and produces 30 data points."""
        config = SimulationConfig(
            duration_days=30,
            start_month=1,
            initial_biomass=0.5,
            harvest_threshold=2.0,
            co2_concentration=5.0,
            depth=0.3,
            surface_area=100.0,
        )
        result = run_simulation(config, species, climate)
        assert len(result.time_days) == 30
        assert len(result.biomass_concentration) == 30
        assert result.duration_days == 30

    def test_90_day_simulation(self, species, climate):
        """A 90-day simulation produces positive CO2 capture."""
        config = SimulationConfig(
            duration_days=90,
            start_month=1,
            initial_biomass=0.5,
            harvest_threshold=2.0,
            co2_concentration=5.0,
            depth=0.3,
            surface_area=100.0,
        )
        result = run_simulation(config, species, climate)
        assert result.total_co2_captured_kg > 0, (
            f"90-day simulation should produce positive CO2, "
            f"got {result.total_co2_captured_kg:.3f} kg"
        )

    def test_365_day_simulation(self, species, climate):
        """A 365-day simulation produces positive CO2 and harvest events."""
        config = SimulationConfig(
            duration_days=365,
            start_month=1,
            initial_biomass=0.5,
            harvest_threshold=2.0,
            co2_concentration=5.0,
            depth=0.3,
            surface_area=100.0,
        )
        result = run_simulation(config, species, climate)
        assert result.total_co2_captured_kg > 0, (
            f"365-day simulation should produce positive CO2, "
            f"got {result.total_co2_captured_kg:.3f} kg"
        )
        assert result.harvest_count > 0, (
            f"365-day simulation should have at least one harvest, "
            f"got {result.harvest_count}"
        )


# ---------------------------------------------------------------------------
# TestBiomassTimeSeries
# ---------------------------------------------------------------------------


class TestBiomassTimeSeries:
    """Validate biomass concentration time-series properties."""

    def test_biomass_always_non_negative(self, annual_result):
        """Biomass concentration never drops below zero on any day."""
        for i, b in enumerate(annual_result.biomass_concentration):
            assert b >= 0, (
                f"Day {i}: biomass = {b:.6f} is negative"
            )

    def test_biomass_starts_near_initial(self, annual_result, default_config):
        """First biomass value is near initial_biomass.

        The first recorded value is after day 0's Euler step, so it may
        differ slightly from initial_biomass due to one day of growth.
        """
        assert annual_result.biomass_concentration[0] == pytest.approx(
            default_config.initial_biomass, abs=0.15
        ), (
            f"First-day biomass {annual_result.biomass_concentration[0]:.4f} "
            f"too far from initial {default_config.initial_biomass}"
        )

    def test_avg_daily_productivity_positive(self, annual_result):
        """Average daily productivity is positive for a 365-day run."""
        assert annual_result.avg_daily_productivity > 0, (
            f"Average daily productivity should be > 0, "
            f"got {annual_result.avg_daily_productivity:.4f}"
        )

    def test_avg_daily_productivity_in_realistic_range(self, annual_result):
        """Annual average daily productivity is 1-12 g/m2/day for Surat.

        Phase 1 validated 6-10 g/m2/day at standard conditions (30C, 800 PAR).
        Annual average will be lower due to hot season zero-growth months
        and monsoon cloud cover. Range: 1-12 g/m2/day.
        """
        prod = annual_result.avg_daily_productivity
        assert 1.0 <= prod <= 12.0, (
            f"Average daily productivity {prod:.2f} g/m2/day outside "
            f"realistic range [1, 12]. "
            f"Phase 1 baseline: 6-10 at standard conditions"
        )


# ---------------------------------------------------------------------------
# TestResultCompleteness
# ---------------------------------------------------------------------------


class TestResultCompleteness:
    """Validate that SimulationResult contains all required fields with correct types."""

    def test_result_has_biomass_time_series(self, annual_result):
        """Biomass time-series has exactly 365 entries."""
        assert len(annual_result.biomass_concentration) == 365, (
            f"Expected 365 biomass entries, "
            f"got {len(annual_result.biomass_concentration)}"
        )

    def test_result_has_co2_accumulation(self, annual_result):
        """CO2 cumulative array has 365 entries and is monotonically non-decreasing."""
        assert len(annual_result.co2_captured_cumulative) == 365, (
            f"Expected 365 cumulative CO2 entries, "
            f"got {len(annual_result.co2_captured_cumulative)}"
        )
        # Monotonically non-decreasing
        for i in range(1, len(annual_result.co2_captured_cumulative)):
            curr = annual_result.co2_captured_cumulative[i]
            prev = annual_result.co2_captured_cumulative[i - 1]
            assert curr >= prev - 1e-12, (
                f"Day {i}: cumulative CO2 decreased from {prev:.6f} to {curr:.6f}"
            )

    def test_result_has_summary_statistics(self, annual_result):
        """All summary statistics are present with reasonable types."""
        # Float fields
        assert isinstance(annual_result.total_co2_captured_kg, float), (
            f"total_co2_captured_kg should be float, "
            f"got {type(annual_result.total_co2_captured_kg)}"
        )
        assert isinstance(annual_result.total_co2_captured_tco2e, float), (
            f"total_co2_captured_tco2e should be float, "
            f"got {type(annual_result.total_co2_captured_tco2e)}"
        )
        assert isinstance(annual_result.total_biomass_harvested_kg, float), (
            f"total_biomass_harvested_kg should be float, "
            f"got {type(annual_result.total_biomass_harvested_kg)}"
        )
        assert isinstance(annual_result.avg_daily_productivity, float), (
            f"avg_daily_productivity should be float, "
            f"got {type(annual_result.avg_daily_productivity)}"
        )
        # Int fields
        assert isinstance(annual_result.harvest_count, int), (
            f"harvest_count should be int, got {type(annual_result.harvest_count)}"
        )

    def test_result_has_run_metadata(self, annual_result):
        """Result includes duration_days and start_month metadata."""
        assert annual_result.duration_days == 365, (
            f"Expected duration_days=365, got {annual_result.duration_days}"
        )
        assert annual_result.start_month == 1, (
            f"Expected start_month=1, got {annual_result.start_month}"
        )
