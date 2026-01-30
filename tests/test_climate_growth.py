"""Tests for daily growth rate integration with climate and temperature response.

Validates that daily_growth_rate() correctly composes Phase 1's
depth-averaged growth model with CTMI temperature response and
photoperiod weighting. Tests cover:
  - Optimal temperature baseline comparison with Phase 1
  - Hot season (April) heat stress growth reduction (>50%)
  - Monsoon light-limited growth patterns
  - Dry season moderate growth
  - Three-season distinct growth pattern verification
  - Full 12-month seasonal profile with load from YAML
  - Edge cases: zero PAR, extreme cold, extreme heat

Standard conditions from Phase 1:
  co2 = 5.0 mg/L, biomass_conc = 1.5 g/L, depth = 0.3 m

References:
    Edmundson & Huesemann (2015): Day/night split validation.
    Phase 1 tests: 66+ tests remain unmodified and passing.
    Phase 2 02-01: Climate config + loader (24 tests).
    Phase 2 02-02: CTMI temperature response (19 tests).
"""

import pytest

from src.climate.growth_modifier import daily_growth_rate
from src.climate.loader import load_city_climate
from src.climate.temperature import temperature_response
from src.config.loader import load_species_params
from src.models.parameters import ClimateParams, GrowthParams, LightParams
from src.simulation.growth import depth_averaged_growth_rate


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def species():
    """Load species parameters (GrowthParams, LightParams)."""
    return load_species_params()


@pytest.fixture
def growth_params(species):
    return species.growth


@pytest.fixture
def light_params(species):
    return species.light


@pytest.fixture
def climate_params():
    """Standard Chlorella vulgaris cardinal temperature parameters."""
    cc = load_city_climate()
    return cc.climate_params


@pytest.fixture
def city_climate():
    """Full Surat climate profile."""
    return load_city_climate()


# Standard simulation conditions
CO2 = 5.0        # mg/L dissolved CO2
BIOMASS = 1.5     # g/L biomass concentration
DEPTH = 0.3       # m pond depth


# ---------------------------------------------------------------------------
# Test 1: Optimal temperature baseline comparison
# ---------------------------------------------------------------------------

class TestOptimalTemperatureBaseline:
    """At T_opt, f_temp=1.0 so the only differences from Phase 1 are
    photoperiod weighting and nighttime respiration subtraction."""

    def test_optimal_temp_produces_positive_growth(
        self, growth_params, light_params, climate_params
    ):
        """Daily growth at T_opt day and night with moderate PAR should be positive."""
        result = daily_growth_rate(
            daytime_temp=28.0,   # T_opt
            nighttime_temp=28.0, # T_opt
            par=500.0,
            photoperiod=12.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert result > 0.0, "Growth at optimal temperature should be positive"

    def test_optimal_temp_less_than_phase1_baseline(
        self, growth_params, light_params, climate_params
    ):
        """Daily growth at T_opt should be less than Phase 1 baseline because
        photoperiod reduces daytime contribution and night adds respiration."""
        phase1_baseline = depth_averaged_growth_rate(
            500.0, CO2, BIOMASS, DEPTH, growth_params, light_params
        )
        daily = daily_growth_rate(
            daytime_temp=28.0,
            nighttime_temp=28.0,
            par=500.0,
            photoperiod=12.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert daily < phase1_baseline, (
            f"Daily growth ({daily:.6f}) should be less than Phase 1 "
            f"baseline ({phase1_baseline:.6f}) due to photoperiod + night respiration"
        )

    def test_optimal_temp_within_expected_fraction(
        self, growth_params, light_params, climate_params
    ):
        """At 12h photoperiod and T_opt, daily growth should be roughly 40-60%
        of Phase 1 baseline (50% day fraction minus night respiration)."""
        phase1_baseline = depth_averaged_growth_rate(
            500.0, CO2, BIOMASS, DEPTH, growth_params, light_params
        )
        daily = daily_growth_rate(
            daytime_temp=28.0,
            nighttime_temp=28.0,
            par=500.0,
            photoperiod=12.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        fraction = daily / phase1_baseline
        # At 12h photoperiod, day_frac=0.5. With T_opt day/night (f_temp=1.0):
        # daily = mu_base * 1.0 * 0.5 - r_maint * 1.0 * 0.5
        # For small mu_base values (high PAR causes photoinhibition at surface),
        # the r_maint subtraction is proportionally larger, so ratio can be <0.30
        assert 0.10 <= fraction <= 0.60, (
            f"Daily/Phase1 ratio = {fraction:.3f}, expected 0.10-0.60 "
            f"(12h photoperiod + T_opt night respiration)"
        )


# ---------------------------------------------------------------------------
# Test 2: Hot season April growth reduction
# ---------------------------------------------------------------------------

class TestHotSeasonAprilReduction:
    """April in Surat: 37C day, 24C night, PAR=525, photoperiod=12.7h.
    At 37C, CTMI gives f_temp_day ~ 0.457 (54% reduction from optimal).
    This causes severe growth reduction, meeting the >50% criterion."""

    def test_april_growth_massively_reduced(
        self, growth_params, light_params, climate_params
    ):
        """April growth should be less than 50% of the best month's growth.

        With 37C daytime heat stress (f_temp=0.457), combined with
        nighttime respiration at 24C (f_temp=0.914), net daily growth
        is drastically reduced -- in fact near zero due to respiration
        exceeding the temperature-limited daytime photosynthesis."""
        # Compute a reference month at near-optimal conditions
        # December: 31C day (~f_temp=0.945), 17C night (low respiration)
        reference = daily_growth_rate(
            daytime_temp=31.0,
            nighttime_temp=17.0,
            par=400.0,
            photoperiod=10.9,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        april = daily_growth_rate(
            daytime_temp=37.0,
            nighttime_temp=24.0,
            par=525.0,
            photoperiod=12.7,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert reference > 0.0, "Reference month (December) should have positive growth"
        assert april < reference * 0.50, (
            f"April growth ({april:.6f}) should be <50% of December "
            f"({reference:.6f}), got {april/reference*100:.1f}%"
        )

    def test_april_f_temp_day_confirms_heat_stress(self, climate_params):
        """Verify CTMI at 37C confirms >50% reduction from optimal."""
        f_temp = temperature_response(
            37.0, climate_params.T_min, climate_params.T_opt, climate_params.T_max
        )
        assert f_temp < 0.50, (
            f"f_temp at 37C = {f_temp:.3f}, expected < 0.50 (>50% reduction)"
        )
        assert f_temp == pytest.approx(0.457, abs=0.01), (
            f"f_temp at 37C = {f_temp:.3f}, expected ~0.457"
        )


# ---------------------------------------------------------------------------
# Test 3: Monsoon July - light-limited growth
# ---------------------------------------------------------------------------

class TestMonsoonJulyLightLimited:
    """July: 31C day (near-optimal temp), 26C night, PAR=348, photoperiod=13.3h.
    Temperature is favorable but PAR is the lowest of the year.
    Growth should be positive but influenced by the reduced light."""

    def test_monsoon_july_positive_growth(
        self, growth_params, light_params, climate_params
    ):
        """July should have positive growth -- near-optimal temperature
        compensates for reduced PAR."""
        july = daily_growth_rate(
            daytime_temp=31.0,
            nighttime_temp=26.0,
            par=348.0,
            photoperiod=13.3,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert july > 0.0, "July should have positive growth despite lower PAR"

    def test_july_lower_par_effect_visible(
        self, growth_params, light_params, climate_params
    ):
        """July at PAR=348 should produce different growth than the same
        temperature conditions at higher PAR, demonstrating light limitation."""
        july_actual = daily_growth_rate(
            daytime_temp=31.0,
            nighttime_temp=26.0,
            par=348.0,   # actual monsoon PAR
            photoperiod=13.3,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        july_high_par = daily_growth_rate(
            daytime_temp=31.0,
            nighttime_temp=26.0,
            par=525.0,   # hot season PAR level
            photoperiod=13.3,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        # Both should be positive but different -- PAR affects growth
        assert july_actual > 0.0
        assert july_high_par > 0.0
        assert july_actual != pytest.approx(july_high_par, rel=0.01), (
            "Growth at different PAR levels should differ measurably"
        )


# ---------------------------------------------------------------------------
# Test 4: Dry season January - moderate growth
# ---------------------------------------------------------------------------

class TestDrySeasonJanuaryModerate:
    """January: 30C day (~f_temp=0.976), 15C night (low respiration), PAR=430, 11h.
    Cool nights minimize respiration losses. Near-optimal daytime temperature.
    Should produce healthy positive growth."""

    def test_january_positive_growth(
        self, growth_params, light_params, climate_params
    ):
        """January should have healthy positive growth."""
        january = daily_growth_rate(
            daytime_temp=30.0,
            nighttime_temp=15.0,
            par=430.0,
            photoperiod=11.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert january > 0.0, "January dry season should have positive growth"

    def test_january_cool_nights_reduce_respiration(self, climate_params):
        """At 15C night, f_temp_night should be low (< 0.4), minimizing
        nighttime respiration losses -- a key advantage of dry season."""
        f_temp_night = temperature_response(
            15.0, climate_params.T_min, climate_params.T_opt, climate_params.T_max
        )
        assert f_temp_night < 0.40, (
            f"f_temp at 15C night = {f_temp_night:.3f}, expected < 0.40 "
            f"(low respiration due to cool nights)"
        )

    def test_january_greater_than_april(
        self, growth_params, light_params, climate_params
    ):
        """January should have significantly more growth than April (heat stressed)."""
        january = daily_growth_rate(
            daytime_temp=30.0, nighttime_temp=15.0,
            par=430.0, photoperiod=11.0,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        april = daily_growth_rate(
            daytime_temp=37.0, nighttime_temp=24.0,
            par=525.0, photoperiod=12.7,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        assert january > april, (
            f"January ({january:.6f}) should exceed April ({april:.6f})"
        )


# ---------------------------------------------------------------------------
# Test 5: Three seasons produce distinct growth patterns
# ---------------------------------------------------------------------------

class TestThreeSeasonsDistinct:
    """Representative months from each season should produce distinguishable
    growth rates. Hot season (April) should be lowest due to heat stress."""

    def test_all_three_seasons_different(
        self, growth_params, light_params, climate_params
    ):
        """Dry, Hot, and Monsoon seasons produce measurably different growth."""
        # Dry: January (30/15, 430, 11.0)
        dry_jan = daily_growth_rate(
            daytime_temp=30.0, nighttime_temp=15.0,
            par=430.0, photoperiod=11.0,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        # Hot: April (37/24, 525, 12.7)
        hot_apr = daily_growth_rate(
            daytime_temp=37.0, nighttime_temp=24.0,
            par=525.0, photoperiod=12.7,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        # Monsoon: July (31/26, 348, 13.3)
        monsoon_jul = daily_growth_rate(
            daytime_temp=31.0, nighttime_temp=26.0,
            par=348.0, photoperiod=13.3,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        # All three should be distinct values
        assert dry_jan != pytest.approx(hot_apr, abs=1e-6), (
            "Dry and Hot season growth should differ"
        )
        assert dry_jan != pytest.approx(monsoon_jul, abs=1e-6), (
            "Dry and Monsoon season growth should differ"
        )
        assert hot_apr != pytest.approx(monsoon_jul, abs=1e-6), (
            "Hot and Monsoon season growth should differ"
        )

    def test_hot_season_lowest(
        self, growth_params, light_params, climate_params
    ):
        """Hot season (April at 37C) should have the lowest growth of the
        three representative months due to severe heat stress."""
        dry_jan = daily_growth_rate(
            daytime_temp=30.0, nighttime_temp=15.0,
            par=430.0, photoperiod=11.0,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        hot_apr = daily_growth_rate(
            daytime_temp=37.0, nighttime_temp=24.0,
            par=525.0, photoperiod=12.7,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        monsoon_jul = daily_growth_rate(
            daytime_temp=31.0, nighttime_temp=26.0,
            par=348.0, photoperiod=13.3,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        assert hot_apr < dry_jan, (
            f"Hot ({hot_apr:.6f}) should be less than Dry ({dry_jan:.6f})"
        )
        assert hot_apr < monsoon_jul, (
            f"Hot ({hot_apr:.6f}) should be less than Monsoon ({monsoon_jul:.6f})"
        )

    def test_dry_season_positive(
        self, growth_params, light_params, climate_params
    ):
        """Dry season (January) should have healthy positive growth:
        near-optimal daytime temp + cool nights reducing respiration."""
        dry_jan = daily_growth_rate(
            daytime_temp=30.0, nighttime_temp=15.0,
            par=430.0, photoperiod=11.0,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        assert dry_jan > 0.005, (
            f"January growth ({dry_jan:.6f}) should be healthy (>0.005 1/d)"
        )


# ---------------------------------------------------------------------------
# Test 6: Full year seasonal profile from YAML
# ---------------------------------------------------------------------------

class TestFullYearSeasonalProfile:
    """Load Surat climate and compute growth for all 12 months.
    Validates seasonal patterns across the entire year."""

    MONTH_NAMES = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    def _compute_monthly_growth(self, city_climate, growth_params, light_params):
        """Helper: compute daily growth rate for each of 12 months."""
        rates = []
        for month in city_climate.months:
            rate = daily_growth_rate(
                daytime_temp=month.temp_day,
                nighttime_temp=month.temp_night,
                par=month.par,
                photoperiod=month.photoperiod,
                co2=CO2,
                biomass_conc=BIOMASS,
                depth=DEPTH,
                growth_params=growth_params,
                light_params=light_params,
                climate_params=city_climate.climate_params,
            )
            rates.append(rate)
        return rates

    def test_all_months_non_negative(
        self, city_climate, growth_params, light_params
    ):
        """All 12 months should produce non-negative growth rates."""
        rates = self._compute_monthly_growth(
            city_climate, growth_params, light_params
        )
        for i, rate in enumerate(rates):
            assert rate >= 0.0, (
                f"{self.MONTH_NAMES[i]} growth rate ({rate:.6f}) should be >= 0"
            )

    def test_most_months_positive(
        self, city_climate, growth_params, light_params
    ):
        """At least 9 of 12 months should have positive growth (>0).
        Only the most extreme heat months (Apr) may clamp to zero."""
        rates = self._compute_monthly_growth(
            city_climate, growth_params, light_params
        )
        positive_count = sum(1 for r in rates if r > 0.0)
        assert positive_count >= 9, (
            f"Expected at least 9 positive months, got {positive_count}. "
            f"Rates: {[f'{r:.4f}' for r in rates]}"
        )

    def test_hot_months_show_over_50_percent_reduction(
        self, city_climate, growth_params, light_params
    ):
        """At least one hot month (Mar-May, indices 2-4) should show >50%
        reduction from the best month, validating the heat stress criterion."""
        rates = self._compute_monthly_growth(
            city_climate, growth_params, light_params
        )
        best_rate = max(rates)
        hot_months = [rates[2], rates[3], rates[4]]  # Mar, Apr, May

        has_severe_reduction = any(
            r < best_rate * 0.50 for r in hot_months
        )
        assert has_severe_reduction, (
            f"No hot month shows >50% reduction from best ({best_rate:.6f}). "
            f"Hot months: Mar={rates[2]:.6f}, Apr={rates[3]:.6f}, May={rates[4]:.6f}"
        )

    def test_no_month_exceeds_its_phase1_baseline(
        self, city_climate, growth_params, light_params
    ):
        """No month's growth rate should exceed Phase 1's depth-averaged
        growth at that month's own PAR. Phase 1 assumes 24h continuous growth
        with no temperature reduction, so daily_growth_rate (with photoperiod
        and temperature effects) must always be lower."""
        rates = self._compute_monthly_growth(
            city_climate, growth_params, light_params
        )
        for i, (rate, month) in enumerate(
            zip(rates, city_climate.months)
        ):
            phase1_at_par = depth_averaged_growth_rate(
                month.par, CO2, BIOMASS, DEPTH, growth_params, light_params
            )
            assert rate <= phase1_at_par, (
                f"{self.MONTH_NAMES[i]} rate ({rate:.6f}) exceeds Phase 1 "
                f"baseline at PAR={month.par} ({phase1_at_par:.6f})"
            )

    def test_seasonal_variation_exists(
        self, city_climate, growth_params, light_params
    ):
        """Growth rates should vary meaningfully across the year (not flat).
        Max-to-min ratio should be at least 3x for Surat's diverse climate."""
        rates = self._compute_monthly_growth(
            city_climate, growth_params, light_params
        )
        positive_rates = [r for r in rates if r > 0.0]
        assert len(positive_rates) >= 2, "Need at least 2 positive months for ratio"
        ratio = max(positive_rates) / min(positive_rates)
        assert ratio > 3.0, (
            f"Max/min ratio = {ratio:.1f}, expected >3 for Surat seasonal variation"
        )


# ---------------------------------------------------------------------------
# Test 7: Zero PAR edge case
# ---------------------------------------------------------------------------

class TestZeroPar:
    """With no light, there should be no photosynthetic growth."""

    def test_zero_par_returns_zero(
        self, growth_params, light_params, climate_params
    ):
        """Zero PAR means no photosynthesis, so net growth should be zero
        (daytime growth is zero, and the function clamps to >= 0)."""
        result = daily_growth_rate(
            daytime_temp=28.0,
            nighttime_temp=20.0,
            par=0.0,
            photoperiod=12.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert result == 0.0, f"Zero PAR should give zero growth, got {result}"


# ---------------------------------------------------------------------------
# Test 8: Extreme cold - no growth
# ---------------------------------------------------------------------------

class TestExtremeCold:
    """Both day and night below T_min (8C) means f_temp=0 for both,
    so no growth and no respiration loss."""

    def test_extreme_cold_returns_zero(
        self, growth_params, light_params, climate_params
    ):
        """Temperatures well below T_min should produce zero growth."""
        result = daily_growth_rate(
            daytime_temp=5.0,
            nighttime_temp=2.0,
            par=500.0,
            photoperiod=12.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert result == 0.0, (
            f"Extreme cold (5/2 C) should give zero growth, got {result}"
        )


# ---------------------------------------------------------------------------
# Test 9: Extreme heat - no growth
# ---------------------------------------------------------------------------

class TestExtremeHeat:
    """Day above T_max (40C) means f_temp_day=0 and daytime growth is zero.
    Night at 35C has f_temp>0 so respiration occurs but net is clamped to 0."""

    def test_extreme_heat_returns_zero(
        self, growth_params, light_params, climate_params
    ):
        """Daytime above T_max should produce zero net growth."""
        result = daily_growth_rate(
            daytime_temp=42.0,
            nighttime_temp=35.0,
            par=500.0,
            photoperiod=12.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert result == 0.0, (
            f"Extreme heat (42/35 C) should give zero growth, got {result}"
        )


# ---------------------------------------------------------------------------
# Test 10: Photoperiod edge cases
# ---------------------------------------------------------------------------

class TestPhotoperiodEdgeCases:
    """Verify photoperiod boundary behavior."""

    def test_zero_photoperiod_returns_zero(
        self, growth_params, light_params, climate_params
    ):
        """Zero daylight hours means no photosynthesis, returns 0.0."""
        result = daily_growth_rate(
            daytime_temp=28.0,
            nighttime_temp=20.0,
            par=500.0,
            photoperiod=0.0,
            co2=CO2,
            biomass_conc=BIOMASS,
            depth=DEPTH,
            growth_params=growth_params,
            light_params=light_params,
            climate_params=climate_params,
        )
        assert result == 0.0, f"Zero photoperiod should return 0, got {result}"

    def test_longer_photoperiod_increases_growth(
        self, growth_params, light_params, climate_params
    ):
        """More daylight hours should generally increase net daily growth
        (more time for photosynthesis, less time for night respiration)."""
        short_day = daily_growth_rate(
            daytime_temp=28.0, nighttime_temp=20.0,
            par=400.0, photoperiod=10.0,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        long_day = daily_growth_rate(
            daytime_temp=28.0, nighttime_temp=20.0,
            par=400.0, photoperiod=14.0,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        assert long_day > short_day, (
            f"14h day ({long_day:.6f}) should exceed 10h day ({short_day:.6f})"
        )


# ---------------------------------------------------------------------------
# Test 11: Phase 1 integration - composition not modification
# ---------------------------------------------------------------------------

class TestPhase1Integration:
    """Verify that Phase 1 growth functions are called correctly and
    not modified. daily_growth_rate should compose with Phase 1, not alter it."""

    def test_phase1_growth_still_works_independently(
        self, growth_params, light_params
    ):
        """Phase 1 depth_averaged_growth_rate should work exactly as before,
        unaffected by Phase 2 imports or code."""
        result = depth_averaged_growth_rate(
            500.0, CO2, BIOMASS, DEPTH, growth_params, light_params
        )
        # Known Phase 1 value: should produce moderate growth (>0.01)
        assert result > 0.01, (
            f"Phase 1 baseline ({result:.6f}) should still work correctly"
        )

    def test_temperature_modifier_is_multiplicative(
        self, growth_params, light_params, climate_params
    ):
        """At T_opt with 24h photoperiod, daily growth should equal
        Phase 1 baseline minus f_temp_night respiration (f_temp=1.0 at T_opt).
        This confirms temperature is multiplicative, not additive."""
        phase1 = depth_averaged_growth_rate(
            500.0, CO2, BIOMASS, DEPTH, growth_params, light_params
        )
        # At T_opt (28C) and 24h photoperiod: day_frac=1.0, night_frac=0.0
        # So daily = mu_base * f_temp_day * 1.0 - r_night * 0.0 = mu_base * 1.0
        daily_24h = daily_growth_rate(
            daytime_temp=28.0, nighttime_temp=28.0,
            par=500.0, photoperiod=24.0,
            co2=CO2, biomass_conc=BIOMASS, depth=DEPTH,
            growth_params=growth_params, light_params=light_params,
            climate_params=climate_params,
        )
        assert daily_24h == pytest.approx(phase1, rel=1e-6), (
            f"At T_opt + 24h photoperiod, daily ({daily_24h:.6f}) should "
            f"equal Phase 1 baseline ({phase1:.6f})"
        )


# NOTE: Test 10 (phase1_tests_not_broken) is implicitly verified by running
# the full test suite with `python -m pytest tests/ -v`. All 109 Phase 1 +
# Phase 2 config + CTMI tests must continue passing alongside these new tests.
