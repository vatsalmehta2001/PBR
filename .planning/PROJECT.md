# AlgaeGrowth Simulator

## What This Is

A Python-based Streamlit web app that simulates algae growth and CO₂ capture under Surat, India's tropical/monsoon climate. Enables carbon credit buyers and sellers to verify existing CO₂ capture claims and project future capture from algae cultivation operations.

## Core Value

Produce accurate, defensible CO₂ capture estimates that carbon credit stakeholders can trust for verification and projection.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Simulator accepts climate parameters (temperature, humidity, solar radiation, rainfall)
- [ ] Simulator accepts farm setup parameters (pond size, depth, algae species, cultivation method)
- [ ] Simulator accepts operational parameters (nutrient inputs, harvesting schedule, CO₂ injection)
- [ ] Built-in Surat climate data (monthly/seasonal averages) as default
- [ ] User can override climate data with custom values
- [ ] Simulator outputs total CO₂ captured over specified time period
- [ ] Visualization shows algae biomass growth over time
- [ ] Visualization shows CO₂ capture accumulation over time
- [ ] Deployable on Streamlit Cloud

### Out of Scope

- User accounts/authentication — v2, after validating core value
- Payment integration — v2, after user traction
- PDF reports for auditors — v2, based on customer feedback
- Confidence intervals/uncertainty — v2, adds complexity without validated need
- Multi-region support — Surat-first, expand after proving model

## Context

- **Opportunity:** Specific business opportunity in Surat driving timeline
- **Target users:** Carbon credit buyers/sellers needing CO₂ capture verification
- **Use cases:** Both verification of existing claims and projection of future capture
- **Growth model:** Monod equations from research papers (accessible via NotebookLM "photosynthesis-growth-models" notebook)
- **Business model:** Freemium SaaS — core simulation free, advanced features (reports, API) paid in future

## Constraints

- **Tech stack:** Python + Streamlit — user specified
- **Deployment:** Streamlit Cloud — free tier for MVP
- **Climate scope:** Surat, India (tropical/monsoon) — specific opportunity
- **Model source:** Monod equations from research papers — scientific basis required for credibility

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit over custom frontend | Rapid development, easy deployment, sufficient for MVP | — Pending |
| Surat-only for v1 | Specific opportunity, validate before expanding | — Pending |
| No auth in v1 | Focus on core simulation value, add accounts when needed | — Pending |
| Freemium model | Lower barrier to entry for carbon credit market | — Pending |

---
*Last updated: 2025-01-27 after initialization*
