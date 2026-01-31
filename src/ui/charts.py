"""Plotly chart builders for biomass and CO2 visualization.

Produces standalone go.Figure objects ready for st.plotly_chart().
Uses separate figures (NOT make_subplots) because add_vrect has known
reliability issues with subplots.

Do NOT wrap figure builders in @st.cache_data -- Plotly Figures have
serialization issues with Streamlit caching (RESEARCH.md Pitfall 3).
"""

from __future__ import annotations

import plotly.graph_objects as go

from src.models.parameters import CityClimate
from src.models.results import SimulationResult

# Season background band colors (green/earth theme from CONTEXT.md)
_SEASON_COLORS: dict[str, str] = {
    "dry": "rgba(255, 235, 180, 0.2)",      # warm sand
    "hot": "rgba(255, 200, 150, 0.2)",       # warm peach
    "monsoon": "rgba(180, 220, 255, 0.2)",   # light blue
    "custom": "rgba(220, 220, 220, 0.15)",   # neutral gray for user overrides
}

# Common layout settings shared by both charts
_COMMON_LAYOUT = dict(
    template="plotly_white",
    hovermode="x unified",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def _compute_season_bands(
    start_month: int, duration_days: int, climate: CityClimate
) -> list[dict]:
    """Compute contiguous season background bands for chart annotation.

    Maps each simulation day to its calendar month using the same 30-day
    approximation the simulation engine uses, looks up the season from
    climate data, and groups contiguous same-season days into bands.

    Args:
        start_month: Starting calendar month (1-12).
        duration_days: Total simulation days.
        climate: City climate with monthly season data.

    Returns:
        List of band dicts with keys: x0, x1, season, color.
    """
    if duration_days <= 0:
        return []

    bands: list[dict] = []
    prev_season: str | None = None
    band_start = 0

    for day in range(duration_days):
        month_index = (start_month - 1 + day // 30) % 12
        season = climate.months[month_index].season

        if season != prev_season:
            # Close previous band
            if prev_season is not None:
                bands.append({
                    "x0": band_start,
                    "x1": day,
                    "season": prev_season,
                    "color": _SEASON_COLORS.get(prev_season, _SEASON_COLORS["custom"]),
                })
            prev_season = season
            band_start = day

    # Close final band
    if prev_season is not None:
        bands.append({
            "x0": band_start,
            "x1": duration_days,
            "season": prev_season,
            "color": _SEASON_COLORS.get(prev_season, _SEASON_COLORS["custom"]),
        })

    return bands


def _add_harvest_markers(fig: go.Figure, harvest_days: tuple[int, ...]) -> None:
    """Add vertical dashed lines for harvest events and a legend entry.

    Args:
        fig: Plotly figure to annotate.
        harvest_days: Day indices where harvests occurred.
    """
    for day in harvest_days:
        fig.add_vline(
            x=day,
            line_dash="dash",
            line_color="rgba(139, 69, 19, 0.6)",
            line_width=1,
        )

    # Single invisible scatter trace for the harvest legend entry
    if harvest_days:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                name="Harvest",
                line=dict(dash="dash", color="rgba(139, 69, 19, 0.6)"),
            )
        )


def _add_season_bands(fig: go.Figure, bands: list[dict]) -> None:
    """Add season background color bands to the chart.

    Args:
        fig: Plotly figure to annotate.
        bands: Season band dicts from _compute_season_bands.
    """
    for band in bands:
        fig.add_vrect(
            x0=band["x0"],
            x1=band["x1"],
            fillcolor=band["color"],
            layer="below",
            line_width=0,
        )


def create_biomass_chart(
    result: SimulationResult, climate: CityClimate
) -> go.Figure:
    """Build interactive biomass concentration time-series chart.

    Includes biomass trace with area fill, season background bands,
    and harvest event markers. Returns a standalone go.Figure.

    Args:
        result: Completed simulation result.
        climate: City climate for season band computation.

    Returns:
        Plotly Figure ready for st.plotly_chart().
    """
    fig = go.Figure()

    # Main data trace: biomass concentration
    fig.add_trace(
        go.Scatter(
            x=list(result.time_days),
            y=list(result.biomass_concentration),
            name="Biomass",
            mode="lines",
            line=dict(color="#2E7D32", width=2),
            fill="tozeroy",
            fillcolor="rgba(46, 125, 50, 0.1)",
        )
    )

    # Season background bands
    bands = _compute_season_bands(result.start_month, result.duration_days, climate)
    _add_season_bands(fig, bands)

    # Harvest event markers
    _add_harvest_markers(fig, result.harvest_days)

    # Layout
    fig.update_layout(
        title="Biomass Concentration Over Time",
        xaxis_title="Day",
        yaxis_title="Biomass (g/L)",
        **_COMMON_LAYOUT,
    )

    return fig


def create_co2_chart(
    result: SimulationResult, climate: CityClimate
) -> go.Figure:
    """Build interactive cumulative CO2 capture chart.

    Includes cumulative CO2 trace with area fill, season background bands,
    and harvest event markers. Returns a standalone go.Figure.

    Args:
        result: Completed simulation result.
        climate: City climate for season band computation.

    Returns:
        Plotly Figure ready for st.plotly_chart().
    """
    fig = go.Figure()

    # Main data trace: cumulative CO2 captured
    fig.add_trace(
        go.Scatter(
            x=list(result.time_days),
            y=list(result.co2_captured_cumulative),
            name="Cumulative CO2",
            mode="lines",
            line=dict(color="#546E7A", width=2),
            fill="tozeroy",
            fillcolor="rgba(84, 110, 122, 0.1)",
        )
    )

    # Season background bands
    bands = _compute_season_bands(result.start_month, result.duration_days, climate)
    _add_season_bands(fig, bands)

    # Harvest event markers
    _add_harvest_markers(fig, result.harvest_days)

    # Layout
    fig.update_layout(
        title="Cumulative CO2 Captured",
        xaxis_title="Day",
        yaxis_title="CO2 Captured (g/m2)",
        **_COMMON_LAYOUT,
    )

    return fig
