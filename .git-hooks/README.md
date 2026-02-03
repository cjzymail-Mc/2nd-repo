# Git Hooks

This directory contains Git hook templates for the project.

## Pre-commit Hook

**Purpose**: Prevent AI agents from accidentally committing to the main branch.

**How it works**:
- Detects environment variables set by `orchestrator.py` and `agent-task.py`
- If `AGENT_TASK=true` or `ORCHESTRATOR_RUNNING=true` → blocks commits to main/master
- Human commits to main → shows warning but allows (after confirmation)
- Commits to feature branches → always allowed

## Installation

**Windows**:
```bash
install-hooks.bat
```

**Linux/Mac**:
```bash
chmod +x install-hooks.sh
./install-hooks.sh
```

## Manual Installation

If the install scripts don't work, copy manually:

```bash
# Copy the hook
cp .git-hooks/pre-commit .git/hooks/pre-commit

# Make executable (Linux/Mac only)
chmod +x .git/hooks/pre-commit
```

## Testing

```bash
# Should be REJECTED (AI on main branch)
git checkout main
export AGENT_TASK=true  # or: set AGENT_TASK=true on Windows
git commit -m "test"

# Should be ALLOWED (AI on feature branch)
git checkout -b feature/test
export AGENT_TASK=true
git commit -m "test"

# Should WARN but allow (human on main branch)
git checkout main
unset AGENT_TASK  # or: set AGENT_TASK= on Windows
git commit -m "test"
```

## Bypass (Emergency Only)

```bash
git commit -m "emergency fix" --no-verify
```

⚠️ **Use with caution**: This bypasses all pre-commit checks.

## More Info

See [docs/GIT_HOOKS_GUIDE.md](../docs/GIT_HOOKS_GUIDE.md) for detailed documentation.
