"""Tests for Surat climate config loading and validation.

Verifies that the climate loader correctly loads surat.yaml, validates
all parameter ranges, and produces frozen/hashable CityClimate dataclasses.

Tests cover:
    - Default Surat profile loads with 12 months
    - Monthly data ranges are physically realistic
    - Season classification matches expected assignments
    - CityClimate is frozen and hashable (for Streamlit caching)
    - Cardinal temperature parameters match expected values
"""

import pytest

from src.climate.loader import load_city_climate, get_climate_citations
from src.models.parameters import CityClimate, ClimateParams, MonthlyClimate


# --- Default Surat profile loading ---


class TestLoadSuratDefaults:
    """Surat climate profile loads correctly with expected structure."""

    def test_city_is_surat(self):
        """Default profile loads Surat, India."""
        climate = load_city_climate()
        assert climate.city == "Surat"
        assert climate.country == "India"

    def test_twelve_months(self):
        """Profile contains exactly 12 months of data."""
        climate = load_city_climate()
        assert len(climate.months) == 12

    def test_climate_params_values(self):
        """Cardinal temperature parameters match expected values."""
        climate = load_city_climate()
        assert climate.climate_params.T_min == 8.0
        assert climate.climate_params.T_opt == 28.0
        assert climate.climate_params.T_max == 40.0

    def test_climate_params_type(self):
        """Climate params is a ClimateParams instance."""
        climate = load_city_climate()
        assert isinstance(climate.climate_params, ClimateParams)

    def test_latitude_longitude(self):
        """Surat coordinates are correct."""
        climate = load_city_climate()
        assert climate.latitude == pytest.approx(21.17, abs=0.01)
        assert climate.longitude == pytest.approx(72.83, abs=0.01)


# --- Monthly data range validation ---


class TestMonthlyDataRanges:
    """All monthly values fall within physically realistic ranges."""

    @pytest.fixture
    def climate(self):
        return load_city_climate()

    def test_temp_day_range(self, climate):
        """Daytime temperatures are in [15, 45] C for all months."""
        for month in climate.months:
            assert 15 <= month.temp_day <= 45, (
                f"temp_day={month.temp_day} out of range for {month.season}"
            )

    def test_temp_night_range(self, climate):
        """Nighttime temperatures are in [10, 30] C for all months."""
        for month in climate.months:
            assert 10 <= month.temp_night <= 30, (
                f"temp_night={month.temp_night} out of range for {month.season}"
            )

    def test_par_range(self, climate):
        """PAR values are in [300, 600] umol/m2/s for all months."""
        for month in climate.months:
            assert 300 <= month.par <= 600, (
                f"par={month.par} out of range for {month.season}"
            )

    def test_photoperiod_range(self, climate):
        """Photoperiod values are in [10, 14] hours for all months."""
        for month in climate.months:
            assert 10 <= month.photoperiod <= 14, (
                f"photoperiod={month.photoperiod} out of range for {month.season}"
            )

    def test_day_warmer_than_night(self, climate):
        """Daytime temperature exceeds nighttime for all months."""
        for month in climate.months:
            assert month.temp_day > month.temp_night, (
                f"temp_day={month.temp_day} <= temp_night={month.temp_night}"
            )

    def test_cloud_cover_fraction_range(self, climate):
        """Cloud cover is in [0, 1] for all months."""
        for month in climate.months:
            assert 0.0 <= month.cloud_cover_fraction <= 1.0, (
                f"cloud_cover_fraction={month.cloud_cover_fraction} out of range"
            )

    def test_rainfall_non_negative(self, climate):
        """Rainfall is non-negative for all months."""
        for month in climate.months:
            assert month.rainfall >= 0, (
                f"rainfall={month.rainfall} is negative"
            )


# --- Season classification ---


class TestSeasonClassification:
    """Season assignments match Surat's three-season pattern."""

    @pytest.fixture
    def climate(self):
        return load_city_climate()

    def test_dry_season_months(self, climate):
        """Oct-Feb are classified as dry season (indices 0,1,9,10,11)."""
        dry_indices = [0, 1, 9, 10, 11]  # Jan, Feb, Oct, Nov, Dec
        for idx in dry_indices:
            assert climate.months[idx].season == "dry", (
                f"Month index {idx} should be 'dry', got '{climate.months[idx].season}'"
            )

    def test_hot_season_months(self, climate):
        """Mar-May are classified as hot season (indices 2,3,4)."""
        hot_indices = [2, 3, 4]  # Mar, Apr, May
        for idx in hot_indices:
            assert climate.months[idx].season == "hot", (
                f"Month index {idx} should be 'hot', got '{climate.months[idx].season}'"
            )

    def test_monsoon_season_months(self, climate):
        """Jun-Sep are classified as monsoon season (indices 5,6,7,8)."""
        monsoon_indices = [5, 6, 7, 8]  # Jun, Jul, Aug, Sep
        for idx in monsoon_indices:
            assert climate.months[idx].season == "monsoon", (
                f"Month index {idx} should be 'monsoon', got '{climate.months[idx].season}'"
            )

    def test_three_seasons_present(self, climate):
        """All three seasons (dry, hot, monsoon) are present in the data."""
        seasons = {month.season for month in climate.months}
        assert seasons == {"dry", "hot", "monsoon"}


# --- Frozen and hashable ---


class TestFrozenHashable:
    """CityClimate and its components are frozen and hashable."""

    def test_city_climate_hashable(self):
        """CityClimate is hashable (for Streamlit caching)."""
        climate = load_city_climate()
        h = hash(climate)
        assert isinstance(h, int)

    def test_climate_params_hashable(self):
        """ClimateParams is hashable."""
        climate = load_city_climate()
        h = hash(climate.climate_params)
        assert isinstance(h, int)

    def test_monthly_climate_hashable(self):
        """Each MonthlyClimate is hashable."""
        climate = load_city_climate()
        for month in climate.months:
            h = hash(month)
            assert isinstance(h, int)

    def test_city_climate_frozen(self):
        """CityClimate is frozen (immutable)."""
        climate = load_city_climate()
        with pytest.raises(AttributeError):
            climate.city = "Mumbai"

    def test_climate_params_frozen(self):
        """ClimateParams is frozen (immutable)."""
        climate = load_city_climate()
        with pytest.raises(AttributeError):
            climate.climate_params.T_opt = 30.0


# --- Citations ---


class TestClimateCitations:
    """Climate citations are accessible from the YAML."""

    def test_citations_available(self):
        """get_climate_citations returns raw YAML with source fields."""
        citations = get_climate_citations()
        assert "city" in citations
        assert "months" in citations
        assert "temperature_params" in citations

    def test_temperature_params_sourced(self):
        """Temperature parameters include source citations."""
        citations = get_climate_citations()
        t_params = citations["temperature_params"]
        for param_name in ["T_min", "T_opt", "T_max"]:
            assert "source" in t_params[param_name], (
                f"{param_name} missing source citation"
            )

    def test_monthly_data_sourced(self):
        """Monthly data fields include source citations."""
        citations = get_climate_citations()
        jan = citations["months"]["january"]
        for field in ["temp_day", "temp_night", "par", "photoperiod"]:
            assert "source" in jan[field], (
                f"January {field} missing source citation"
            )
