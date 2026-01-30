# Requirements: AlgaeGrowth Simulator

**Defined:** 2026-01-27
**Core Value:** Produce accurate, defensible CO2 capture estimates that carbon credit stakeholders can trust

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Simulation Core

- [x] **SIM-01**: Implement Monod growth equations with conservative field-validated parameters (6-10 g/m2/day baseline)
- [x] **SIM-02**: Implement Beer-Lambert light attenuation calculations for depth-averaged growth rate
- [x] **SIM-03**: Implement temperature-dependent growth modifier including >35C inhibition (culture crash)
- [ ] **SIM-04**: Calculate CO2 capture using species-specific conversion factors with cited sources

### Climate Data

- [x] **CLIM-01**: Provide Surat monthly climate defaults (temperature, humidity, solar radiation, rainfall)
- [x] **CLIM-02**: Model three seasons: Dry (Oct-Feb), Hot (Mar-May), Monsoon (Jun-Sep)
- [x] **CLIM-03**: Apply monsoon cloud cover factor reducing PAR availability June-September
- [ ] **CLIM-04**: User can override any climate default with custom values

### Farm Parameters

- [ ] **FARM-01**: User can input pond/reactor surface area and volume
- [ ] **FARM-02**: User can input pond depth (critical for light penetration calculations)

### Operational Parameters

- [ ] **OPS-01**: User can specify simulation duration (days/months)
- [ ] **OPS-02**: User can input initial biomass concentration (g/L)
- [ ] **OPS-03**: User can input CO2 injection rate

### Outputs & Visualization

- [ ] **OUT-01**: Display total CO2 captured (tCO2e) with calculation methodology shown
- [ ] **OUT-02**: Show biomass growth time-series chart (Plotly interactive)
- [ ] **OUT-03**: Show CO2 accumulation time-series chart (Plotly interactive)
- [ ] **OUT-04**: Export simulation data as CSV and JSON for external verification

### Carbon Credit Context

- [ ] **CRED-01**: Display methodology transparency (equations, assumptions, parameter sources)
- [ ] **CRED-02**: Show clear disclaimers: "Estimates CO2 capture for verification support, not verified carbon credits"

### Deployment

- [ ] **DEPLOY-01**: Application deployable to Streamlit Cloud free tier

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Simulation

- **SIM-05**: Multi-species comparison (Chlorella vs Spirulina side-by-side)
- **SIM-06**: User can select from preset algae species with different parameters
- **SIM-07**: User can select cultivation method (open pond vs closed photobioreactor)
- **SIM-08**: User can configure harvesting schedule

### Enhanced Carbon Credit

- **CRED-03**: GEI-compatible output format for India CCTS
- **CRED-04**: Baseline scenario comparison (with vs without algae cultivation)
- **CRED-05**: Confidence intervals / uncertainty bounds on estimates

### User Management

- **USER-01**: User accounts and authentication
- **USER-02**: Save and load simulations
- **USER-03**: Payment integration for premium tier

### Reporting

- **REPORT-01**: Generate PDF verification reports for auditors

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Automatic carbon credit issuance | Only accredited registries (Verra, Gold Standard) can issue credits; would destroy credibility |
| "Guaranteed" CO2 capture claims | All models have uncertainty; promising exact numbers invites liability |
| Blockchain-based credit tracking | India CCTS uses regulated exchanges, not blockchain; adds complexity without value |
| Real-time satellite integration | DMRV systems cost millions; use validated climate data instead |
| Mobile app | Web-first, mobile browser sufficient for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SIM-01 | Phase 1 | Complete |
| SIM-02 | Phase 1 | Complete |
| SIM-03 | Phase 2 | Complete |
| SIM-04 | Phase 3 | Pending |
| CLIM-01 | Phase 2 | Complete |
| CLIM-02 | Phase 2 | Complete |
| CLIM-03 | Phase 2 | Complete |
| CLIM-04 | Phase 4 | Pending |
| FARM-01 | Phase 4 | Pending |
| FARM-02 | Phase 4 | Pending |
| OPS-01 | Phase 4 | Pending |
| OPS-02 | Phase 4 | Pending |
| OPS-03 | Phase 4 | Pending |
| OUT-01 | Phase 5 | Pending |
| OUT-02 | Phase 5 | Pending |
| OUT-03 | Phase 5 | Pending |
| OUT-04 | Phase 5 | Pending |
| CRED-01 | Phase 6 | Pending |
| CRED-02 | Phase 6 | Pending |
| DEPLOY-01 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-01-27*
*Traceability updated: 2026-01-27 (roadmap creation)*
