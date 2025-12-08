#!/bin/bash
# check_lint.sh - Script to check Python code linting without making changes

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}=========================================================="
echo "               Code Linting Check for Gomoku"
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

echo -e "${YELLOW}Checking code in $DIR with Ruff...${NC}"
ruff check "$DIR" --config config/pyproject.toml > ruff_report.txt || true
ruff check "$DIR" --config config/pyproject.toml --statistics || true

echo -e "${YELLOW}Checking formatting with Black...${NC}"
black --check "$DIR" --config config/pyproject.toml || true

echo -e "${GREEN}=========================================================="
echo "                     Code check completed!"
echo -e "==========================================================${NC}"
