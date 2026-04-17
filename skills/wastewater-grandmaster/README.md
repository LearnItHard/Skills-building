# Wastewater Grandmaster

Grandmaster-level engineering assistant for **GB 50014-2021 室外排水设计标准** (Outdoor Drainage Design Standard).

## Features

- **314 canonical GB 50014-2021 chapters** with structured indexes
- **11 calculation scripts** covering hydraulics, storm/sewage flow, pumps, treatment, sludge, sponge city, clearance, and monitoring
- **Typed rule engine** evaluating 14 legal mandatory clauses and ~2048 design rules
- **Unit-tracked, citation-enriched JSON outputs** from every script

## Installation

### Via add-skill
```bash
npx add-skill LearnItHard/Skills-building --skill wastewater-grandmaster
```

### Manual
Copy the `skills/wastewater-grandmaster` folder into your skills directory.

### Release
This skill is released as `v1.0.0` on GitHub. To install the tagged release locally:
```bash
git clone https://github.com/LearnItHard/Skills-building.git
cd Skills-building
git checkout v1.0.0
cp -r skills/wastewater-grandmaster ~/.claude/skills/
```

## Quick Start

All calculation scripts are standalone CLI tools.

### Storm Flow
```bash
python scripts/calc_storm_flow.py \
  --A1 17.0 --C 0.8 --P 2 --b 12 --n 0.75 \
  --t1 10 --t2 15 --psi 0.65 --F 50
```

### Sewage Flow
```bash
python scripts/calc_sewage_flow.py \
  --population 50000 --water_quota_Lpd 180 \
  --discharge_coeff 0.85 --json
```

If you need the commentary-based peak-factor fit instead of the normative table,
add `--peak_factor_method fitted`.

### Pump Head
```bash
python scripts/calc_pump_sewage.py \
  --design_flow_L_s 100 --static_head_m 5 \
  --head_loss_m 2 --safety_head_m 1 \
  --max_pump_flow_L_s 120 --json
```

### Treatment Volume
```bash
python scripts/calc_treatment.py \
  --Q_m3d 10000 --So 200 --Se 20 --Ls 0.3 --X 3.5 \
  --Y 0.6 --theta_c 10 --Xv 2.5 --Kd20 0.06 --theta_T 1.03 --T 15
```

### Sponge City Design Rainfall
```bash
python scripts/calc_sponge_city.py \
  --rainfall_mm "[10,20,30,40,50]" \
  --target_control_rate 0.8
```

### Compliance Check (Rule Engine)
```python
from scripts.rule_engine import TypedRuleEngine

engine = TypedRuleEngine(
    "references/mandatory_clauses.json",
    "references/design_rules.json"
)

results = engine.check(
  "排水管渠和附属构筑物",
    {"system_type": "sewage"},
    {"fullness": 0.60, "pipe_diameter_mm": 250}
)
for r in results:
  print(r.clause, r.status, r.citation_text)
```

Use `engine.list_domains()` if you need to inspect the available source-rule domains first.

## Tests

Run the full test suite:

```bash
cd skills/wastewater-grandmaster
python -m pytest tests/ -v
```

## Directory Structure

```
wastewater-grandmaster/
├── SKILL.md                     # Skill manifest
├── README.md                    # This file
├── scripts/                     # Calculation scripts
│   ├── common/                  # Shared modules (units, citations, validation)
│   ├── calc_hydraulics.py
│   ├── calc_storm_flow.py
│   ├── calc_sewage_flow.py
│   ├── calc_pump_storm.py
│   ├── calc_pump_sewage.py
│   ├── calc_pump_combined.py
│   ├── calc_treatment.py
│   ├── calc_sludge.py
│   ├── calc_sponge_city.py
│   ├── calc_clearance.py
│   ├── calc_monitoring.py
│   └── rule_engine.py
├── tests/                       # pytest test files
├── references/                  # GB 50014-2021 data
│   ├── gb50014-2021/            # 314 canonical chapters
│   ├── glossary.json
│   ├── formula_index.json
│   ├── table_index.json
│   ├── mandatory_clauses.json
│   ├── design_rules.json
│   ├── cross_standard_refs.json
│   ├── applicability_rules.md
│   └── design_workflows.md
```

## License

MIT
