# Contributing to BLACKSPOT

Thank you for your interest in improving SSD forensic triage tooling.

## Scope

BLACKSPOT is a **read-only, host-side** SSD triage tool. Contributions must:

- Never write to the target drive or alter evidence
- Never require proprietary firmware tools or chip-off hardware
- Work with standard Linux block-device interfaces

## How to Contribute

### Bug Reports
Open an issue with: OS/kernel version, SSD model (if applicable), full traceback, and the command you ran.

### Detection Rules
New fingerprint patterns for controller behaviors (DZAT, DRAT, non-deterministic TRIM) are welcome. Include:
- The controller/firmware combination tested
- Raw capture data or a reproducible script
- Expected vs. observed behavior

### Sample Packs
Synthetic or real (sanitized) capture data that exercises edge cases.

### Documentation
Improvements to the decision tree, talk outline, or forensic workflow docs.

## Development Setup

```bash
git clone https://github.com/p17433308-cmyk/dead-mens-tales.git
cd dead-mens-tales
pip install -e .
pytest tests/
```

## Code Style

- Python 3.9+, type hints encouraged
- No third-party dependencies in core (stdlib only)
- Tests for every new detection rule

## License

By contributing, you agree that your contributions will be licensed under the project's existing license.
