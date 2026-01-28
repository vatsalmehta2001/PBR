"""YAML config loader with Pydantic validation for species parameters.

Loads species kinetic parameters from YAML files that include per-parameter
citations (value + unit + source + note). Validates ranges through Pydantic,
then returns frozen dataclasses for simulation consumption.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from src.models.parameters import GrowthParams, LightParams, SpeciesParams


# ---------------------------------------------------------------------------
# Pydantic validation model (range checking only)
# ---------------------------------------------------------------------------

class GrowthParamsValidator(BaseModel):
    """Validates growth parameter ranges."""

    mu_max: float = Field(ge=0.1, le=5.0)
    Ks_co2: float = Field(ge=0.01, le=10.0)
    I_opt: float = Field(ge=10.0, le=500.0)
    r_maintenance: float = Field(ge=0.0, le=0.1)
    discount_factor: float = Field(ge=0.1, le=1.0)


class LightParamsValidator(BaseModel):
    """Validates light parameter ranges."""

    sigma_x: float = Field(ge=0.01, le=1.0)
    background_turbidity: float = Field(ge=0.0, le=5.0)


class CarbonParamsValidator(BaseModel):
    """Validates carbon stoichiometry parameter ranges."""

    carbon_content: float = Field(ge=0.3, le=0.7)
    co2_to_biomass_ratio: float = Field(ge=1.0, le=3.0)


class SpeciesParamsValidator(BaseModel):
    """Top-level validator for the complete species parameter set."""

    species: str
    growth: GrowthParamsValidator
    light: LightParamsValidator
    carbon: CarbonParamsValidator


# ---------------------------------------------------------------------------
# Helper: extract numeric values from YAML's nested value/unit/source dicts
# ---------------------------------------------------------------------------

def _extract_values(section: dict[str, Any]) -> dict[str, Any]:
    """Extract numeric 'value' fields from a YAML section.

    Each YAML parameter entry is a dict with keys: value, unit, source, note.
    This function extracts just the 'value' for each parameter name.
    """
    extracted = {}
    for key, entry in section.items():
        if isinstance(entry, dict) and "value" in entry:
            extracted[key] = entry["value"]
        else:
            extracted[key] = entry
    return extracted


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFAULT_YAML_PATH = Path(__file__).parent / "species_params.yaml"


def load_species_params(path: str | Path | None = None) -> SpeciesParams:
    """Load and validate species parameters from a YAML config file.

    Args:
        path: Path to a species_params.yaml file. If None, uses the bundled
              default (Chlorella vulgaris) config.

    Returns:
        A frozen SpeciesParams dataclass with validated parameter values.

    Raises:
        pydantic.ValidationError: If any parameter is outside its valid range.
        FileNotFoundError: If the specified YAML file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    yaml_path = Path(path) if path is not None else _DEFAULT_YAML_PATH

    with open(yaml_path) as f:
        raw_data = yaml.safe_load(f)

    # Extract numeric values from nested value/unit/source structure
    flat_data = {
        "species": raw_data["species"],
        "growth": _extract_values(raw_data["growth"]),
        "light": _extract_values(raw_data["light"]),
        "carbon": _extract_values(raw_data["carbon"]),
    }

    # Validate through Pydantic
    validated = SpeciesParamsValidator(**flat_data)

    # Build frozen dataclasses (not Pydantic models)
    growth = GrowthParams(
        mu_max=validated.growth.mu_max,
        Ks_co2=validated.growth.Ks_co2,
        I_opt=validated.growth.I_opt,
        r_maintenance=validated.growth.r_maintenance,
        discount_factor=validated.growth.discount_factor,
    )

    light = LightParams(
        sigma_x=validated.light.sigma_x,
        background_turbidity=validated.light.background_turbidity,
    )

    return SpeciesParams(
        name=validated.species,
        growth=growth,
        light=light,
        carbon_content=validated.carbon.carbon_content,
        co2_to_biomass_ratio=validated.carbon.co2_to_biomass_ratio,
    )


def get_parameter_citations(path: str | Path | None = None) -> dict:
    """Load and return the full YAML data including citations.

    Returns the raw YAML structure with value, unit, source, and note
    for each parameter. Useful for transparency display in the UI.

    Args:
        path: Path to a species_params.yaml file. If None, uses the bundled
              default config.

    Returns:
        Dictionary with the complete YAML structure including citations.
    """
    yaml_path = Path(path) if path is not None else _DEFAULT_YAML_PATH

    with open(yaml_path) as f:
        return yaml.safe_load(f)
