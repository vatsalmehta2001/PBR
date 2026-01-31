"""Methodology display module for the AlgaeGrowth Simulator.

Renders a collapsible explanation of the CO2 calculation methodology
including plain English summary, LaTeX equations (toggle), dynamic
parameter table with DOI-linked sources, key model assumptions,
factors not modeled (toggle), and full references.

Uses only standard KaTeX-compatible LaTeX notation per Streamlit's
built-in math rendering engine. Citation data loaded dynamically
from YAML configs (single source of truth).
"""

import streamlit as st

from src.config.loader import get_parameter_citations
from src.climate.loader import get_climate_citations
from src.models.results import SimulationResult


# ---------------------------------------------------------------------------
# Reference database: full citation strings keyed by DOI
# (YAML source fields are abbreviated; these provide complete references)
# ---------------------------------------------------------------------------

_REFERENCE_DB: dict[str, str] = {
    "10.1002/elsc.201900107": (
        "Schediwy, K., Giraldo, L., & Friehs, K. (2019). "
        "Model-based analysis of mixotrophic *Chlorella vulgaris* bioprocesses. "
        "*Engineering in Life Sciences*, 19(10), 700-710."
    ),
    "10.1016/j.gce.2023.10.004": (
        "Razzak, S.A., Mofijur, M., Arafat, K.M.Y., et al. (2024). "
        "Microalgae-based carbon capture and sequestration. "
        "*Green Chemical Engineering*, 5(2), 135-149."
    ),
    "10.1016/j.cep.2009.03.006": (
        "Converti, A., Casazza, A.A., Ortiz, E.Y., et al. (2009). "
        "Effect of temperature and nitrogen concentration on the growth "
        "and lipid content of *Nannochloropsis oculata* and *Chlorella vulgaris*. "
        "*Chemical Engineering and Processing*, 48(6), 1146-1151."
    ),
    "10.1016/j.biortech.2012.07.022": (
        "Bernard, O. & Remond, B. (2012). "
        "Validation of a simple model accounting for light and temperature "
        "effect on microalgal growth. "
        "*Bioresource Technology*, 123, 520-527."
    ),
    "10.1006/jtbi.1993.1099": (
        "Rosso, L., Lobry, J.R., & Flandrois, J.P. (1993). "
        "An unexpected correlation between cardinal temperatures of "
        "microbial growth. "
        "*Journal of Theoretical Biology*, 162(4), 447-463."
    ),
}


# ---------------------------------------------------------------------------
# Display name mapping for YAML parameter keys
# ---------------------------------------------------------------------------

_PARAM_DISPLAY_NAMES: dict[str, str] = {
    "mu_max": "Max growth rate (mu_max)",
    "Ks_co2": "CO2 half-saturation (Ks)",
    "I_opt": "Optimal irradiance (I_opt)",
    "r_maintenance": "Maintenance respiration",
    "discount_factor": "Lab-to-field discount",
    "sigma_x": "Light absorption (sigma_x)",
    "background_turbidity": "Background turbidity",
    "carbon_content": "Carbon content",
    "co2_to_biomass_ratio": "CO2:biomass ratio",
}

_TEMP_DISPLAY_NAMES: dict[str, str] = {
    "T_min": "Minimum temperature (T_min)",
    "T_opt": "Optimal temperature (T_opt)",
    "T_max": "Maximum temperature (T_max)",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doi_link(source_text: str, doi: str | None) -> str:
    """Format a source field as a DOI link if available, plain text otherwise.

    Extracts the short author citation (e.g. 'Schediwy et al. (2019)')
    from the source text for the link label.
    """
    if doi is None or doi == "null":
        return source_text

    # Extract author citation: take text up to first semicolon or end
    label = source_text.split(";")[0].split(",")[0].strip()
    # If the label doesn't contain a year in parens, use raw source
    if "(" not in label:
        label = source_text.split(";")[0].strip()

    return f"[{label}](https://doi.org/{doi})"


def _get_param_value(sp, group: str, key: str):
    """Get the actual simulation parameter value from the result SpeciesParams."""
    if group == "growth":
        return getattr(sp.growth, key, None)
    elif group == "light":
        return getattr(sp.light, key, None)
    elif group == "carbon":
        if key == "carbon_content":
            return sp.carbon_content
        elif key == "co2_to_biomass_ratio":
            return sp.co2_to_biomass_ratio
    return None


def _collect_unique_dois(species_data: dict, climate_data: dict) -> list[tuple[str, str]]:
    """Collect unique DOIs from both YAML configs.

    Returns a list of (doi, full_citation) tuples in a stable order,
    plus any non-DOI web sources appended at the end.
    """
    seen_dois: dict[str, str] = {}
    has_web_sources = False

    # Scan species params
    for group_name in ("growth", "light", "carbon"):
        group = species_data.get(group_name, {})
        for _key, entry in group.items():
            if isinstance(entry, dict):
                doi = entry.get("doi")
                if doi and doi not in seen_dois:
                    seen_dois[doi] = _REFERENCE_DB.get(doi, f"DOI: {doi}")

    # Scan climate temperature_params
    temp_params = climate_data.get("temperature_params", {})
    for _key, entry in temp_params.items():
        if isinstance(entry, dict):
            doi = entry.get("doi")
            if doi and doi not in seen_dois:
                seen_dois[doi] = _REFERENCE_DB.get(doi, f"DOI: {doi}")
            source = entry.get("source", "")
            # Check for Bernard & Remond in source text (secondary ref)
            if "Bernard" in source and "10.1016/j.biortech.2012.07.022" not in seen_dois:
                seen_dois["10.1016/j.biortech.2012.07.022"] = _REFERENCE_DB[
                    "10.1016/j.biortech.2012.07.022"
                ]

    # Rosso et al. is used in the CTMI model (referenced in equations)
    if "10.1006/jtbi.1993.1099" not in seen_dois:
        seen_dois["10.1006/jtbi.1993.1099"] = _REFERENCE_DB["10.1006/jtbi.1993.1099"]

    # Check for web sources in monthly climate data
    months = climate_data.get("months", {})
    if months:
        has_web_sources = True

    results = [(doi, citation) for doi, citation in seen_dois.items()]

    return results, has_web_sources


# ---------------------------------------------------------------------------
# Main display function
# ---------------------------------------------------------------------------

def display_methodology(result: SimulationResult) -> None:
    """Render calculation methodology in a Streamlit expander.

    Displays six sections:
    1. Plain English summary of the CO2 capture calculation
    2. LaTeX equations (behind a checkbox toggle)
    3. Enhanced parameter table with DOI-linked sources
    4. Key model assumptions with quantitative impact
    5. Factors not modeled (behind a checkbox toggle)
    6. Full references with DOI links

    Args:
        result: Simulation result containing parameters_used for the
                dynamic parameter table.
    """
    with st.expander("Calculation Methodology", expanded=False):
        # --------------------------------------------------------------
        # Section 1: Plain English Summary
        # --------------------------------------------------------------
        st.markdown("""
**How CO2 capture is calculated:**

1. **Growth modeling**: Daily biomass growth is computed using Monod kinetics
   with light-dependent (Beer-Lambert) and temperature-dependent (CTMI) modifiers.
2. **CO2 conversion**: Biomass produced each day is converted to CO2 captured
   using the species-specific carbon content and CO2-to-biomass ratio.
3. **Conservative approach**: Only positive net growth contributes to CO2 capture.
   Maintenance respiration and a lab-to-field discount factor are applied.
4. **Harvest cycling**: When biomass exceeds the harvest threshold, it is reset
   to the initial concentration, simulating periodic harvesting.
""")

        # --------------------------------------------------------------
        # Section 2: Equations (toggle)
        # --------------------------------------------------------------
        show_equations = st.checkbox("Show equations", key="show_equations")

        if show_equations:
            st.markdown("**Monod growth with modifiers:**")
            st.latex(
                r"\mu = \mu_{max} \cdot \frac{S}{K_s + S}"
                r" \cdot f(I) \cdot f(T) \cdot \delta"
            )

            st.markdown("**Daily CO2 conversion:**")
            st.latex(
                r"CO_2 = \Delta B \cdot V \cdot r_{CO_2:bio}"
                r"\quad \text{where} \quad"
                r"r_{CO_2:bio} = \frac{44}{12} \cdot C_{content}"
            )

            st.markdown("**Total tonnes CO2 equivalent:**")
            st.latex(
                r"tCO_2e = \frac{\sum CO_{2,daily}}{1000}"
            )

        # --------------------------------------------------------------
        # Section 3: Enhanced Parameter Table with Sources
        # --------------------------------------------------------------
        st.markdown("**Parameters Used**")

        # Load citation data from YAML configs
        species_data = get_parameter_citations()
        climate_data = get_climate_citations()

        sp = result.parameters_used

        # Build species parameter table
        param_rows = []
        for group_name in ("growth", "light", "carbon"):
            group = species_data.get(group_name, {})
            for key, entry in group.items():
                if not isinstance(entry, dict) or "value" not in entry:
                    continue
                display_name = _PARAM_DISPLAY_NAMES.get(key, key)
                value = _get_param_value(sp, group_name, key)
                if value is None:
                    value = entry["value"]
                unit = entry.get("unit", "")
                source_text = entry.get("source", "")
                doi = entry.get("doi")
                source_link = _doi_link(source_text, doi)
                param_rows.append(
                    f"| {display_name} | {value} {unit} | {source_link} |"
                )

        species_table = (
            "| Parameter | Value | Source |\n"
            "|-----------|-------|--------|\n"
            + "\n".join(param_rows)
        )
        st.markdown(species_table, unsafe_allow_html=True)

        # Build temperature parameter table
        st.markdown("**Temperature Parameters**")
        temp_params = climate_data.get("temperature_params", {})
        temp_rows = []
        for key in ("T_min", "T_opt", "T_max"):
            entry = temp_params.get(key, {})
            if not isinstance(entry, dict):
                continue
            display_name = _TEMP_DISPLAY_NAMES.get(key, key)
            value = entry.get("value", "")
            unit = entry.get("unit", "")
            source_text = entry.get("source", "")
            doi = entry.get("doi")
            source_link = _doi_link(source_text, doi)
            temp_rows.append(
                f"| {display_name} | {value} {unit} | {source_link} |"
            )

        temp_table = (
            "| Parameter | Value | Source |\n"
            "|-----------|-------|--------|\n"
            + "\n".join(temp_rows)
        )
        st.markdown(temp_table, unsafe_allow_html=True)

        # --------------------------------------------------------------
        # Section 4: Key Model Assumptions
        # --------------------------------------------------------------
        st.markdown("**Key Model Assumptions**")

        assumptions_table = (
            "| Assumption | Impact | Source |\n"
            "|-----------|--------|--------|\n"
            "| Lab-to-field discount: 0.5x | Reduces productivity by 50% "
            "| [Schediwy et al. (2019)](https://doi.org/10.1002/elsc.201900107) |\n"
            "| Forward Euler stepping (1-day) | ~2-5% deviation vs. higher-order "
            "| Standard numerical methods |\n"
            "| Constant CO2 at user-set level | Overestimates if supply is intermittent "
            "| Model simplification |\n"
            "| Monthly climate averages | +/-10-15% vs. daily weather data "
            "| Acceptable for annual planning |\n"
            "| Single temperature per day/night | Misses within-day dynamics "
            "| Standard in monthly models |\n"
            "| Maintenance respiration = 0.01/d | Assumed value "
            "| General microalgae literature |\n"
            "| Background turbidity = 0.5/m | Assumed value "
            "| Open pond literature estimate |"
        )
        st.markdown(assumptions_table, unsafe_allow_html=True)

        # --------------------------------------------------------------
        # Section 5: Factors Not Modeled (toggle)
        # --------------------------------------------------------------
        show_not_modeled = st.checkbox(
            "Show factors not modeled", key="show_not_modeled"
        )

        if show_not_modeled:
            not_modeled_table = (
                "| Factor | Potential Impact | Why Not Modeled |\n"
                "|--------|-----------------|------------------|\n"
                "| Nutrient depletion (N, P) "
                "| Could reduce growth 50-100% when depleted "
                "| Assumes continuous nutrient supply |\n"
                "| Culture contamination "
                "| Catastrophic (total loss) "
                "| Stochastic event; unpredictable |\n"
                "| Mixing energy / power input "
                "| Affects net energy balance "
                "| Focus is on CO2 capture, not energy |\n"
                "| Evaporation and water balance "
                "| Concentrates salts over time "
                "| Secondary effect with makeup water |\n"
                "| pH dynamics "
                "| Affects CO2 solubility "
                "| Assumes pH control via CO2 injection |\n"
                "| Biofilm and wall growth "
                "| Reduces light 10-30% "
                "| Site-specific; unpredictable |\n"
                "| Genetic drift / strain adaptation "
                "| Long-term growth shift "
                "| Multi-year timescale only |\n"
                "| Downstream processing losses "
                "| 10-30% biomass loss "
                "| Focus is on in-pond CO2 capture |\n"
                "| Daily weather variability "
                "| Smoothed by monthly averages "
                "| Acceptable for annual estimates |\n"
                "| CO2 supply interruptions "
                "| Drops growth rate to near-zero "
                "| Assumes continuous injection |\n"
                "| Multi-species competition "
                "| Slower growth than monoculture "
                "| Assumes maintained monoculture |"
            )
            st.markdown(not_modeled_table, unsafe_allow_html=True)

        # --------------------------------------------------------------
        # Section 6: Full References
        # --------------------------------------------------------------
        st.markdown("**References**")

        ref_list, has_web_sources = _collect_unique_dois(
            species_data, climate_data
        )

        ref_lines = []
        for i, (doi, citation) in enumerate(ref_list, start=1):
            ref_lines.append(
                f"{i}. {citation} "
                f"[DOI](https://doi.org/{doi})"
            )

        if has_web_sources:
            ref_lines.append(
                f"{len(ref_list) + 1}. Weather Atlas / WeatherSpark / "
                f"ClimatesToTravel -- Surat climate averages (1981-2010)"
            )

        st.markdown("\n".join(ref_lines))
