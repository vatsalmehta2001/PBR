"""Sidebar input components for the AlgaeGrowth Simulator.

Renders three collapsible sections in the Streamlit sidebar:
Climate Settings, Pond Parameters, and Simulation Controls.
Returns a dict of all collected input values plus validation state.
"""

import streamlit as st

from src.models.parameters import CityClimate
from src.ui.defaults import (
    DEFAULT_CO2_CONCENTRATION,
    DEFAULT_DEPTH,
    DEFAULT_HARVEST_THRESHOLD,
    DEFAULT_INITIAL_BIOMASS,
    DEFAULT_SURFACE_AREA,
    DURATION_PRESETS,
    MONTH_NAMES,
    build_overridden_climate,
    collect_validation_errors,
)


def render_sidebar(default_climate: CityClimate) -> dict:
    """Render the complete simulation parameter sidebar.

    Creates three collapsible sections for climate, pond, and simulation
    parameters. Validates inputs and returns all values in a dict.

    Args:
        default_climate: The default Surat CityClimate profile. Used for
            read-only display when override is off, and as the base for
            building overridden climate when override is on.

    Returns:
        Dict with keys:
            surface_area (float): Pond surface area [m2].
            depth (float): Pond depth [m].
            initial_biomass (float): Initial biomass concentration [g/L].
            harvest_threshold (float): Harvest threshold [g/L].
            co2_concentration (float): Dissolved CO2 [mg/L].
            duration_days (int): Simulation duration [days].
            start_month (int): Starting month [1-12].
            climate_overridden (bool): Whether climate override is active.
            override_climate (CityClimate | None): Overridden climate, or None.
            validation_errors (list[str]): List of hard errors (empty = valid).
            run_clicked (bool): Whether the Run button was clicked.
    """
    override_climate: CityClimate | None = None

    with st.sidebar:
        st.header("Simulation Parameters")

        # ---------------------------------------------------------------
        # Section 1: Climate Settings (collapsed by default)
        # ---------------------------------------------------------------
        with st.expander("Climate Settings", expanded=False):
            climate_overridden = st.toggle(
                "Override Surat defaults",
                key="climate_override",
            )

            if not climate_overridden:
                # Show read-only summary of Surat climate
                months = default_climate.months
                temp_day_range = (
                    min(m.temp_day for m in months),
                    max(m.temp_day for m in months),
                )
                temp_night_range = (
                    min(m.temp_night for m in months),
                    max(m.temp_night for m in months),
                )
                par_range = (
                    min(m.par for m in months),
                    max(m.par for m in months),
                )
                st.caption(
                    f"{default_climate.city}, {default_climate.country}\n\n"
                    f"Day temp: {temp_day_range[0]:.0f}"
                    f"-{temp_day_range[1]:.0f} C\n\n"
                    f"Night temp: {temp_night_range[0]:.0f}"
                    f"-{temp_night_range[1]:.0f} C\n\n"
                    f"PAR: {par_range[0]:.0f}"
                    f"-{par_range[1]:.0f} umol/m2/s"
                )
            else:
                # Editable override inputs
                temp_day = st.number_input(
                    "Daytime temperature (C)",
                    min_value=0.0,
                    max_value=55.0,
                    value=32.0,
                    step=0.5,
                    format="%.1f",
                    key="climate_temp_day",
                )
                temp_night = st.number_input(
                    "Nighttime temperature (C)",
                    min_value=0.0,
                    max_value=40.0,
                    value=22.0,
                    step=0.5,
                    format="%.1f",
                    key="climate_temp_night",
                )
                par = st.number_input(
                    "PAR (umol/m2/s)",
                    min_value=50.0,
                    max_value=2500.0,
                    value=400.0,
                    step=10.0,
                    format="%.0f",
                    key="climate_par",
                )
                photoperiod = st.number_input(
                    "Photoperiod (hours)",
                    min_value=6.0,
                    max_value=18.0,
                    value=12.0,
                    step=0.5,
                    format="%.1f",
                    key="climate_photoperiod",
                )
                override_climate = build_overridden_climate(
                    default_climate, temp_day, temp_night, par, photoperiod
                )

        # ---------------------------------------------------------------
        # Section 2: Pond Parameters (expanded by default)
        # ---------------------------------------------------------------
        with st.expander("Pond Parameters", expanded=True):
            surface_area = st.number_input(
                "Surface area (m2)",
                min_value=1.0,
                max_value=10000.0,
                value=DEFAULT_SURFACE_AREA,
                step=10.0,
                format="%.1f",
                key="pond_surface_area",
            )
            depth = st.number_input(
                "Depth (m)",
                min_value=0.05,
                max_value=2.0,
                value=DEFAULT_DEPTH,
                step=0.05,
                format="%.2f",
                key="pond_depth",
            )
            if depth > 0.5:
                st.warning(
                    "Depth >0.5m may cause light limitation in dense cultures"
                )

        # ---------------------------------------------------------------
        # Section 3: Simulation Controls (expanded by default)
        # ---------------------------------------------------------------
        with st.expander("Simulation Controls", expanded=True):
            start_month_name = st.selectbox(
                "Start month",
                options=MONTH_NAMES,
                index=0,
                key="sim_start_month",
            )
            start_month = MONTH_NAMES.index(start_month_name) + 1

            preset_label = st.selectbox(
                "Duration preset",
                options=list(DURATION_PRESETS.keys()),
                index=4,
                key="sim_duration_preset",
            )
            preset_value = DURATION_PRESETS[preset_label]

            if preset_value is None:
                duration_days = st.number_input(
                    "Duration (days)",
                    min_value=1,
                    max_value=365,
                    value=365,
                    step=1,
                    key="sim_duration_custom",
                )
            else:
                duration_days = preset_value
                st.caption(f"{duration_days} days")

            initial_biomass = st.number_input(
                "Initial biomass (g/L)",
                min_value=0.01,
                max_value=5.0,
                value=DEFAULT_INITIAL_BIOMASS,
                step=0.1,
                format="%.2f",
                key="sim_initial_biomass",
            )
            harvest_threshold = st.number_input(
                "Harvest threshold (g/L)",
                min_value=0.5,
                max_value=10.0,
                value=DEFAULT_HARVEST_THRESHOLD,
                step=0.5,
                format="%.1f",
                key="sim_harvest_threshold",
            )
            co2_concentration = st.number_input(
                "CO2 concentration (mg/L)",
                min_value=0.0,
                max_value=50.0,
                value=DEFAULT_CO2_CONCENTRATION,
                step=0.5,
                format="%.1f",
                key="sim_co2_concentration",
            )

        # ---------------------------------------------------------------
        # Validation and Run button
        # ---------------------------------------------------------------
        validation_errors = collect_validation_errors(
            surface_area, depth, initial_biomass, co2_concentration
        )

        if validation_errors:
            for error in validation_errors:
                st.error(error)

        run_clicked = st.button(
            "Run Simulation",
            type="primary",
            disabled=bool(validation_errors),
            use_container_width=True,
            key="run_button",
        )

    return {
        "surface_area": surface_area,
        "depth": depth,
        "initial_biomass": initial_biomass,
        "harvest_threshold": harvest_threshold,
        "co2_concentration": co2_concentration,
        "duration_days": duration_days,
        "start_month": start_month,
        "climate_overridden": climate_overridden,
        "override_climate": override_climate,
        "validation_errors": validation_errors,
        "run_clicked": run_clicked,
    }
