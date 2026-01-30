"""YAML config loader with Pydantic validation for city climate profiles.

Loads city climate data from YAML files that include per-parameter
citations (value + unit + source + note). Validates ranges through Pydantic,
then returns frozen dataclasses for simulation consumption.

Mirrors the pattern established in src/config/loader.py for species parameters.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from src.config.loader import _extract_values
from src.models.parameters import CityClimate, ClimateParams, MonthlyClimate


# ---------------------------------------------------------------------------
# Pydantic validation models (range checking only)
# ---------------------------------------------------------------------------

class MonthlyClimateValidator(BaseModel):
    """Validates a single month of climate data."""

    season: str
    temp_day: float = Field(ge=-10.0, le=55.0)
    temp_night: float = Field(ge=-10.0, le=45.0)
    par: float = Field(ge=0.0, le=2500.0)
    photoperiod: float = Field(ge=0.0, le=24.0)
    rainfall: float = Field(ge=0.0, le=2000.0)
    cloud_cover_fraction: float = Field(ge=0.0, le=1.0)


class ClimateProfileValidator(BaseModel):
    """Validates a complete city climate profile."""

    city: str
    country: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    T_min: float = Field(ge=-10.0, le=20.0)
    T_opt: float = Field(ge=15.0, le=40.0)
    T_max: float = Field(ge=25.0, le=55.0)
    months: dict[str, MonthlyClimateValidator]


# ---------------------------------------------------------------------------
# Month ordering (Jan-Dec) for consistent tuple construction
# ---------------------------------------------------------------------------

_MONTH_ORDER = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFAULT_YAML_PATH = Path(__file__).parent / "surat.yaml"


def load_city_climate(path: str | Path | None = None) -> CityClimate:
    """Load and validate a city climate profile from a YAML config file.

    Args:
        path: Path to a city climate YAML file. If None, uses the bundled
              default (Surat, India) config.

    Returns:
        A frozen CityClimate dataclass with validated parameter values.
        Months are ordered January through December as a tuple.

    Raises:
        pydantic.ValidationError: If any parameter is outside its valid range.
        FileNotFoundError: If the specified YAML file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    yaml_path = Path(path) if path is not None else _DEFAULT_YAML_PATH

    with open(yaml_path) as f:
        raw_data = yaml.safe_load(f)

    # Extract numeric values from nested value/unit/source structure
    temp_params = _extract_values(raw_data["temperature_params"])

    months_raw: dict[str, Any] = raw_data["months"]
    months_extracted: dict[str, dict[str, Any]] = {}
    for month_name, month_data in months_raw.items():
        months_extracted[month_name] = _extract_values(month_data)

    # Build flat structure for Pydantic validation
    flat_data = {
        "city": raw_data["city"],
        "country": raw_data["country"],
        "latitude": raw_data["latitude"],
        "longitude": raw_data["longitude"],
        "T_min": temp_params["T_min"],
        "T_opt": temp_params["T_opt"],
        "T_max": temp_params["T_max"],
        "months": months_extracted,
    }

    # Validate through Pydantic
    validated = ClimateProfileValidator(**flat_data)

    # Build frozen dataclasses (not Pydantic models)
    climate_params = ClimateParams(
        T_min=validated.T_min,
        T_opt=validated.T_opt,
        T_max=validated.T_max,
    )

    monthly_climate_list: list[MonthlyClimate] = []
    for month_name in _MONTH_ORDER:
        month_val = validated.months[month_name]
        monthly_climate_list.append(
            MonthlyClimate(
                season=month_val.season,
                temp_day=month_val.temp_day,
                temp_night=month_val.temp_night,
                par=month_val.par,
                photoperiod=month_val.photoperiod,
                rainfall=month_val.rainfall,
                cloud_cover_fraction=month_val.cloud_cover_fraction,
            )
        )

    return CityClimate(
        city=validated.city,
        country=validated.country,
        latitude=validated.latitude,
        longitude=validated.longitude,
        climate_params=climate_params,
        months=tuple(monthly_climate_list),
    )


def get_climate_citations(path: str | Path | None = None) -> dict:
    """Load and return the full YAML data including citations.

    Returns the raw YAML structure with value, unit, source, and note
    for each parameter. Useful for transparency display in the UI.

    Args:
        path: Path to a city climate YAML file. If None, uses the bundled
              default config.

    Returns:
        Dictionary with the complete YAML structure including citations.
    """
    yaml_path = Path(path) if path is not None else _DEFAULT_YAML_PATH

    with open(yaml_path) as f:
        return yaml.safe_load(f)
