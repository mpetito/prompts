#!/usr/bin/env bash
#
# Setup script to symlink the repository's skills/ directory to the
# cross-tool agent skills folder (~/.agents/skills/).
#
# This makes all skills available to any tool that supports the
# ~/.agents/skills/ convention (opencode, Claude Code, etc.).
#
# Usage:
#   ./setup-opencode.sh
#
# Works on WSL, Linux, and macOS.
#

set -euo pipefail

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Resolve repository root from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SKILLS="$SCRIPT_DIR/skills"

# Cross-tool skills directory (shared by opencode, Claude Code, etc.)
TARGET_SKILLS="$HOME/.agents/skills"

echo -e "${CYAN}Setting up cross-tool agent skills...${NC}"
echo ""

# Validate source
if [ ! -d "$SOURCE_SKILLS" ]; then
    echo -e "${RED}Error: Source skills directory not found:${NC}"
    echo -e "  ${RED}$SOURCE_SKILLS${NC}"
    exit 1
fi

# Handle existing target (symlink, directory, or missing)
if [ -e "$TARGET_SKILLS" ] || [ -L "$TARGET_SKILLS" ]; then
    if [ -L "$TARGET_SKILLS" ]; then
        # It's already a symbolic link
        CURRENT_TARGET="$(readlink "$TARGET_SKILLS")"

        if [ "$CURRENT_TARGET" = "$SOURCE_SKILLS" ]; then
            echo -e "${CYAN}Symbolic link already exists and points to this repository.${NC}"
            echo -e "  ${CYAN}Link:   $TARGET_SKILLS${NC}"
            echo -e "  ${CYAN}Target: $CURRENT_TARGET${NC}"
            echo ""
            echo -e "${GREEN}Setup complete! No changes needed.${NC}"
            exit 0
        fi

        echo -e "${YELLOW}Existing symlink found:${NC}"
        echo -e "  ${YELLOW}Link:   $TARGET_SKILLS${NC}"
        echo -e "  ${YELLOW}Target: $CURRENT_TARGET${NC}"
        read -r -p "Do you want to replace it? (y/N) " response
        echo ""

        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm "$TARGET_SKILLS"
            echo -e "${GREEN}Removed existing symlink.${NC}"
        else
            echo -e "${YELLOW}Skipped. Existing symlink left in place.${NC}"
            exit 0
        fi
    else
        # It's a regular directory — back it up
        PARENT_DIR="$(dirname "$TARGET_SKILLS")"
        FOLDER_NAME="$(basename "$TARGET_SKILLS")"
        BACKUP_DIR="$PARENT_DIR/${FOLDER_NAME}_old"

        if [ -e "$BACKUP_DIR" ]; then
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            BACKUP_DIR="$PARENT_DIR/${FOLDER_NAME}_old_$TIMESTAMP"
        fi

        echo -e "${YELLOW}Existing skills folder found.${NC}"
        echo -e "${YELLOW}Renaming to backup: $BACKUP_DIR${NC}"
        mv "$TARGET_SKILLS" "$BACKUP_DIR"
        echo -e "${GREEN}Backup created successfully.${NC}"
    fi
fi

# Ensure parent directory exists
mkdir -p "$(dirname "$TARGET_SKILLS")"

# Create the symbolic link
ln -s "$SOURCE_SKILLS" "$TARGET_SKILLS"

echo ""
echo -e "${GREEN}Skills symbolic link created successfully!${NC}"
echo -e "  ${CYAN}Link:   $TARGET_SKILLS${NC}"
echo -e "  ${CYAN}Target: $SOURCE_SKILLS${NC}"
echo ""

# Verify: list skills
echo -e "${CYAN}Available skills ($(find "$SOURCE_SKILLS" -mindepth 1 -maxdepth 1 -type d | wc -l) found):${NC}"
for skill_dir in "$SOURCE_SKILLS"/*/; do
    skill_name="$(basename "$skill_dir")"
    echo -e "  ${GREEN}•${NC} $skill_name"
done

echo ""
echo -e "${GREEN}Setup complete.${NC}"
echo ""
echo -e "These skills are now auto-discovered by tools that scan ${CYAN}~/.agents/skills/${NC}."
