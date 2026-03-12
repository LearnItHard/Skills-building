# LearnItHard Skills Installer

Interactive CLI tool to install and manage LearnItHard skills for Claude Code, OpenCode, Codex, and Cursor.

## Usage

### One-line install (no need to clone)

```bash
npx @learnithard/skills-installer
```

This will:
1. Auto-detect your installed AI agents
2. Show interactive menu
3. Install selected skills to all detected agents

## Features

- 🔍 **Auto-detect** Claude Code, OpenCode, Codex, Cursor
- 📦 **Install** specific skills or full pack
- 🗑️ **Uninstall** skills
- 🔄 **Update** all skills
- 📋 **List** available skills

## Available Skills

| Skill | Description |
|-------|-------------|
| `mineru-converter` | Document conversion using MinerU API |
| `skills-manager` | CLI tool to manage AI agent skills |

## How it works

1. Detects which AI agents you have installed
2. Clones the Skills-building repo to temp
3. Copies skill files to each agent's skills directory:
   - Claude Code: `~/.claude/skills/`
   - OpenCode: `~/.config/opencode/skill/`
   - Codex: `~/.codex/skills/`
   - Cursor: `~/.cursor/skills/`

## Development

```bash
# Clone repo
git clone https://github.com/LearnItHard/Skills-building.git
cd Skills-building/npm-installer

# Install dependencies
npm install

# Run locally
npm start
```

## Publishing to npm

```bash
# Login to npm
npm login

# Publish (must bump version first)
npm version patch
npm publish --access public
```

## License

MIT
