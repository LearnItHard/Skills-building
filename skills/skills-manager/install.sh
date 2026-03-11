#!/bin/bash
# Skills Manager Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/LearnItHard/Skills-building/main/skills/skills-manager/install.sh | bash

set -e

INSTALL_DIR="${HOME}/.local/share/skills-manager"
BIN_DIR="${HOME}/.local/bin"
REPO_URL="https://github.com/LearnItHard/Skills-building"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Installing Skills Manager...${NC}"

# Create directories
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Download the script
echo "Downloading skills.py..."
curl -fsSL "${REPO_URL}/raw/main/skills/skills-manager/skills.py" -o "$INSTALL_DIR/skills.py"

# Create wrapper script
cat > "$BIN_DIR/skills" << 'EOF'
#!/bin/bash
python3 "$HOME/.local/share/skills-manager/skills.py" "$@"
EOF

chmod +x "$BIN_DIR/skills"

# Check if BIN_DIR is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Warning: $BIN_DIR is not in your PATH${NC}"
    echo "Add this to your shell profile (.bashrc, .zshrc, etc.):"
    echo "  export PATH=\"$BIN_DIR:\$PATH\""
fi

echo -e "${GREEN}✓ Skills Manager installed successfully!${NC}"
echo ""
echo "Usage:"
echo "  skills install LearnItHard/Skills-building/mineru-converter"
echo "  skills list"
echo "  skills uninstall mineru-converter"
