# Contributing to pyKnit

Thank you for your interest in contributing! This guide will help you get started.

## Setup

```bash
git clone https://github.com/wilsonify/pyknit.git
cd pyknit
pip install -e .
pip install -r requirements.txt
```

## Running tests

```bash
# Unit tests
python -m pytest test/unit/ -x -q

# End-to-end tests (requires Docker)
python -m pytest test/end-to-end/ -x -q

# All tests
python -m pytest test/ -x -q
```

## Code style

We use `black` for formatting and `flake8` for linting:

```bash
black pyknit/ test/
flake8 pyknit/ test/
```

Pre-commit hooks run these automatically:

```bash
pre-commit install
```

## Making changes

1. **Create a branch** from main
2. **Make your changes** -- follow existing code patterns
3. **Add tests** for new functionality
4. **Run the test suite** to make sure nothing breaks
5. **Submit a pull request** with a clear description

## Adding a new function

1. Add the function to the appropriate module in `pyknit/`
2. Add docstrings and type hints
3. Add unit tests in `test/unit/`
4. If the function is useful in browser demos, add a demo module in `pyknit/pyscript/_demos/`

## Adding a new demo

See [creating a demo](creating-a-demo.md) for the full workflow.

## Reporting bugs

[Open an issue](https://github.com/wilsonify/pyknit/issues) with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your Python version and OS

## Security issues

If you find a security issue, please email the maintainer privately rather than
opening a public issue.
