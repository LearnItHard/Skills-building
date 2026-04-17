---
name: wastewater-grandmaster
description: Grandmaster-level engineering assistant for GB 50014-2021 Outdoor Drainage Design Standard. Provides precise clause citation from 314 canonical chapters, bounded hydraulic and treatment calculations with unit tracking, and layered compliance review distinguishing 14 legal mandatory clauses from ~2048 design rules.
---

# Wastewater Grandmaster (污水处理大师)

## Overview

`wastewater-grandmaster` is a grandmaster-level engineering assistant for **GB 50014-2021 室外排水设计标准** (Outdoor Drainage Design Standard). It combines three tightly integrated capabilities:

1. **Precise Clause Citation** — Instant lookup across all 314 canonical chapters with structured indexes (formulas, tables, mandatory clauses, cross-references).
2. **Bounded Calculations** — Typed Python scripts for hydraulics, storm/sewage flow, pump stations, treatment, sludge digestion, sponge-city rainfall, and clearance checks. Every output carries units, applicability warnings, and GB citations.
3. **Layered Compliance Review** — A typed rule engine that evaluates designs against the 14 legal mandatory clauses and ~2048 design rules, returning `PASS`, `VIOLATION`, `WARNING`, `MANUAL_REVIEW`, or `NOT_APPLICABLE`.

## When to Use

- Designing or reviewing municipal drainage, sewage, stormwater, or combined systems in China.
- You need **exact GB 50014-2021 clause numbers** with Chinese text.
- You want **calculations** (rainfall intensity, pipe hydraulics, pump head, bioreactor volume, sludge digestion, sponge-city control rate) that warn about unit mismatches and method applicability.
- You need **compliance checks** that separate "must not violate" legal mandates from "should follow" design rules.

## Core Capabilities

### 1. Citation & Lookup

All 314 canonical GB 50014-2021 chapters are bundled under `references/gb50014-2021/` with pre-built indexes:

- `index.json` — Chapter-to-file mapping
- `glossary.json` — 21 core terms
- `formula_index.json` — 42 formulas with clause numbers
- `table_index.json` — 68 tables
- `mandatory_clauses.json` — Exactly 14 legal mandatory clauses
- `design_rules.json` — ~2048 design rules with typed conditions
- `cross_standard_refs.json` — Cross-references to other Chinese standards

### 2. Calculation Scripts

Every script is a standalone CLI tool that prints JSON. Run from the skill root (`skills/wastewater-grandmaster/`):

| Script | What it calculates | Key GB clauses |
|--------|-------------------|----------------|
| `scripts/calc_hydraulics.py` | Velocity, flow, hydraulic radius for circular/trapezoidal channels | 5.2.4, 5.2.7 |
| `scripts/calc_storm_flow.py` | Rainfall intensity, total concentration time, and design storm flow | 4.1.7, 4.1.9, 4.1.11 |
| `scripts/calc_sewage_flow.py` | Domestic sewage design flow with explicit Kz source (`table`, `fitted`, or override) | 4.1.13, 4.1.15 |
| `scripts/calc_pump_storm.py` | Storm pump head = static + loss + safety | 6.2.4 |
| `scripts/calc_pump_sewage.py` | Sewage pump head + sump volume (5 min of max pump flow) | 6.2.1, 6.2.4, 6.3.1 |
| `scripts/calc_pump_combined.py` | Combined pump head with pre/post interception flows | 6.2.3, 6.2.4 |
| `scripts/calc_treatment.py` | Bioreactor volume by sludge loading (7.6.10-1) or sludge age (7.6.10-2), plus temperature-corrected Kd (7.6.11) | 7.6.10, 7.6.11 |
| `scripts/calc_sludge.py` | Anaerobic digester volume by time (8.3.6-1) or load (8.3.6-2), optional gas estimate | 8.3.6 |
| `scripts/calc_sponge_city.py` | Annual runoff control rate → design rainfall via cumulative frequency sorting (Appendix A.0.1) | 附录 A.0.1 |
| `scripts/calc_clearance.py` | Minimum horizontal/vertical clearance between drainage pipe and other underground utilities/structures (Appendix C lookup) | 附录C |
| `scripts/calc_monitoring.py` | Online instrument checklist and smart drainage basic item checklist | 9.2, 9.6 |

**Example — Storm flow:**
```bash
python scripts/calc_storm_flow.py \
  --A1 17.0 --C 0.8 --P 2 --b 12 --n 0.75 \
  --t1 10 --t2 15 --psi 0.65 --F 50
```

**Example — Treatment volume:**
```bash
python scripts/calc_treatment.py \
  --Q_m3d 10000 --So 200 --Se 20 --Ls 0.3 --X 3.5 \
  --Y 0.6 --theta_c 10 --Xv 2.5 --Kd20 0.06 --theta_T 1.03 --T 15
```

### 3. Rule Engine

`scripts/rule_engine.py` provides `TypedRuleEngine` for programmatic compliance checking.

**Supported rule types:**
- `numeric_threshold` — Parameter bounds (e.g., fullness ≤ 0.55)
- `enum_branch` — Discrete design context checks
- `facility_existence` — Required infrastructure presence
- `manual_review` — Engineer-required verification

**Example usage:**
```python
from scripts.rule_engine import TypedRuleEngine

engine = TypedRuleEngine(
    "references/mandatory_clauses.json",
    "references/design_rules.json"
)

results = engine.check(
  domain="排水管渠和附属构筑物",
    design_context={"system_type": "sewage"},
    parameters={"fullness": 0.60, "pipe_diameter_mm": 250}
)
```

If you need the exact domain values bundled with the rule datasets, call `engine.list_domains()` first.

Each `RuleResult` includes:
- `clause`, `text`, `domain`, `severity`
- `status` — `PASS` / `VIOLATION` / `WARNING` / `MANUAL_REVIEW` / `NOT_APPLICABLE`
- `citation_text` — Ready-to-cite GB reference

## Design Data & References

- `references/gb50014-2021/` — All 314 canonical chapters
- `references/glossary.json` — Term definitions
- `references/formula_index.json` — 42 formulas
- `references/table_index.json` — 68 tables
- `references/mandatory_clauses.json` — 14 legal mandatory clauses
- `references/design_rules.json` — ~2048 design rules
- `references/cross_standard_refs.json` — Cross-references
- `references/applicability_rules.md` — When each method applies
- `references/design_workflows.md` — 8 engineering decision trees

## Running Tests

All scripts have matching pytest test files under `tests/`.

```bash
python -m pytest tests/ -v
```

## Important Notes

- **Kz fitted formula disclaimer:** When using `peak_factor_method="fitted"` in `calc_sewage_flow.py`, the output includes `"disclaimer": "Kz 来源于条文说明拟合式，非正文公式"`.
- **Storm applicability:** For `F > 2 km²` (200 hm²), `calc_storm_flow.py` sets `method_switched: true` and reminds you to switch methods per GB 50014-2021 4.1.7.
- **Citation paths:** `citation_text` and related outputs now resolve to the real nested markdown file under `references/gb50014-2021/`.
- **Legal mandatory clauses:** There are exactly 14 items in `mandatory_clauses.json`. No expansion is allowed.
- **Not applicable rules:** The rule engine returns `NOT_APPLICABLE` when `design_context["system_type"]` (sewage / storm / combined) does not match a rule's domain.
