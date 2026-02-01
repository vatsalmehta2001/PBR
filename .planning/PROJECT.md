# AlgaeGrowth Simulator

## What This Is

A Python/Streamlit web application that simulates algae growth and CO2 capture under Surat, India's tropical/monsoon climate. Uses peer-reviewed Monod growth kinetics with Steele photoinhibition, CTMI temperature response, and species-specific CO2 conversion to produce defensible estimates for carbon credit verification workflows.

## Core Value

Produce accurate, defensible CO2 capture estimates that carbon credit stakeholders can trust for verification and projection.

## Requirements

### Validated

- Simulator accepts climate parameters (temperature, PAR, photoperiod) with Surat defaults -- v1.0
- Simulator accepts farm setup parameters (pond surface area, depth) -- v1.0
- Simulator accepts operational parameters (CO2 injection, initial biomass, harvest threshold, duration) -- v1.0
- Built-in Surat climate data (12-month seasonal averages) as default -- v1.0
- User can override climate data with custom values -- v1.0
- Simulator outputs total CO2 captured (tCO2e) with methodology visible -- v1.0
- Interactive biomass growth and CO2 accumulation charts (Plotly) -- v1.0
- CSV/JSON data export with disclaimers for verification workflows -- v1.0
- Methodology transparency with DOI-linked citations, assumptions, and references -- v1.0
- Clear disclaimers framing tool as estimation aid, not credit issuance -- v1.0
- Deployable on Streamlit Cloud free tier -- v1.0

### Active

(None -- next milestone not yet defined)

### Out of Scope

- User accounts/authentication -- v2, after validating core value
- Payment integration -- v2, after user traction
- PDF reports for auditors -- v2, based on customer feedback
- Confidence intervals/uncertainty -- v2, adds complexity without validated need
- Multi-region support -- Surat-first, expand after proving model
- Multi-species comparison -- v2 (Chlorella vs Spirulina)
- GEI-compatible output for India CCTS -- v2
- Harvesting schedule configuration -- v2

## Context

- **Opportunity:** Specific business opportunity in Surat driving timeline
- **Target users:** Carbon credit buyers/sellers needing CO2 capture verification
- **Use cases:** Both verification of existing claims and projection of future capture
- **Growth model:** Monod + Steele photoinhibition + CTMI temperature response (5 DOI-cited papers)
- **Business model:** Freemium SaaS -- core simulation free, advanced features (reports, API) paid in future
- **Current state:** v1.0 shipped (6,251 LOC Python/YAML, 172 tests, 34 files)

## Constraints

- **Tech stack:** Python + Streamlit
- **Deployment:** Streamlit Cloud -- free tier
- **Climate scope:** Surat, India (tropical/monsoon)
- **Model source:** Peer-reviewed equations with DOI citations -- scientific basis required for credibility

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit over custom frontend | Rapid development, easy deployment, sufficient for MVP | ✓ Good -- shipped in 4 days |
| Surat-only for v1 | Specific opportunity, validate before expanding | ✓ Good -- focused scope |
| No auth in v1 | Focus on core simulation value, add accounts when needed | ✓ Good -- reduced complexity |
| Freemium model | Lower barrier to entry for carbon credit market | -- Pending validation |
| Physics-first architecture (Phases 1-3 before UI) | Validated model before wrapping with UI | ✓ Good -- clean separation |
| Conservative 6-10 g/m2/day baseline | Lab-to-field 0.5x discount avoids overestimation | ✓ Good -- defensible |
| Species-specific CO2 conversion (1.83) | Derived from cited carbon content, not magic constant | ✓ Good -- auditable |
| Frozen dataclasses throughout | Cache safety, immutability, reproducibility | ✓ Good -- zero mutation bugs |
| YAML single source of truth for parameters | DOI citations, auditable, UI reads dynamically | ✓ Good -- methodology section works |
| Forward Euler 1-day stepping | Simple, transparent, ~2-5% deviation acceptable | ✓ Good -- sufficient accuracy |

---
*Last updated: 2026-02-01 after v1.0 milestone*
