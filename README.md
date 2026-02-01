# AlgaeGrowth Simulator

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.53+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/tests-172_passing-2E7D32)](#testing)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Peer-reviewed microalgal growth simulation for defensible CO2 capture estimation under Surat, India's tropical climate.**

## What It Does

Estimates CO2 captured by open-pond *Chlorella vulgaris* cultivation using Monod growth kinetics, Steele photoinhibition, and CTMI temperature response — all with DOI-cited parameters. Designed to produce defensible numbers that carbon credit verification bodies (Verra, Gold Standard, India CCTS) can evaluate.

## Key Features

- **Monod + Steele growth model** with 20-layer Beer-Lambert depth integration
- **CTMI cardinal temperature model** with day/night split for Surat's 8-40 C range
- **Conservative 50% lab-to-field discount** — outputs 6-10 g/m2/day, not lab-ideal 20+
- **Three-season Surat climate** — Dry (Oct-Feb), Hot (Mar-May), Monsoon (Jun-Sep) with monthly PAR, temperature, and cloud cover from WeatherSpark data
- **CO2 accounting** — species-specific 1.83 g CO2/g biomass conversion factor (Schediwy et al., 2019)
- **Harvest cycling** — automatic biomass reset at configurable threshold with event tracking
- **Interactive Plotly charts** with season background bands and harvest markers
- **CSV/JSON export** with embedded methodology disclaimers for verification workflows
- **Full transparency** — every parameter links to its DOI source; equations, assumptions, and "not modeled" factors are visible in-app

## Architecture

<p align="center">
  <img src="docs/diagrams/architecture.svg" alt="System Architecture" width="100%">
</p>

## Simulation Flow

<p align="center">
  <img src="docs/diagrams/simulation-flow.svg" alt="Simulation Flow" width="700">
</p>

## Growth Model

<p align="center">
  <img src="docs/diagrams/growth-model.svg" alt="Growth Model" width="100%">
</p>

## Demo

<p align="center">
  <img src="docs/Streamlit UI.png" alt="Growth Model" width="100%">
</p>

## Quick Start

```bash
# Clone
git clone https://github.com/vatsalmehta2001/PBR.git
cd PBR

# Install dependencies (Python 3.12+)
pip install -e ".[dev]"

# Run
streamlit run src/ui/app.py
```

Opens at `http://localhost:8501`. Adjust parameters in the sidebar and click **Run Simulation**.

## Project Structure

```
AlgaeGrowth-Simulator/
├── src/
│   ├── simulation/          # engine.py, growth.py, light.py
│   ├── climate/             # temperature.py, growth_modifier.py, loader.py, surat.yaml
│   ├── models/              # parameters.py (frozen dataclasses), results.py
│   ├── config/              # species_params.yaml (DOI-cited), loader.py
│   └── ui/                  # app.py, sidebar.py, results.py, charts.py, export.py
├── tests/                   # 172 tests across 9 files
├── docs/diagrams/           # SVG architecture diagrams (beautiful-mermaid)
├── .streamlit/              # Theme config (green eco theme)
├── pyproject.toml           # Python 3.12+, dependencies, tool config
└── LICENSE                  # MIT
```

<details>
<summary><strong>Scientific Methodology</strong></summary>

### Growth Model

The simulator combines three peer-reviewed submodels evaluated at each daily timestep:

**1. Steele Photoinhibition** (light response)

$$f(I) = \frac{I}{I_{opt}} \cdot e^{1 - I/I_{opt}}$$

Peaks at 1.0 when irradiance equals `I_opt` (80 umol/m2/s for *C. vulgaris*), declining at higher intensities.

**2. Monod CO2 Kinetics** (substrate limitation)

$$f(CO_2) = \frac{CO_2}{K_s + CO_2}$$

Half-saturation `K_s` = 0.5 mg/L dissolved CO2.

**3. CTMI Cardinal Temperature** (thermal response)

$$\varphi(T) = \frac{(T - T_{max})(T - T_{min})^2}{(T_{opt} - T_{min}) \left[ (T_{opt} - T_{min})(T - T_{opt}) - (T_{opt} - T_{max})(T_{opt} + T_{min} - 2T) \right]}$$

Returns 0 outside [T_min, T_max], peaks at 1.0 at T_opt. For Surat: T_min=8 C, T_opt=28 C, T_max=40 C.

**4. Beer-Lambert Depth Integration** (light attenuation)

$$I(z) = I_0 \cdot e^{-(\sigma_x \cdot X + k_{bg}) \cdot z}$$

Pond divided into 20 layers; growth rate computed at each layer midpoint and averaged. Avoids 20-50% overestimation from using surface irradiance alone.

**5. Combined Growth Rate**

$$\mu_{net} = \mu_{max} \cdot f(I_{avg}) \cdot f(CO_2) \cdot \varphi(T_{day}) \cdot D_f \cdot \frac{h_{photo}}{24} - r_m \cdot \varphi(T_{night}) \cdot \frac{24 - h_{photo}}{24}$$

Where D_f = 0.5 (lab-to-field discount) and r_m = 0.01/d (maintenance respiration).

### Parameter Sources

| Parameter | Value | Unit | Source | DOI |
|-----------|-------|------|--------|-----|
| mu_max | 1.0 | 1/d | Schediwy et al. (2019) | [10.1002/elsc.201900107](https://doi.org/10.1002/elsc.201900107) |
| K_s (CO2) | 0.5 | mg/L | Schediwy et al. (2019) | [10.1002/elsc.201900107](https://doi.org/10.1002/elsc.201900107) |
| I_opt | 80.0 | umol/m2/s | Razzak et al. (2024) | [10.1016/j.gce.2023.10.004](https://doi.org/10.1016/j.gce.2023.10.004) |
| r_maintenance | 0.01 | 1/d | General microalgae literature | — |
| sigma_x | 0.2 | m2/g | Schediwy et al. (2019) | [10.1002/elsc.201900107](https://doi.org/10.1002/elsc.201900107) |
| k_bg | 0.5 | 1/m | General open pond literature | — |
| carbon_content | 0.50 | g_C/g_DW | Schediwy et al. (2019) | [10.1002/elsc.201900107](https://doi.org/10.1002/elsc.201900107) |
| CO2:biomass | 1.83 | g_CO2/g_DW | Derived: (44/12) x 0.50 | [10.1002/elsc.201900107](https://doi.org/10.1002/elsc.201900107) |
| discount_factor | 0.50 | — | Schediwy et al. (2019) | [10.1002/elsc.201900107](https://doi.org/10.1002/elsc.201900107) |
| T_min | 8.0 | C | Conservative lower bound | — |
| T_opt | 28.0 | C | Converti et al. (2009) | [10.1016/j.cep.2009.03.006](https://doi.org/10.1016/j.cep.2009.03.006) |
| T_max | 40.0 | C | Converti et al. (2009) | [10.1016/j.cep.2009.03.006](https://doi.org/10.1016/j.cep.2009.03.006) |

### Key Assumptions

- Monod kinetics with single-substrate (CO2) limitation
- Steele photoinhibition (growth declines above I_opt)
- Day/night temperature split (avoids averaging artifacts at 35+ C)
- 50% lab-to-field discount factor (midpoint of 40-60% range)
- Forward Euler integration with 1-day timestep (~2-5% deviation from finer stepping)
- 30-day month approximation for seasonal mapping

### Factors Not Modeled

- Nutrient limitation (N, P depletion)
- Contamination and zooplankton grazing
- Pond surface evaporation and water balance
- CO2 gas-liquid transfer kinetics
- Culture crash recovery dynamics
- Light spectrum variation (PAR only)

### References

1. Schediwy, K. et al. (2019). Kinetic modeling of *Chlorella vulgaris*. *Eng. Life Sci.*, 19(12), 935-943. [10.1002/elsc.201900107](https://doi.org/10.1002/elsc.201900107)
2. Razzak, S.A. et al. (2024). Microalgae cultivation for CO2 capture. *Green Chem. Eng.* [10.1016/j.gce.2023.10.004](https://doi.org/10.1016/j.gce.2023.10.004)
3. Converti, A. et al. (2009). Effect of temperature on *Chlorella vulgaris* growth rate. *Chem. Eng. Process.*, 48(6), 1146-1151. [10.1016/j.cep.2009.03.006](https://doi.org/10.1016/j.cep.2009.03.006)
4. Bernard, O. & Remond, B. (2012). Validation of a microalgae growth model. *Bioresour. Technol.*, 111, 386-394. [10.1016/j.biortech.2012.07.022](https://doi.org/10.1016/j.biortech.2012.07.022)
5. Rosso, L. et al. (1993). An unexpected correlation between cardinal temperatures. *Appl. Environ. Microbiol.*, 59(3), 744-754.
6. Steele, J.H. (1962). Environmental control of photosynthesis in the sea. *Limnol. Oceanogr.*, 7(2), 137-150.

</details>

## Testing

```bash
# Run all 172 tests
pytest

# With coverage
pytest --tb=short -q

# Specific module
pytest tests/test_growth.py -v
```

Test suite covers growth kinetics, light attenuation, temperature response, climate integration, simulation engine, harvest logic, CO2 accounting, parameter validation, and YAML loading.

## Carbon Credit Disclaimer

> This simulator estimates CO2 capture based on peer-reviewed growth models and Surat climate data. Results are intended to **support** carbon credit verification applications, not to represent verified carbon credits.
>
> For actual carbon credit issuance, submit simulation exports alongside site-specific data to an accredited verification body:
> - **[Verra (VCS)](https://verra.org/)** -- Largest voluntary carbon market; ISO 14065 verification
> - **[Gold Standard](https://www.goldstandard.org/)** -- WWF-founded; requires 3+ UN SDG contributions
> - **[India CCTS](https://beeindia.gov.in/)** -- Carbon Credit Trading Scheme under BEE

## License

MIT License. Copyright (c) 2026 Vatsal Mehta. See [LICENSE](LICENSE).

## Citations

If you use this simulator in research or verification workflows, please cite:

```bibtex
@software{algaegrowth_simulator,
  title   = {AlgaeGrowth Simulator},
  author  = {Mehta, Vatsal},
  year    = {2026},
  url     = {https://github.com/vatsalmehta2001/PBR},
  note    = {Monod + Steele + CTMI growth model for CO2 capture estimation}
}
```
