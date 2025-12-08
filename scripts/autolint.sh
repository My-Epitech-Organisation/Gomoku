#!/bin/bash
# autolint.sh - Script to automatically fix Python code linting issues

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}=========================================================="
echo "               Code Auto-Linting for Gomoku"
echo -e "==========================================================${NC}"

# Check if Ruff is installed
if ! command -v ruff &> /dev/null; then
    echo -e "${RED}Ruff is not installed. Installing...${NC}"
    pip install ruff
fi

# Check if Black is installed
if ! command -v black &> /dev/null; then
    echo -e "${RED}Black is not installed. Installing...${NC}"
    pip install black
fi

# Define backend path
DIR="src"

if [ ! -d "$DIR" ]; then
    echo -e "${RED}Error: Directory does not exist.${NC}"
    exit 1
fi

echo -e "${YELLOW}Auto-fixing code in $DIR with Ruff...${NC}"
ruff check "$DIR" --config config/pyproject.toml --fix --statistics || true

echo -e "${YELLOW}Formatting code with Black...${NC}"
black "$DIR" --config config/pyproject.toml || true

echo -e "${GREEN}=========================================================="
echo "                 Backend auto-linting completed!"
echo -e "==========================================================${NC}"
