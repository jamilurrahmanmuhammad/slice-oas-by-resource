"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
from pathlib import Path
from slice_oas.parser import parse_oas


@pytest.fixture
def fixtures_dir():
    """Get path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def oas_3_0_simple(fixtures_dir):
    """Load simple OAS 3.0 fixture."""
    path = fixtures_dir / "oas_3_0_simple.yaml"
    if path.exists():
        return path
    return None


@pytest.fixture
def oas_3_1_simple(fixtures_dir):
    """Load simple OAS 3.1 fixture."""
    path = fixtures_dir / "oas_3_1_simple.yaml"
    if path.exists():
        return path
    return None


@pytest.fixture
def oas_batch_test(fixtures_dir):
    """Load batch test OAS fixture with multiple endpoints."""
    path = fixtures_dir / "oas_batch_test.yaml"
    if path.exists():
        return path
    return None


@pytest.fixture
def batch_test_doc(oas_batch_test):
    """Parse and return batch test OAS document."""
    return parse_oas(str(oas_batch_test))


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
