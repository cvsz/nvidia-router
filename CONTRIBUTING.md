# Contributing to zrouter

Thank you for considering contributing to zrouter! This document provides guidelines for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Review](#code-review)
- [License](#license)

## Getting Started

### Prerequisites

- Python 3.10+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/cvsz/zrouter.git
cd zrouter

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Install development dependencies
pip install pytest ruff pyinstaller
```

## Development Workflow

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Run tests and linting
5. Commit your changes
6. Push to your fork
7. Open a pull request

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints for all function signatures
- Use docstrings for all public functions and classes
- Maximum line length: 88 characters (ruff default)

### Linting

We use `ruff` for linting and formatting:

```bash
# Check for linting issues
.venv/bin/python -m ruff check zrouter.py test_zrouter.py zcloud-gui.py zcloud-tui.py

# Auto-fix formatting
.venv/bin/python -m ruff format zrouter.py test_zrouter.py zcloud-gui.py zcloud-tui.py
```

### Testing

We use `pytest` for testing:

```bash
# Run all tests
.venv/bin/python -m pytest test_zrouter.py -v

# Run with coverage
.venv/bin/python -m pytest test_zrouter.py --cov=zrouter.py
```

All tests must pass before submitting a pull request.

## Submitting Changes

1. Fork the repository on GitHub
2. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Run tests and linting:
   ```bash
   .venv/bin/python -m pytest test_zrouter.py
   .venv/bin/python -m ruff check zrouter.py test_zrouter.py zcloud-gui.py zcloud-tui.py
   ```
5. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```
6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. Open a pull request on GitHub

## Code Review

All pull requests require:
- At least one approving review
- All CI checks passing
- No merge conflicts

## Security

Do not commit API keys or other sensitive information. See [SECURITY.md](SECURITY.md) for more information.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.