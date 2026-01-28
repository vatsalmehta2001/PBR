"""Monod growth kinetics with Steele photoinhibition for microalgal simulation.

Implements three core pure functions plus helper functions for computing
microalgal specific growth rate, areal productivity, and productivity
validation. The Steele photoinhibition model is essential for outdoor
cultivation under intense solar radiation (e.g., Surat, India) where
light intensities far exceed the optimal for Chlorella vulgaris.

The combined growth model uses multiplicative limiting factors:
    mu = max(mu_max * f_light(I) * f_co2(CO2) * discount_factor - r_maintenance, 0)

where:
    - f_light: Steele (1962) photoinhibition response
    - f_co2: Monod saturation kinetics for dissolved CO2
    - discount_factor: Lab-to-field yield gap correction (40-60%)
    - r_maintenance: Maintenance respiration loss

Functions are pure (no side effects, no state mutation) and take raw
float arguments plus frozen GrowthParams dataclasses.

References:
    Steele (1962): Photoinhibition model f(I) = (I/I_opt) * exp(1 - I/I_opt)
    Schediwy et al. (2019): Chlorella vulgaris kinetic parameters
    Razzak et al. (2024): CO2 capture and photoinhibition review
    CONTEXT.md: 6-10 g/m2/day conservative productivity target
"""

import numpy as np

from src.models.parameters import GrowthParams, LightParams


def steele_light_response(I: float, I_opt: float) -> float:
    """Compute Steele (1962) photoinhibition light response.

    Returns a growth fraction [0, 1] that peaks at exactly 1.0 when
    I = I_opt and declines for both lower and higher irradiances.
    The decline above I_opt models photoinhibition -- damage to
    photosynthetic apparatus under excess light.

    Formula:
        f(I) = (I / I_opt) * exp(1 - I / I_opt)

    Args:
        I: Irradiance at the culture [umol/m2/s].
        I_opt: Optimal irradiance for growth [umol/m2/s].

    Returns:
        Light response fraction in [0, 1]. Returns 0.0 for I <= 0.

    References:
        Steele (1962): Environmental control of photosynthesis in the sea.
        Razzak et al. (2024), citing Metsoviti et al.: I_opt = 80 umol/m2/s
        for Chlorella vulgaris.
    """
    if I <= 0.0:
        return 0.0

    ratio = I / I_opt
    return float(ratio * np.exp(1.0 - ratio))


def monod_co2_response(co2: float, Ks_co2: float) -> float:
    """Compute Monod saturation kinetics for dissolved CO2.

    Returns a growth fraction [0, 1] that is 0.5 when CO2 = Ks_co2
    (half-saturation) and approaches 1.0 at high CO2 concentrations.

    Formula:
        f(CO2) = CO2 / (Ks_co2 + CO2)

    Args:
        co2: Dissolved CO2 concentration [mg/L].
        Ks_co2: Half-saturation constant for CO2 [mg/L].

    Returns:
        CO2 response fraction in [0, 1]. Returns 0.0 for co2 <= 0.

    References:
        Schediwy et al. (2019), Table 2: Ks_co2 = 0.5 mg/L for C. vulgaris.
    """
    if co2 <= 0.0:
        return 0.0

    return co2 / (Ks_co2 + co2)


def specific_growth_rate(I_avg: float, co2: float, params: GrowthParams) -> float:
    """Compute specific growth rate with multiplicative limiting factors.

    Combines Steele photoinhibition and Monod CO2 response with a
    real-world discount factor and maintenance respiration subtraction.
    Result is clamped to >= 0 (no negative growth).

    Formula:
        mu = max(mu_max * f_light * f_co2 * discount_factor - r_maintenance, 0.0)

    Args:
        I_avg: Average irradiance experienced by the culture [umol/m2/s].
        co2: Dissolved CO2 concentration [mg/L].
        params: GrowthParams dataclass with mu_max, Ks_co2, I_opt,
                r_maintenance, and discount_factor.

    Returns:
        Specific growth rate [1/d], always >= 0.

    References:
        Combined model per Schediwy et al. (2019) approach with
        Steele light response and Monod CO2 kinetics.
        Discount factor: 40-60% lab-to-field yield gap (CONTEXT.md).
    """
    f_light = steele_light_response(I_avg, params.I_opt)
    f_co2 = monod_co2_response(co2, params.Ks_co2)

    gross = params.mu_max * f_light * f_co2 * params.discount_factor
    net = gross - params.r_maintenance

    return max(net, 0.0)


def compute_areal_productivity(mu: float, biomass_conc: float, depth: float) -> float:
    """Convert volumetric growth rate to areal productivity.

    Areal productivity represents biomass production per unit pond surface
    area per day -- the key metric for comparing cultivation systems and
    estimating CO2 capture capacity.

    Formula:
        P = mu * X * D * 1000 [g/m2/day]

    where X is in g/L, D in m, and 1000 converts L/m3.

    Args:
        mu: Specific growth rate [1/d].
        biomass_conc: Biomass concentration X [g/L].
        depth: Pond depth D [m].

    Returns:
        Areal productivity [g/m2/day].
    """
    return mu * biomass_conc * depth * 1000.0


def depth_averaged_growth_rate(
    I0: float,
    co2: float,
    biomass_conc: float,
    depth: float,
    growth_params: GrowthParams,
    light_params: LightParams,
    n_layers: int = 20,
) -> float:
    """Compute depth-averaged specific growth rate via numerical layer integration.

    Divides the pond into n_layers and computes the specific growth rate
    at each layer midpoint using the local irradiance from Beer-Lambert
    attenuation. This properly accounts for the nonlinear Steele
    photoinhibition response -- using a single depth-averaged irradiance
    would misrepresent growth because the Steele function is nonlinear
    (Jensen's inequality).

    The Beer-Lambert calculation is inlined here to keep growth.py
    minimally coupled (no dependency on light.py).

    Args:
        I0: Surface irradiance [umol/m2/s].
        co2: Dissolved CO2 concentration [mg/L].
        biomass_conc: Biomass concentration X [g/L].
        depth: Pond depth D [m].
        growth_params: GrowthParams dataclass.
        light_params: LightParams dataclass (sigma_x, background_turbidity).
        n_layers: Number of depth layers for numerical integration (default 20).

    Returns:
        Depth-averaged specific growth rate [1/d].

    References:
        Numerical integration approach per RESEARCH.md depth_averaged_growth_numerical.
        Beer-Lambert: I(z) = I0 * exp(-(sigma_x * X + k_bg) * z)
    """
    if I0 <= 0.0 or depth <= 0.0:
        return 0.0

    # Total extinction coefficient
    K = light_params.sigma_x * biomass_conc + light_params.background_turbidity

    # Layer thickness
    dz = depth / n_layers

    total_mu = 0.0
    for i in range(n_layers):
        # Midpoint depth of this layer
        z_mid = (i + 0.5) * dz
        # Beer-Lambert attenuation at layer midpoint (inlined)
        I_z = I0 * float(np.exp(-K * z_mid))
        # Growth rate at this layer
        mu_z = specific_growth_rate(I_z, co2, growth_params)
        total_mu += mu_z

    return total_mu / n_layers


def check_productivity_warnings(productivity: float) -> list[str]:
    """Check areal productivity against field-realistic bounds.

    Returns warning messages when computed productivity exceeds typical
    field values (>10 g/m2/day). The 6-10 g/m2/day range is the
    conservative target for defensible carbon credit estimation.

    Args:
        productivity: Computed areal productivity [g/m2/day].

    Returns:
        List of warning strings. Empty if productivity is within bounds.

    References:
        CONTEXT.md: "If the model says >10, we flag it."
    """
    warnings: list[str] = []

    if productivity > 10.0:
        warnings.append(
            f"Output exceeds typical field values ({productivity} g/m2/day > 10 g/m2/day)"
        )

    return warnings
