#!/bin/bash
# Install Git Hooks - Works from any directory

echo "Installing Git hooks..."
echo ""

# Get project root (where .git directory is)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -z "$PROJECT_ROOT" ]; then
    echo "ERROR: Not a git repository"
    echo "Please run this script from within a git repository"
    exit 1
fi

echo "Project root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Check if hook template exists
if [ ! -f ".git-hooks/pre-commit" ]; then
    echo "ERROR: Hook template not found: .git-hooks/pre-commit"
    echo "Please ensure the project structure is correct"
    exit 1
fi

# Backup existing hook
if [ -f ".git/hooks/pre-commit" ]; then
    echo "Backing up existing hook..."
    cp ".git/hooks/pre-commit" ".git/hooks/pre-commit.backup"
fi

# Copy hook file
echo "Installing pre-commit hook..."
cp ".git-hooks/pre-commit" ".git/hooks/pre-commit"

# Make executable
chmod +x ".git/hooks/pre-commit"

echo ""
echo "SUCCESS: Git hook installed"
echo ""
echo "What it does:"
echo "  - Blocks AI agents from committing to main branch"
echo "  - Warns humans when committing to main branch"
echo ""
echo "Test the hook:"
echo "  1. Switch to main: git checkout main"
echo "  2. Set env var: export AGENT_TASK=true"
echo "  3. Try commit: git commit -m 'test'"
echo "  4. Should be rejected"
echo ""
