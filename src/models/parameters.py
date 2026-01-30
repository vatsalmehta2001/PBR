"""Frozen dataclasses for microalgal growth simulation parameters.

All parameter containers are frozen (immutable) and hashable, enabling
safe use as Streamlit cache keys and preventing accidental mutation
during simulation runs.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GrowthParams:
    """Monod growth kinetics parameters for a single species."""

    mu_max: float
    """Maximum specific growth rate [1/d]."""

    Ks_co2: float
    """Half-saturation constant for dissolved CO2 [mg/L]."""

    I_opt: float
    """Optimal light intensity for Steele photoinhibition model [umol/m2/s]."""

    r_maintenance: float
    """Maintenance respiration rate [1/d]. Subtracted from gross growth."""

    discount_factor: float
    """Real-world discount factor (0-1). Accounts for lab-to-field yield gap.
    Typical value: 0.5 (40-60% range midpoint)."""


@dataclass(frozen=True)
class LightParams:
    """Beer-Lambert light attenuation parameters."""

    sigma_x: float
    """Biomass-specific light absorption coefficient [m2/g].
    Determines how strongly biomass attenuates light with depth."""

    background_turbidity: float
    """Non-biomass light extinction coefficient [1/m].
    Accounts for water, dissolved organics, and suspended particles."""


@dataclass(frozen=True)
class ReactorParams:
    """Physical reactor/pond geometry parameters."""

    depth: float
    """Pond or reactor depth [m]."""

    surface_area: float
    """Pond or reactor surface area [m2]."""


@dataclass(frozen=True)
class SpeciesParams:
    """Complete species parameter set with provenance.

    Aggregates growth kinetics, light attenuation, and carbon stoichiometry
    for a single microalgal species. Frozen and hashable for cache keying.
    """

    name: str
    """Species name (e.g., 'Chlorella vulgaris')."""

    growth: GrowthParams
    """Monod growth kinetics parameters."""

    light: LightParams
    """Beer-Lambert light attenuation parameters."""

    carbon_content: float
    """Fraction of biomass dry weight that is carbon [g_C/g_DW].
    Used to derive CO2 capture from biomass production."""

    co2_to_biomass_ratio: float
    """Mass of CO2 captured per unit biomass produced [g_CO2/g_DW].
    Derived as (M_CO2 / M_C) * carbon_content = (44/12) * carbon_content."""


@dataclass(frozen=True)
class ClimateParams:
    """Cardinal temperature parameters for the CTMI temperature response model.

    Defines the minimum, optimal, and maximum temperatures for microalgal
    growth. Frozen and hashable for cache keying.

    References:
        Rosso et al. (1993): CTMI original formulation.
        Bernard & Remond (2012): Validation for microalgae.
    """

    T_min: float
    """Minimum temperature for growth [C]. Growth is zero below this."""

    T_opt: float
    """Optimal temperature for maximum growth [C]. CTMI returns 1.0 here."""

    T_max: float
    """Maximum temperature for growth [C]. Growth is zero above this."""


@dataclass(frozen=True)
class MonthlyClimate:
    """Climate data for a single month at a specific location.

    Contains all environmental parameters needed for monthly growth
    simulation: temperature (day/night split), light, and precipitation.
    Frozen and hashable for cache keying.
    """

    season: str
    """Season classification ('dry', 'hot', or 'monsoon')."""

    temp_day: float
    """Average daytime high temperature [C]."""

    temp_night: float
    """Average nighttime low temperature [C]."""

    par: float
    """Average daytime photosynthetically active radiation [umol/m2/s]."""

    photoperiod: float
    """Average daylight hours [h]."""

    rainfall: float
    """Average monthly rainfall [mm]."""

    cloud_cover_fraction: float
    """Average cloud cover fraction [0-1]."""


@dataclass(frozen=True)
class CityClimate:
    """Complete city climate profile with 12 months of data.

    Aggregates location metadata, cardinal temperature parameters, and
    monthly climate data. Uses tuple for months to ensure hashability.
    Frozen and hashable for Streamlit cache keying.
    """

    city: str
    """City name."""

    country: str
    """Country name."""

    latitude: float
    """Latitude in decimal degrees [N positive]."""

    longitude: float
    """Longitude in decimal degrees [E positive]."""

    climate_params: ClimateParams
    """Cardinal temperature parameters for this city's target species."""

    months: tuple[MonthlyClimate, ...]
    """Twelve months of climate data (Jan-Dec). Tuple for hashability."""
