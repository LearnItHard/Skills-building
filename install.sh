#!/bin/bash
# MinerU Converter Skill Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/LearnItHard/Skills-building/main/install.sh | bash

set -e

SKILL_NAME="mineru-converter"
REPO_URL="https://github.com/LearnItHard/Skills-building"
SKILL_SOURCE="skills/mineru-converter"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect agent and set install path
detect_agent() {
    if [ -n "$CLAUDE_CODE" ] || [ -d "$HOME/.claude" ]; then
        AGENT="claude-code"
        INSTALL_DIR="$HOME/.claude/skills/$SKILL_NAME"
    elif [ -n "$OPENCODE" ] || [ -d "$HOME/.config/opencode" ]; then
        AGENT="opencode"
        INSTALL_DIR="$HOME/.config/opencode/skill/$SKILL_NAME"
    elif [ -n "$CODEX_HOME" ] || [ -d "$HOME/.codex" ]; then
        AGENT="codex"
        INSTALL_DIR="$HOME/.codex/skills/$SKILL_NAME"
    else
        # Default to Claude Code
        AGENT="claude-code"
        INSTALL_DIR="$HOME/.claude/skills/$SKILL_NAME"
    fi
}

# Install skill
install_skill() {
    echo -e "${GREEN}Installing $SKILL_NAME for $AGENT...${NC}"
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT
    
    # Clone repository
    echo "Downloading skill..."
    git clone --depth 1 "$REPO_URL" "$TEMP_DIR/repo" 2>/dev/null || {
        echo -e "${RED}Failed to clone repository${NC}"
        exit 1
    }
    
    # Create install directory
    mkdir -p "$(dirname "$INSTALL_DIR")"
    
    # Remove old installation if exists
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}Removing old installation...${NC}"
        rm -rf "$INSTALL_DIR"
    fi
    
    # Copy skill files
    cp -r "$TEMP_DIR/repo/$SKILL_SOURCE" "$INSTALL_DIR"
    
    echo -e "${GREEN}✓ $SKILL_NAME installed successfully!${NC}"
    echo ""
    echo "Location: $INSTALL_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. cd $INSTALL_DIR"
    echo "  2. cp .env.example .env"
    echo "  3. Edit .env and add your MinerU API token"
    echo "  4. pip install -r requirements.txt"
}

# Uninstall skill
uninstall_skill() {
    detect_agent
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}Uninstalling $SKILL_NAME...${NC}"
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}✓ Uninstalled${NC}"
    else
        echo -e "${RED}Skill not found at $INSTALL_DIR${NC}"
    fi
}

# Show help
show_help() {
    cat << EOF
MinerU Converter Skill Installer

Usage:
  install.sh [command]

Commands:
  install     Install the skill (default)
  uninstall   Remove the skill
  help        Show this help message

One-line install:
  curl -fsSL https://raw.githubusercontent.com/LearnItHard/Skills-building/main/install.sh | bash

EOF
}

# Main
main() {
    case "${1:-install}" in
        install)
            detect_agent
            install_skill
            ;;
        uninstall)
            uninstall_skill
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
