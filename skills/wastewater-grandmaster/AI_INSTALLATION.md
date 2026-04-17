# Wastewater Grandmaster AI Installation Guide

This file is a concise installation and update guide for AI installers, automation scripts, and maintainers.

## Skill path
- Skill root: `skills/wastewater-grandmaster`
- Compact reference bundle: `skills/wastewater-grandmaster/references/gb50014-2021`

## Installation options

### 1. Install via add-skill
```bash
npx add-skill LearnItHard/Skills-building --skill wastewater-grandmaster
```

### 2. Manual install from repository
```bash
git clone https://github.com/LearnItHard/Skills-building.git
cd Skills-building
cp -r skills/wastewater-grandmaster ~/.claude/skills/
```

### 3. Install specific release tag
```bash
git clone https://github.com/LearnItHard/Skills-building.git
cd Skills-building
git checkout v1.0.0
cp -r skills/wastewater-grandmaster ~/.claude/skills/
```

## Verify installation

From the skill folder, run:
```bash
cd skills/wastewater-grandmaster
python -m pytest tests/test_rule_engine.py -q
```

Confirm the compact reference bundle is present:
- `references/gb50014-2021/gb50014-2021-full.md`
- `references/gb50014-2021/appendix-c-clearance.md`

## Update strategy

- For local installs, overwrite `~/.claude/skills/wastewater-grandmaster` with the updated `skills/wastewater-grandmaster` folder.
- Prefer tagging each release, e.g. `v1.0.1` for bug fixes or `v1.1.0` for feature updates.
- Use `git add -A skills/wastewater-grandmaster` when committing changes to include file additions, modifications, and deletions.

## AI installer notes

- The skill intentionally bundles GB 50014-2021 text into a compact set of files to avoid installer failures from excessive tiny files.
- Do not rely on legacy nested markdown paths under `references/gb50014-2021/`.
- Resolve citations using `references/gb50014-2021/gb50014-2021-full.md` and `references/gb50014-2021/appendix-c-clearance.md`.
- Use the `README.md` and `SKILL.md` for human-readable metadata; use this file for automation-friendly installation steps.
