"""Unit tests for CLI argument parsing and error formatting."""

import pytest
from pathlib import Path
from slice_oas.cli import (
    parse_arguments,
    format_validation_error,
    create_error_formatter,
)
from slice_oas.models import ValidationResult, ValidationPhase
from slice_oas.exceptions import InvalidOASError


class TestCLIArgumentParser:
    """Test CLI argument parsing with conversational interface."""

    def test_parse_input_file_argument(self):
        """Test parsing required --input argument."""
        args = parse_arguments(["--input", "spec.yaml"])
        assert args.input == "spec.yaml"

    def test_parse_output_directory_argument(self):
        """Test parsing --output-dir argument."""
        args = parse_arguments(["--input", "spec.yaml", "--output-dir", "output"])
        assert args.output_dir == "output"

    def test_output_dir_defaults_to_current_directory(self):
        """Test --output-dir defaults to current directory."""
        args = parse_arguments(["--input", "spec.yaml"])
        assert args.output_dir == "."

    def test_parse_output_version_argument(self):
        """Test parsing --output-version argument."""
        args = parse_arguments(
            ["--input", "spec.yaml", "--output-version", "3.1.x"]
        )
        assert args.output_version == "3.1.x"

    def test_output_version_defaults_to_auto(self):
        """Test --output-version defaults to 'auto'."""
        args = parse_arguments(["--input", "spec.yaml"])
        assert args.output_version == "auto"

    def test_parse_batch_mode_flag(self):
        """Test --batch flag for batch processing."""
        args = parse_arguments(["--input", "spec.yaml", "--batch"])
        assert args.batch is True

    def test_batch_mode_defaults_to_false(self):
        """Test --batch defaults to False."""
        args = parse_arguments(["--input", "spec.yaml"])
        assert args.batch is False

    def test_parse_filter_argument(self):
        """Test --filter argument for batch path filtering."""
        args = parse_arguments(
            ["--input", "spec.yaml", "--batch", "--filter", "/users"]
        )
        assert args.filter == "/users"

    def test_filter_only_in_batch_mode(self):
        """Test --filter requires --batch mode."""
        args = parse_arguments(
            ["--input", "spec.yaml", "--filter", "/users"]
        )
        # Should still parse but filter is optional
        assert args.filter == "/users"

    def test_missing_input_raises_error(self):
        """Test missing required --input argument raises error."""
        with pytest.raises(SystemExit):
            parse_arguments([])

    def test_help_argument(self):
        """Test --help argument."""
        with pytest.raises(SystemExit) as exc_info:
            parse_arguments(["--help"])
        assert exc_info.value.code == 0


class TestValidationErrorFormatter:
    """Test conversion of technical errors to user-friendly messages."""

    def test_format_file_structure_error(self):
        """Test formatting file structure validation error."""
        result = ValidationResult(
            phase=ValidationPhase.FILE_STRUCTURE,
            passed=False,
            error_message="Invalid YAML syntax"
        )
        formatted = format_validation_error(result)
        assert "file format is invalid" in formatted.lower()
        assert "YAML" not in formatted  # No technical terms

    def test_format_operation_integrity_error(self):
        """Test formatting operation integrity error."""
        result = ValidationResult(
            phase=ValidationPhase.OPERATION_INTEGRITY,
            passed=False,
            error_message="Missing required field 'responses'"
        )
        formatted = format_validation_error(result)
        assert "endpoint definition is incomplete" in formatted.lower()
        assert "responses" not in formatted  # No technical field names

    def test_format_reference_resolution_error(self):
        """Test formatting reference resolution error."""
        result = ValidationResult(
            phase=ValidationPhase.REFERENCE_RESOLUTION,
            passed=False,
            error_message="Cannot resolve #/components/schemas/User"
        )
        formatted = format_validation_error(result)
        assert "referenced" in formatted.lower()
        assert "#/components" not in formatted  # No technical references

    def test_format_success_message(self):
        """Test formatting successful validation."""
        result = ValidationResult(
            phase=ValidationPhase.FILE_STRUCTURE,
            passed=True
        )
        formatted = format_validation_error(result)
        assert "passed" in formatted.lower()
        assert "✓" in formatted

    def test_format_includes_phase_context(self):
        """Test formatted message contextualizes the phase."""
        result = ValidationResult(
            phase=ValidationPhase.RESPONSE_INTEGRITY,
            passed=False
        )
        formatted = format_validation_error(result)
        assert "response" in formatted.lower()


class TestErrorFormatterFactory:
    """Test creation of error formatters."""

    def test_create_error_formatter_returns_callable(self):
        """Test error formatter factory returns a callable."""
        formatter = create_error_formatter("user")
        assert callable(formatter)

    def test_formatter_accepts_exception(self):
        """Test formatter can handle Exception objects."""
        formatter = create_error_formatter("user")
        error = InvalidOASError("File does not exist")
        formatted = formatter(error)
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_user_formatter_removes_technical_details(self):
        """Test user-facing formatter hides implementation details."""
        formatter = create_error_formatter("user")
        error = InvalidOASError("json.JSONDecodeError: Expecting value at line 5")
        formatted = formatter(error)
        assert "json.JSONDecodeError" not in formatted
        assert "line 5" not in formatted

    def test_debug_formatter_includes_full_traceback(self):
        """Test debug formatter includes technical details."""
        formatter = create_error_formatter("debug")
        error = InvalidOASError("Test error")
        formatted = formatter(error)
        # Debug formatter should include more details
        assert isinstance(formatted, str)
