"""Results display module for the AlgaeGrowth Simulator.

Renders simulation results in the Streamlit main content area:
summary metric cards, interactive charts, seasonal breakdown,
browsable daily data table, export buttons, conditional warnings,
and calculation methodology.
"""

import pandas as pd
import streamlit as st
from streamlit import column_config as cc

from src.models.parameters import CityClimate, SimulationConfig
from src.models.results import SimulationResult
from src.ui.charts import create_biomass_chart, create_co2_chart
from src.ui.export import build_export_filename, prepare_csv_string, prepare_json_string
from src.ui.methodology import display_methodology


def display_results(
    result: SimulationResult,
    climate: CityClimate,
    config: SimulationConfig,
) -> None:
    """Render simulation results in the main content area.

    Displays six sections:
    1. Summary Metrics -- four st.metric cards in a row
    1b. Interactive Charts -- biomass and CO2 stacked vertically
    2. Seasonal Breakdown -- three columns for dry/hot/monsoon
    3. Daily Values -- a browsable DataFrame
    3b. Data Export -- CSV and JSON download buttons
    4. Warnings -- conditional warning banners
    5. Calculation Methodology -- collapsible expander

    Args:
        result: A frozen SimulationResult from the simulation engine.
        climate: City climate data for chart season bands.
        config: Simulation configuration for export metadata.
    """
    # ------------------------------------------------------------------
    # Section 1: Summary Metrics
    # ------------------------------------------------------------------
    st.subheader("Simulation Results")

    col1, col2, col3, col4 = st.columns(4, border=True)

    with col1:
        st.metric("CO2 Captured", f"{result.total_co2_captured_tco2e:.4f} tCO2e")
    with col2:
        st.metric("Avg Productivity", f"{result.avg_daily_productivity:.1f} g/m2/d")
    with col3:
        st.metric("Harvests", str(result.harvest_count))
    with col4:
        st.metric("Duration", f"{result.duration_days} days")

    # ------------------------------------------------------------------
    # Section 1b: Interactive Charts
    # ------------------------------------------------------------------
    st.subheader("Growth Trajectory")

    biomass_fig = create_biomass_chart(result, climate)
    st.plotly_chart(biomass_fig, use_container_width=True)

    co2_fig = create_co2_chart(result, climate)
    st.plotly_chart(co2_fig, use_container_width=True)

    # ------------------------------------------------------------------
    # Section 2: Seasonal Breakdown
    # ------------------------------------------------------------------
    st.subheader("Seasonal Breakdown")

    season_names = ("Dry (Oct-Feb)", "Hot (Mar-May)", "Monsoon (Jun-Sep)")
    s_col1, s_col2, s_col3 = st.columns(3, border=True)

    for col, name, co2_kg, prod in zip(
        (s_col1, s_col2, s_col3),
        season_names,
        result.seasonal_co2,
        result.seasonal_productivity,
    ):
        with col:
            st.markdown(f"**{name}**")
            st.metric("CO2 Captured", f"{co2_kg:.4f} kg")
            st.metric("Avg Productivity", f"{prod:.1f} g/m2/d")

    # ------------------------------------------------------------------
    # Section 3: Daily Data Table
    # ------------------------------------------------------------------
    st.subheader("Daily Values")

    df = pd.DataFrame(
        {
            "Day": [int(d) for d in result.time_days],
            "Biomass (g/L)": list(result.biomass_concentration),
            "Growth Rate (1/d)": list(result.growth_rate_daily),
            "Productivity (g/m2/d)": list(result.productivity_areal),
            "CO2 Captured (kg)": list(result.co2_captured_daily),
            "Cumulative CO2 (g/m2)": list(result.co2_captured_cumulative),
        }
    )

    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "Day": cc.NumberColumn("Day", format="%d"),
            "Biomass (g/L)": cc.NumberColumn("Biomass (g/L)", format="%.3f"),
            "Growth Rate (1/d)": cc.NumberColumn(
                "Growth Rate (1/d)", format="%.4f"
            ),
            "Productivity (g/m2/d)": cc.NumberColumn(
                "Productivity (g/m2/d)", format="%.2f"
            ),
            "CO2 Captured (kg)": cc.NumberColumn(
                "CO2 Captured (kg)", format="%.4f"
            ),
            "Cumulative CO2 (g/m2)": cc.NumberColumn(
                "Cumulative CO2 (g/m2)", format="%.2f"
            ),
        },
    )

    # ------------------------------------------------------------------
    # Section 3b: Data Export
    # ------------------------------------------------------------------
    csv_data = prepare_csv_string(result, config)
    json_data = prepare_json_string(result, config)
    csv_filename = build_export_filename(result, config, "csv")
    json_filename = build_export_filename(result, config, "json")

    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv",
            on_click="ignore",
        )
    with exp_col2:
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name=json_filename,
            mime="application/json",
            on_click="ignore",
        )

    # ------------------------------------------------------------------
    # Section 4: Warnings (conditional)
    # ------------------------------------------------------------------
    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)

    # ------------------------------------------------------------------
    # Section 5: Calculation Methodology
    # ------------------------------------------------------------------
    display_methodology(result)
