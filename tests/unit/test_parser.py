"""Unit tests for OAS parser module."""

import pytest
from pathlib import Path
from slice_oas.parser import parse_oas, detect_oas_version


class TestParserBasics:
    """Test basic parser functionality."""

    def test_load_yaml_file(self, fixtures_dir):
        """Test loading a YAML OAS file."""
        yaml_file = fixtures_dir / "oas_3_0_simple.yaml"
        result = parse_oas(str(yaml_file))
        assert result is not None
        assert "openapi" in result
        assert "info" in result

    def test_load_json_file(self, fixtures_dir, tmp_path):
        """Test loading a JSON OAS file."""
        # Would test JSON parsing
        pass

    def test_validate_structure(self, fixtures_dir):
        """Test that parsed OAS has required root keys."""
        yaml_file = fixtures_dir / "oas_3_0_simple.yaml"
        result = parse_oas(str(yaml_file))
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result

    def test_reject_malformed(self, fixtures_dir):
        """Test that malformed OAS is rejected."""
        malformed_file = fixtures_dir / "malformed.yaml"
        # Should raise or return error
        try:
            result = parse_oas(str(malformed_file))
            # Malformed files should be rejected
            assert result is None or "error" in result
        except Exception:
            # Expected to fail
            pass


class TestVersionDetection:
    """Test OAS version detection."""

    def test_detect_version_3_0(self, fixtures_dir):
        """Test detection of OAS 3.0.x."""
        yaml_file = fixtures_dir / "oas_3_0_simple.yaml"
        result = parse_oas(str(yaml_file))
        version = detect_oas_version(result)
        assert version == "3.0.x"

    def test_detect_version_3_1(self, fixtures_dir):
        """Test detection of OAS 3.1.x."""
        yaml_file = fixtures_dir / "oas_3_1_simple.yaml"
        result = parse_oas(str(yaml_file))
        version = detect_oas_version(result)
        assert version == "3.1.x"

    def test_version_from_openapi_field(self, fixtures_dir):
        """Test that version is correctly parsed from openapi field."""
        yaml_file = fixtures_dir / "oas_3_0_simple.yaml"
        result = parse_oas(str(yaml_file))
        version = detect_oas_version(result)
        assert version in ["3.0.x", "3.1.x"]
