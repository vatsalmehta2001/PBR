# Roadmap: AlgaeGrowth Simulator

## Overview

This roadmap delivers a Python/Streamlit web application that simulates algae growth and CO2 capture for carbon credit verification in Surat, India. The structure follows research recommendations: build validated physics first (Phases 1-3), then wrap with UI (Phase 4), add visualization/export (Phase 5), and frame for carbon credit context (Phase 6). Each phase delivers a coherent capability that can be tested independently.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Core Model** - Monod equations, Beer-Lambert, conservative parameters
- [x] **Phase 2: Surat Climate Integration** - Temperature inhibition, seasonal modeling, monsoon effects
- [ ] **Phase 3: Simulation Engine & CO2 Calculation** - ODE solver, time-series, CO2 conversion
- [ ] **Phase 4: Streamlit UI (Inputs)** - Parameter forms, user overrides, session state
- [ ] **Phase 5: Visualization & Export** - Interactive charts, CSV/JSON export, deployment
- [ ] **Phase 6: Carbon Credit Context** - Methodology transparency, disclaimers, credibility

## Phase Details

### Phase 1: Foundation & Core Model
**Goal**: Establish pure Python simulation foundation with conservative, field-validated growth equations
**Depends on**: Nothing (first phase)
**Requirements**: SIM-01, SIM-02
**Success Criteria** (what must be TRUE):
  1. Monod growth equations return biomass productivity in 6-10 g/m2/day range for standard conditions
  2. Beer-Lambert calculations reduce growth rate for deeper ponds (>0.3m depth shows measurable attenuation)
  3. Parameter dataclasses are hashable and immutable for downstream caching
  4. Unit tests pass for growth and light modules with documented parameter sources
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md -- Project scaffolding, frozen parameter dataclasses, YAML config with citations, validated loader
- [x] 01-02-PLAN.md -- Beer-Lambert light attenuation and depth-averaged irradiance (TDD)
- [x] 01-03-PLAN.md -- Monod growth kinetics with Steele photoinhibition and integration tests (TDD)

### Phase 2: Surat Climate Integration
**Goal**: Model Surat's extreme climate (40C+ pre-monsoon, 359mm monsoon rainfall) with temperature-dependent growth inhibition
**Depends on**: Phase 1
**Requirements**: SIM-03, CLIM-01, CLIM-02, CLIM-03
**Success Criteria** (what must be TRUE):
  1. Surat climate defaults load correctly (temperature ranges 7.6-44C, humidity 42-86%, rainfall 0-359mm/month)
  2. Three seasons are distinguishable in output: Dry (Oct-Feb), Hot (Mar-May), Monsoon (Jun-Sep)
  3. Growth rate drops significantly (>50%) when temperature exceeds 35C (culture crash modeling)
  4. Monsoon months (Jun-Sep) show reduced productivity due to cloud cover PAR reduction
  5. Climate module integrates with Phase 1 growth equations without breaking unit tests
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md -- Climate dataclasses, Surat YAML config, Pydantic-validated loader
- [x] 02-02-PLAN.md -- CTMI temperature response function (TDD)
- [x] 02-03-PLAN.md -- Day/night growth integration with seasonal verification tests

### Phase 3: Simulation Engine & CO2 Calculation
**Goal**: Orchestrate growth + climate into full time-series simulation with species-specific CO2 capture calculation
**Depends on**: Phases 1 and 2
**Requirements**: SIM-04
**Success Criteria** (what must be TRUE):
  1. Simulation runs for user-specified duration (1 day to 365 days) without errors
  2. CO2 capture output uses species-specific conversion factors with cited sources (not magic 1.88 constant)
  3. SimulationResults dataclass contains biomass time series, CO2 accumulation, and summary statistics
  4. Output values are realistic for Surat conditions (integration tests verify ranges)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Streamlit UI (Inputs)
**Goal**: Enable users to configure simulation parameters with sensible Surat defaults and validation
**Depends on**: Phase 3
**Requirements**: CLIM-04, FARM-01, FARM-02, OPS-01, OPS-02, OPS-03
**Success Criteria** (what must be TRUE):
  1. User can override any climate default with custom values via form inputs
  2. User can input pond surface area and volume with validation (positive numbers only)
  3. User can input pond depth with warning for depths >0.5m (light limitation)
  4. User can specify simulation duration in days or months
  5. User can set initial biomass concentration and CO2 injection rate
  6. Form submission triggers cached simulation run (no re-computation on UI interaction)
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD

### Phase 5: Visualization & Export
**Goal**: Display simulation results with interactive charts and enable data export for verification workflows
**Depends on**: Phase 4
**Requirements**: OUT-01, OUT-02, OUT-03, OUT-04, DEPLOY-01
**Success Criteria** (what must be TRUE):
  1. Total CO2 captured displays in tCO2e with calculation methodology visible
  2. Biomass growth time-series chart is interactive (zoom, hover, pan via Plotly)
  3. CO2 accumulation time-series chart shows daily/cumulative capture
  4. User can export simulation data as CSV and JSON files
  5. Application deploys successfully to Streamlit Cloud free tier
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD
- [ ] 05-03: TBD

### Phase 6: Carbon Credit Context
**Goal**: Frame tool correctly for carbon credit verification with methodology transparency and appropriate disclaimers
**Depends on**: Phase 5
**Requirements**: CRED-01, CRED-02
**Success Criteria** (what must be TRUE):
  1. Methodology transparency section shows equations, assumptions, and parameter sources with citations
  2. Clear disclaimer visible: "Estimates CO2 capture for verification support, not verified carbon credits"
  3. User understands this is a decision-support tool, not credit issuance (no liability exposure)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Core Model | 3/3 | Complete | 2026-01-28 |
| 2. Surat Climate Integration | 3/3 | Complete | 2026-01-30 |
| 3. Simulation Engine & CO2 | 0/TBD | Not started | - |
| 4. Streamlit UI (Inputs) | 0/TBD | Not started | - |
| 5. Visualization & Export | 0/TBD | Not started | - |
| 6. Carbon Credit Context | 0/TBD | Not started | - |

---
*Roadmap created: 2026-01-27*
*Requirements coverage: 20/20 (100%)*
