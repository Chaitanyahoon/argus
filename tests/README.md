# Discord Bot Unit Tests

This directory contains comprehensive unit tests for the Discord bot's core functionality.

## What's Tested

### 1. **Fuzzy Matching** (`test_bot_utils.py`)
- ✅ Exact name/username matching
- ✅ Partial name matching
- ✅ Case-insensitive matching
- ✅ Substring matching with bonus score
- ✅ Short name protection (prevents false positives)
- ✅ Whitespace handling
- ✅ Channel name matching with space-to-dash conversion

### 2. **Rate Limiting** (`test_rate_limiting.py`)
- ✅ Basic rate limit enforcement
- ✅ Per-key independent rate limits
- ✅ Cleanup of old attempts after time window
- ✅ Accurate retry time calculation
- ✅ Rapid successive attempt handling
- ✅ High-volume request processing
- ✅ Voice command scenario (5 per 30s)

### 3. **Safety Checks** (`test_safety_checks.py`)
- ✅ **Kick Safety**: Owner protection, role hierarchy, normal users
- ✅ **Ban Safety**: Bot protection, owner protection, role hierarchy
- ✅ **Mute Safety**: Bot protection, voice channel requirement, double-mute prevention
- ✅ **Unmute Safety**: Bot protection, voice channel requirement, double-unmute prevention
- ✅ **Combined scenarios**: Protection consistency across operations

## Running Tests

### Prerequisites
```bash
pip install pytest
```

### Run All Tests
```bash
# Verbose output
pytest tests/ -v

# With coverage
pytest tests/ --cov=core --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_bot_utils.py -v
pytest tests/test_rate_limiting.py -v
pytest tests/test_safety_checks.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_bot_utils.py::TestFuzzyFindMember -v
```

### Run Specific Test
```bash
pytest tests/test_bot_utils.py::TestFuzzyFindMember::test_exact_display_name_match -v
```

## Test Coverage

To see coverage report:
```bash
pytest tests/ --cov=core --cov-report=term-missing
```

## Notes

- Tests use mocking to avoid requiring actual Discord connections
- Each test is independent and can be run in any order
- Tests should pass with Python 3.11+
- All edge cases are covered (empty strings, whitespace, special characters, etc.)

## CI/CD Integration

To integrate into your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pip install pytest
    pytest tests/ -v --tb=short
```
