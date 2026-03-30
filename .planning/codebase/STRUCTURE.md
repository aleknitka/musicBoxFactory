# Codebase Structure

**Analysis Date:** 2026-03-30

## Directory Layout

```
musicBoxFactory/
├── main.py                 # Application entry point
├── pyproject.toml          # Python package configuration and metadata
├── README.md               # Project documentation
├── .python-version         # Python version specification (3.13)
├── .gitignore              # Git ignore patterns
└── .planning/
    └── codebase/           # Planning and analysis documents
```

## Directory Purposes

**Project Root:**
- Purpose: Application root and package configuration
- Contains: Entry point script, package metadata, version specification
- Key files: `main.py`, `pyproject.toml`, `.python-version`

**.planning/codebase/:**
- Purpose: Architecture and code analysis documentation
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md (generated)
- Key files: Analysis documents for planning and execution phases

**musicboxfactory/ (to be created):**
- Purpose: Core package containing music box generation logic
- Contains: Modules for algorithmic loop creation, music box emulation
- Key files: (Not yet implemented)

## Key File Locations

**Entry Points:**
- `main.py`: Primary application entry point with main() function

**Configuration:**
- `pyproject.toml`: Package metadata, Python version requirement (>=3.13), project name and description
- `.python-version`: Specifies Python 3.13 for version managers (pyenv, direnv)
- `.gitignore`: Standard Python ignores (__pycache__/, *.pyc, build/, dist/, .venv/)

**Documentation:**
- `README.md`: Project overview and usage (currently minimal)

**Core Logic:**
- (Not yet implemented) - Will be in `musicboxfactory/` package subdirectory

**Testing:**
- (Not yet implemented) - Candidates: `tests/` directory or `musicboxfactory/tests/`

## Naming Conventions

**Files:**
- Snake case for module files: `main.py`, `config.py` (future)
- UPPERCASE.md for documentation: `README.md`

**Directories:**
- Snake case for packages: `musicboxfactory/` (lowercase, no hyphens)
- Standard names: `.planning/`, `tests/`, `src/` or `musicboxfactory/` for main code

**Python Modules:**
- Module files: snake_case (e.g., `loop_generator.py`, `music_box.py`)
- Class names: PascalCase (e.g., `LoopGenerator`, `MusicBox`)
- Function names: snake_case (e.g., `generate_loop()`, `create_pattern()`)
- Constants: UPPER_CASE (e.g., `MAX_LOOP_LENGTH`)

## Where to Add New Code

**New Feature:**
- Primary code: `musicboxfactory/{feature_name}.py` (one module per feature)
- Tests: `tests/test_{feature_name}.py` (mirror module structure)
- Example: `musicboxfactory/loop_generator.py` paired with `tests/test_loop_generator.py`

**New Component/Module:**
- Implementation: Create module in `musicboxfactory/` following snake_case naming
- Initialize in `musicboxfactory/__init__.py` with public exports
- Example: `musicboxfactory/patterns.py` for pattern definitions

**Utilities:**
- Shared helpers: `musicboxfactory/utils.py` or domain-specific utility modules
- Helper functions here should be used by 2+ modules
- Keep utilities focused and single-responsibility

**CLI Commands:**
- Entry point script: Extend `main.py` or create `musicboxfactory/cli.py`
- Register entry points in `pyproject.toml` [project.scripts] section

## Special Directories

**.git/:**
- Purpose: Version control metadata
- Generated: Yes (automatically)
- Committed: Yes (tracked by Git itself)

**.venv/ (not present, to be created):**
- Purpose: Virtual environment for isolated dependencies
- Generated: Yes (created by `python -m venv .venv`)
- Committed: No (listed in .gitignore)

**__pycache__/ (not present, generated):**
- Purpose: Python bytecode cache
- Generated: Yes (automatically by Python)
- Committed: No (listed in .gitignore)

**.planning/codebase/:**
- Purpose: Code analysis and planning documentation
- Generated: Yes (by /gsd:map-codebase command)
- Committed: Yes (tracked in Git)

---

*Structure analysis: 2026-03-30*
