# Skills Manager CLI

A simple CLI tool to install and manage Claude Code / OpenCode / Codex skills from GitHub repositories.

## Features

- 🔍 **Auto-detect** which AI agent you're using
- 📦 **Install** skills from GitHub with one command
- 🗑️ **Uninstall** skills easily
- 📋 **List** installed skills
- 🎯 **Multi-agent support** (Claude Code, OpenCode, Codex, Cursor)

## Installation

### One-line install (Linux/Mac)

```bash
curl -fsSL https://raw.githubusercontent.com/LearnItHard/Skills-building/main/skills/skills-manager/install.sh | bash
```

### Windows (PowerShell)

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/LearnItHard/Skills-building/main/skills/skills-manager/install.ps1" -OutFile "$env:TEMP\skills-install.ps1"; & "$env:TEMP\skills-install.ps1"
```

### Manual install

```bash
# Clone the repository
git clone https://github.com/LearnItHard/Skills-building.git

# Copy skills-manager to your PATH
cp Skills-building/skills/skills-manager/skills.py /usr/local/bin/skills
chmod +x /usr/local/bin/skills
```

## Usage

### Install a skill

```bash
# Install specific skill from repo
skills install LearnItHard/Skills-building/mineru-converter

# Install with force (overwrite existing)
skills install LearnItHard/Skills-building/mineru-converter --force
```

### List installed skills

```bash
skills list
```

### Uninstall a skill

```bash
skills uninstall mineru-converter
```

## How it works

1. Detects which AI agent you're using (Claude Code, OpenCode, etc.)
2. Clones the repository to a temp directory
3. Copies the skill to the appropriate directory:
   - Claude Code: `~/.claude/skills/`
   - OpenCode: `~/.config/opencode/skill/`
   - Codex: `~/.codex/skills/`

## Repository Structure

The tool expects skills to be organized as:

```
repo/
├── skills/
│   └── skill-name/
│       ├── SKILL.md
│       └── ...
└── ...
```

Or in the root:

```
repo/
├── skill-name/
│   ├── SKILL.md
│   └── ...
└── ...
```

## License

MIT
