"""Results display module for the AlgaeGrowth Simulator.

Renders simulation results in the Streamlit main content area:
summary metric cards, seasonal breakdown, browsable daily data table,
and conditional warnings.
"""

import pandas as pd
import streamlit as st
from streamlit import column_config as cc

from src.models.results import SimulationResult


def display_results(result: SimulationResult) -> None:
    """Render simulation results in the main content area.

    Displays four sections:
    1. Summary Metrics -- four st.metric cards in a row
    2. Seasonal Breakdown -- three columns for dry/hot/monsoon
    3. Daily Values -- a browsable DataFrame
    4. Warnings -- conditional warning banners

    Args:
        result: A frozen SimulationResult from the simulation engine.
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
    # Section 4: Warnings (conditional)
    # ------------------------------------------------------------------
    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)
