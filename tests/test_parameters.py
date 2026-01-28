"""Tests for parameter dataclasses, YAML config loading, and validation.

Covers:
- Default parameter loading returns correct Chlorella vulgaris values
- Frozen dataclass immutability
- Hashability of all parameter types
- Pydantic validation rejects out-of-range values
- Citation data is accessible
- ASSUMED parameters are flagged in YAML notes
"""

import dataclasses
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config.loader import get_parameter_citations, load_species_params
from src.models.parameters import (
    GrowthParams,
    LightParams,
    ReactorParams,
    SpeciesParams,
)
from src.models.results import SimulationResult


# ---------------------------------------------------------------------------
# Default parameter loading
# ---------------------------------------------------------------------------


class TestDefaultParamsLoad:
    """Test that load_species_params() returns correct default values."""

    def test_default_params_load(self):
        params = load_species_params()
        assert isinstance(params, SpeciesParams)
        assert params.growth.mu_max == 1.0
        assert params.growth.Ks_co2 == 0.5
        assert params.growth.I_opt == 80.0
        assert params.growth.r_maintenance == 0.01
        assert params.growth.discount_factor == 0.5
        assert params.light.sigma_x == 0.2
        assert params.light.background_turbidity == 0.5
        assert params.carbon_content == 0.50
        assert params.co2_to_biomass_ratio == pytest.approx(1.83, rel=1e-2)

    def test_species_name(self):
        params = load_species_params()
        assert params.name == "Chlorella vulgaris"


# ---------------------------------------------------------------------------
# Frozen / immutable
# ---------------------------------------------------------------------------


class TestFrozenDataclasses:
    """Test that all parameter dataclasses are frozen (immutable)."""

    def test_growth_params_frozen(self):
        gp = GrowthParams(mu_max=1.0, Ks_co2=0.5, I_opt=80.0,
                          r_maintenance=0.01, discount_factor=0.5)
        with pytest.raises(dataclasses.FrozenInstanceError):
            gp.mu_max = 2.0

    def test_light_params_frozen(self):
        lp = LightParams(sigma_x=0.2, background_turbidity=0.5)
        with pytest.raises(dataclasses.FrozenInstanceError):
            lp.sigma_x = 0.3

    def test_reactor_params_frozen(self):
        rp = ReactorParams(depth=0.3, surface_area=10.0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            rp.depth = 0.5

    def test_species_params_frozen(self):
        params = load_species_params()
        with pytest.raises(dataclasses.FrozenInstanceError):
            params.name = "Something else"

    def test_params_are_frozen(self):
        """Mutation of any loaded param raises FrozenInstanceError."""
        params = load_species_params()
        with pytest.raises(dataclasses.FrozenInstanceError):
            params.growth.mu_max = 999.0


# ---------------------------------------------------------------------------
# Hashability
# ---------------------------------------------------------------------------


class TestHashability:
    """Test that all parameter dataclasses are hashable."""

    def test_growth_params_hashable(self):
        gp = GrowthParams(mu_max=1.0, Ks_co2=0.5, I_opt=80.0,
                          r_maintenance=0.01, discount_factor=0.5)
        assert isinstance(hash(gp), int)

    def test_light_params_hashable(self):
        lp = LightParams(sigma_x=0.2, background_turbidity=0.5)
        assert isinstance(hash(lp), int)

    def test_reactor_params_hashable(self):
        rp = ReactorParams(depth=0.3, surface_area=10.0)
        assert isinstance(hash(rp), int)

    def test_species_params_hashable(self):
        params = load_species_params()
        assert isinstance(hash(params), int)

    def test_params_are_hashable(self):
        """All parameter types can be used as dict keys / set members."""
        params = load_species_params()
        param_set = {params, params}
        assert len(param_set) == 1

    def test_simulation_result_hashable(self):
        params = load_species_params()
        result = SimulationResult(
            time_days=(0.0, 1.0),
            biomass_concentration=(1.0, 1.5),
            productivity_areal=(0.0, 5.0),
            co2_captured_cumulative=(0.0, 9.15),
            warnings=(),
            parameters_used=params,
        )
        assert isinstance(hash(result), int)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    """Test that Pydantic validation rejects out-of-range values."""

    def _write_yaml_with_override(self, overrides: dict) -> Path:
        """Write a temporary YAML file with specific parameter overrides."""
        data = {
            "species": "Test species",
            "growth": {
                "mu_max": {"value": 1.0, "unit": "1/d", "source": "test", "note": "test"},
                "Ks_co2": {"value": 0.5, "unit": "mg/L", "source": "test", "note": "test"},
                "I_opt": {"value": 80.0, "unit": "umol/m2/s", "source": "test", "note": "test"},
                "r_maintenance": {"value": 0.01, "unit": "1/d", "source": "test", "note": "test"},
                "discount_factor": {"value": 0.5, "unit": "dimensionless",
                                    "source": "test", "note": "test"},
            },
            "light": {
                "sigma_x": {"value": 0.2, "unit": "m2/g", "source": "test", "note": "test"},
                "background_turbidity": {"value": 0.5, "unit": "1/m",
                                         "source": "test", "note": "test"},
            },
            "carbon": {
                "carbon_content": {"value": 0.50, "unit": "g_C/g_DW",
                                   "source": "test", "note": "test"},
                "co2_to_biomass_ratio": {"value": 1.83, "unit": "g_CO2/g_DW",
                                         "source": "test", "note": "test"},
            },
        }

        # Apply overrides (e.g., {"growth": {"mu_max": {"value": 999}}})
        for section, params in overrides.items():
            for param_name, param_overrides in params.items():
                data[section][param_name].update(param_overrides)

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(data, tmp)
        tmp.close()
        return Path(tmp.name)

    def test_invalid_mu_max_too_high(self):
        path = self._write_yaml_with_override(
            {"growth": {"mu_max": {"value": 10.0}}}
        )
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            load_species_params(path)

    def test_invalid_mu_max_too_low(self):
        path = self._write_yaml_with_override(
            {"growth": {"mu_max": {"value": 0.001}}}
        )
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            load_species_params(path)

    def test_invalid_carbon_content_too_high(self):
        path = self._write_yaml_with_override(
            {"carbon": {"carbon_content": {"value": 0.95}}}
        )
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            load_species_params(path)

    def test_invalid_sigma_x_negative(self):
        path = self._write_yaml_with_override(
            {"light": {"sigma_x": {"value": -0.1}}}
        )
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            load_species_params(path)

    def test_invalid_params_rejected(self):
        """Out-of-range values raise ValidationError."""
        path = self._write_yaml_with_override(
            {"growth": {"discount_factor": {"value": 5.0}}}
        )
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            load_species_params(path)


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------


class TestCitations:
    """Test that citation data is accessible from the YAML."""

    def test_citations_available(self):
        citations = get_parameter_citations()
        assert isinstance(citations, dict)
        assert "species" in citations
        # Check that growth parameters have source keys
        for param_name in ["mu_max", "Ks_co2", "I_opt", "r_maintenance", "discount_factor"]:
            assert "source" in citations["growth"][param_name], (
                f"Missing 'source' for growth.{param_name}"
            )
            assert "note" in citations["growth"][param_name], (
                f"Missing 'note' for growth.{param_name}"
            )

    def test_citations_reference_schediwy(self):
        citations = get_parameter_citations()
        schediwy_found = False
        for section_name in ["growth", "light", "carbon"]:
            section = citations[section_name]
            for param_data in section.values():
                if isinstance(param_data, dict) and "source" in param_data:
                    if "Schediwy" in param_data["source"]:
                        schediwy_found = True
                        break
        assert schediwy_found, "No citation references Schediwy et al."


# ---------------------------------------------------------------------------
# ASSUMED parameters flagging
# ---------------------------------------------------------------------------


class TestAssumedParams:
    """Test that parameters marked ASSUMED are flagged in their notes."""

    def test_assumed_params_flagged(self):
        """Parameters without primary-source backing have 'ASSUMED' in note."""
        citations = get_parameter_citations()

        # Known ASSUMED parameters
        assumed_params = [
            ("growth", "r_maintenance"),
            ("light", "background_turbidity"),
        ]

        for section, param in assumed_params:
            note = citations[section][param].get("note", "")
            assert "ASSUMED" in note, (
                f"{section}.{param} should be flagged as ASSUMED in its note, "
                f"but note is: '{note}'"
            )

    def test_non_assumed_params_not_flagged(self):
        """Parameters with primary-source backing should NOT say ASSUMED."""
        citations = get_parameter_citations()

        non_assumed_params = [
            ("growth", "mu_max"),
            ("growth", "Ks_co2"),
            ("growth", "I_opt"),
            ("carbon", "carbon_content"),
        ]

        for section, param in non_assumed_params:
            note = citations[section][param].get("note", "")
            assert "ASSUMED" not in note, (
                f"{section}.{param} should NOT be flagged as ASSUMED, "
                f"but note is: '{note}'"
            )


# ---------------------------------------------------------------------------
# SimulationResult
# ---------------------------------------------------------------------------


class TestSimulationResult:
    """Test the SimulationResult dataclass."""

    def test_peak_productivity(self):
        params = load_species_params()
        result = SimulationResult(
            time_days=(0.0, 1.0, 2.0),
            biomass_concentration=(1.0, 1.5, 2.0),
            productivity_areal=(0.0, 5.0, 8.0),
            co2_captured_cumulative=(0.0, 9.15, 23.79),
            warnings=(),
            parameters_used=params,
        )
        assert result.peak_productivity == 8.0

    def test_peak_productivity_empty(self):
        params = load_species_params()
        result = SimulationResult(
            time_days=(),
            biomass_concentration=(),
            productivity_areal=(),
            co2_captured_cumulative=(),
            warnings=(),
            parameters_used=params,
        )
        assert result.peak_productivity == 0.0
