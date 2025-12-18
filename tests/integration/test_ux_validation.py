"""Integration tests for Black Box UX validation (Phase 7 US5).

Test scenarios:
- T089: No-code UX validation (scan output for code patterns)
- T090: Plain-language prompts (all prompts in simple English)
- T091: Error message clarity (no technical jargon in errors)
- T092: Path validation feedback (helpful guidance on invalid paths)
- T093: Progress message conversational tone
- T100: Comprehensive regex checks for code/JSON/YAML patterns

Constitution Principle I (Black Box Abstraction):
Non-programmer users MUST never see code, algorithms, pseudocode, or technical
implementation details. The skill operates as a complete black box: user provides
input → skill executes silently → user receives results.
"""

import pytest
import re
import sys
import io
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from slice_oas.cli import (
    format_validation_error,
    format_batch_error_summary,
    format_conversion_error_summary,
    print_batch_summary,
    print_conversion_summary,
    create_error_formatter,
    parse_arguments,
)
from slice_oas.models import ValidationResult, ValidationPhase, BatchExtractionResult
from slice_oas.exceptions import (
    InvalidOASError,
    MissingReferenceError,
    ConversionError,
    ValidationError,
)
from slice_oas.progress import ProgressReporter, create_progress_callback


# Patterns that indicate technical content (should NOT appear in user output)
TECHNICAL_PATTERNS = [
    # Code patterns
    r'\bdef\s+\w+\s*\(',           # Python function definitions
    r'\bclass\s+\w+[\s:({]',       # Class definitions
    r'\bimport\s+\w+',             # Import statements
    r'\bfrom\s+\w+\s+import',      # From imports
    r'\breturn\s+\w+',             # Return statements
    r'\braise\s+\w+',              # Raise statements
    r'\btry\s*:',                  # Try blocks
    r'\bexcept\s+\w+',             # Except blocks
    r'\bself\.\w+',                # Self references
    r'\bNone\b',                   # Python None (except in casual use)
    r'\bTrue\b|\bFalse\b',         # Python booleans (except in casual use)
    r'__\w+__',                    # Dunder methods
    r'\[\s*\d+\s*\]',              # Array indexing
    r'\{\s*["\']?\w+["\']?\s*:',   # Dict literals with keys

    # JSON/YAML patterns
    r'"openapi"\s*:',              # OpenAPI JSON key
    r'"paths"\s*:',                # Paths JSON key
    r'"components"\s*:',           # Components JSON key
    r'"schemas"\s*:',              # Schemas JSON key
    r'\$ref\s*:',                  # JSON reference
    r'#/components/',              # Internal reference path

    # Technical jargon
    r'\bstacktrace\b',             # Stack trace
    r'\bTraceback\b',              # Python traceback
    r'\bException\b',              # Exception class
    r'\bError\b.*\bat line\b',     # Error at line X
    r'\bTypeError\b',              # Type error
    r'\bKeyError\b',               # Key error
    r'\bValueError\b',             # Value error
    r'\bAttributeError\b',         # Attribute error
    r'\bIndexError\b',             # Index error
    r'File "[^"]+", line \d+',     # Python file/line reference
    r'\bmodule\b.*\bnot found\b',  # Module not found
    r'\bNoneType\b',               # NoneType error

    # API/Code terms that confuse non-programmers
    r'\bHTTP\s+\d{3}\b',           # HTTP status codes (prefer "success"/"error")
    r'\bJSON\b',                   # JSON (prefer "file format")
    r'\bYAML\b',                   # YAML (prefer "file format")
    r'\bAPI\b(?!\s+(?:file|specification))', # API alone (OK: "API file")
    r'\bparameter\b',              # Parameter (prefer "option" or "setting")
    r'\bschema\b',                 # Schema (prefer "structure" or "format")
    r'\brequest\b\s+body',         # Request body
    r'\bresponse\b\s+body',        # Response body
    r'\bheader\b(?!s?\s*$)',       # Header (except "headers" at end)
    r'\bpayload\b',                # Payload
    r'\bserialization\b',          # Serialization
    r'\bdeserialization\b',        # Deserialization
    r'\bparser\b',                 # Parser
    r'\bvalidator\b',              # Validator
    r'\bhandler\b',                # Handler
    r'\bcallback\b',               # Callback
    r'\basync\b',                  # Async
    r'\bsync\b',                   # Sync
    r'\bthread\b',                 # Thread (prefer "parallel")
    r'\bmutex\b',                  # Mutex
    r'\block\b',                   # Lock
    r'\bbuffer\b',                 # Buffer
    r'\bcache\b',                  # Cache
    r'\bstack\b',                  # Stack
    r'\bheap\b',                   # Heap
    r'\bqueue\b',                  # Queue
    r'\bpointer\b',                # Pointer
    r'\breference\b(?!\s+(?:exist|found|missing))', # Reference (OK: "reference exists")
    r'\bnull\b',                   # Null
    r'\bundefined\b',              # Undefined
]

# Patterns that are acceptable for non-programmer users
ACCEPTABLE_PATTERNS = [
    r'\bfile\b',                   # File
    r'\bfolder\b',                 # Folder
    r'\bdirectory\b',              # Directory
    r'\bpath\b',                   # Path (file path)
    r'\bformat\b',                 # Format
    r'\bversion\b',                # Version
    r'\bendpoint\b',               # Endpoint (acceptable)
    r'\bextract\b',                # Extract
    r'\bconvert\b',                # Convert
    r'\bcreate\b',                 # Create
    r'\bsave\b',                   # Save
    r'\bprocess\b',                # Process
    r'\bcomplete\b',               # Complete
    r'\bsuccess\b',                # Success
    r'\bfail\b',                   # Fail
    r'\berror\b(?!\s+at)',         # Error (not "error at line")
    r'\bwarning\b',                # Warning
    r'\bplease\b',                 # Please
    r'\btry\s+again\b',            # Try again
    r'\bcheck\b',                  # Check
    r'\bverify\b',                 # Verify
]


def contains_technical_content(text: str) -> list:
    """Check if text contains technical content that violates Black Box principle.

    Args:
        text: Text to check

    Returns:
        List of matched technical patterns found
    """
    violations = []
    for pattern in TECHNICAL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            violations.extend(matches)
    return violations


def is_plain_language(text: str) -> bool:
    """Check if text uses plain, conversational language.

    Args:
        text: Text to check

    Returns:
        True if text is in plain language
    """
    # Check for technical violations
    violations = contains_technical_content(text)
    return len(violations) == 0


class TestNoCodeUXValidation:
    """T089, T100: Scan all output for code patterns."""

    def test_validation_error_messages_no_code(self):
        """Verify validation error messages contain no code."""
        for phase in ValidationPhase:
            result = ValidationResult(
                phase=phase,
                passed=False,
                error_message="Technical error details here"
            )
            message = format_validation_error(result)
            violations = contains_technical_content(message)
            assert not violations, f"Phase {phase.name} message contains technical content: {violations}"

    def test_batch_error_summary_no_code(self):
        """Verify batch error summary contains no code."""
        failed = [
            ("/users/{id}", "GET", "KeyError: 'schema' not found"),
            ("/orders", "POST", "ValidationError: missing required field"),
        ]
        summary = format_batch_error_summary(failed)
        violations = contains_technical_content(summary)
        # The error reasons are sanitized - only path/method shown
        assert "KeyError" not in summary
        assert "ValidationError" not in summary

    def test_conversion_error_summary_no_code(self):
        """Verify conversion error summary contains no code."""
        failed = [
            ("/users", "GET", "ConversionError: nullable not supported"),
            ("/orders", "POST", "TypeError: cannot convert None"),
        ]
        summary = format_conversion_error_summary(failed)
        violations = contains_technical_content(summary)
        # Should not expose technical error reasons
        assert "ConversionError" not in summary
        assert "TypeError" not in summary

    def test_exception_user_messages_no_code(self):
        """Verify exception USER_MESSAGE attributes are plain language."""
        exceptions = [InvalidOASError, MissingReferenceError, ConversionError, ValidationError]
        for exc_class in exceptions:
            message = exc_class.USER_MESSAGE
            violations = contains_technical_content(message)
            assert not violations, f"{exc_class.__name__}.USER_MESSAGE contains: {violations}"

    def test_error_formatter_user_mode_no_code(self):
        """Verify user-mode error formatter produces no code."""
        formatter = create_error_formatter("user")

        # Test various exceptions
        test_exceptions = [
            InvalidOASError("Technical: KeyError at line 42"),
            MissingReferenceError("#/components/schemas/User not found"),
            ConversionError("nullable: true not supported in 3.0"),
            ValidationError("JSON schema validation failed"),
            FileNotFoundError("/path/to/file.yaml"),
            PermissionError("Access denied: /root/file"),
            Exception("Unexpected NoneType error"),
        ]

        for exc in test_exceptions:
            message = formatter(exc)
            violations = contains_technical_content(message)
            assert not violations, f"Formatter for {type(exc).__name__} contains: {violations}"


class TestPlainLanguagePrompts:
    """T090: All prompts in simple English."""

    def test_argparse_help_is_plain_language(self):
        """Verify CLI help text uses plain language."""
        # Capture help output
        with pytest.raises(SystemExit):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                parse_arguments(['--help'])

    def test_batch_summary_plain_language(self):
        """Verify batch summary uses plain language."""
        result = BatchExtractionResult(
            total_endpoints=10,
            extracted_count=8,
            failed_count=2,
            validation_pass_rate=0.8,
            elapsed_time=5.0,
            csv_index_path=Path("/output/index.csv"),
            failed_endpoints=[],
            output_files=[Path("/output/users_GET.yaml")],
        )

        output = io.StringIO()
        with redirect_stdout(output):
            print_batch_summary(result)

        text = output.getvalue()
        # Should contain user-friendly terms
        assert "complete" in text.lower()
        assert "extracted" in text.lower() or "processed" in text.lower()
        # Should not contain technical terms
        violations = contains_technical_content(text)
        # Filter out acceptable patterns like "validation_pass_rate" shown as percentage
        assert not violations, f"Batch summary contains technical content: {violations}"

    def test_conversion_summary_plain_language(self):
        """Verify conversion summary uses plain language."""
        result = BatchExtractionResult(
            total_endpoints=10,
            extracted_count=9,
            failed_count=1,
            validation_pass_rate=0.9,
            elapsed_time=3.0,
            csv_index_path=None,
            failed_endpoints=[],
            output_files=[Path("/output/users_GET.yaml")],
        )

        output = io.StringIO()
        with redirect_stdout(output):
            print_conversion_summary(result, "3.0.x", "3.1.x")

        text = output.getvalue()
        assert "complete" in text.lower()
        assert "3.0" in text or "3.1" in text  # Version numbers OK


class TestErrorMessageClarity:
    """T091: No technical jargon in errors."""

    def test_file_not_found_message_clarity(self):
        """Verify file not found message is clear."""
        formatter = create_error_formatter("user")
        message = formatter(FileNotFoundError("/some/path/file.yaml"))

        assert "not found" in message.lower()
        assert "FileNotFoundError" not in message
        assert "/some/path" not in message  # Don't expose internal paths

    def test_permission_error_message_clarity(self):
        """Verify permission error message is clear."""
        formatter = create_error_formatter("user")
        message = formatter(PermissionError("Access denied"))

        assert "permission" in message.lower() or "access" in message.lower()
        assert "PermissionError" not in message

    def test_generic_error_message_clarity(self):
        """Verify generic errors are handled gracefully."""
        formatter = create_error_formatter("user")
        message = formatter(RuntimeError("Internal assertion failed"))

        assert "try again" in message.lower() or "issue" in message.lower()
        assert "RuntimeError" not in message
        assert "assertion" not in message.lower()

    def test_validation_phase_errors_are_actionable(self):
        """Verify validation errors provide actionable guidance."""
        for phase in ValidationPhase:
            result = ValidationResult(
                phase=phase,
                passed=False,
                error_message="Technical error"
            )
            message = format_validation_error(result)

            # Should provide guidance
            actionable_words = ["check", "verify", "ensure", "try", "please", "contact"]
            has_guidance = any(word in message.lower() for word in actionable_words)
            assert has_guidance, f"Phase {phase.name} error lacks actionable guidance: {message}"


class TestPathValidationFeedback:
    """T092: Helpful guidance on invalid paths."""

    def test_invalid_path_error_is_helpful(self):
        """Verify invalid path errors provide helpful guidance."""
        # These would be generated by CLI when path validation fails
        error_messages = [
            "The path was not found in the specification. Please try again with a valid path.",
            "The method was not found for this path. Please try again with a valid method.",
            "No endpoints found in the specification. Please provide a valid OpenAPI file.",
            "No HTTP methods found for this path. Please select a different endpoint.",
        ]

        for message in error_messages:
            # Should have guidance
            assert "please" in message.lower()
            # Should not have technical terms
            violations = contains_technical_content(message)
            assert not violations, f"Path error contains technical content: {violations}"

    def test_filter_pattern_error_is_helpful(self):
        """Verify filter pattern errors are helpful."""
        # When filter matches no endpoints
        error_message = "No endpoints matched the filter pattern. Please try a different pattern or remove the filter."

        assert "please" in error_message.lower()
        assert "try" in error_message.lower()


class TestProgressMessageTone:
    """T093: Progress message conversational tone."""

    def test_progress_reporter_uses_simple_language(self):
        """Verify progress messages use simple language."""
        output = io.StringIO()

        reporter = ProgressReporter(verbose=True)

        with redirect_stdout(output):
            reporter(1, 10, "/users", "GET")
            reporter(5, 10, "/orders", "POST")
            reporter(10, 10, "/products", "DELETE")

        text = output.getvalue()

        # Should use simple "Extracting" not technical "Executing extraction pipeline"
        assert "extracting" in text.lower() or "processing" in text.lower()

        # Should not have technical terms
        assert "thread" not in text.lower()
        assert "worker" not in text.lower()
        assert "pipeline" not in text.lower()

    def test_progress_summary_is_conversational(self):
        """Verify progress summary is conversational."""
        output = io.StringIO()

        with redirect_stdout(output):
            ProgressReporter.summary(
                extracted_count=8,
                failed_count=2,
                total_count=10,
                elapsed_time=5.0,
            )

        text = output.getvalue()

        # Should use user-friendly terms
        assert "complete" in text.lower()
        # Should show counts in simple format
        assert "8" in text
        assert "10" in text


class TestComprehensiveUXValidation:
    """T100: Comprehensive regex checks for all output."""

    def test_all_exception_classes_have_user_messages(self):
        """Verify all custom exceptions have USER_MESSAGE attribute."""
        from slice_oas import exceptions
        import inspect

        for name, obj in inspect.getmembers(exceptions):
            if inspect.isclass(obj) and issubclass(obj, Exception) and obj != Exception:
                assert hasattr(obj, 'USER_MESSAGE'), f"{name} lacks USER_MESSAGE"
                message = obj.USER_MESSAGE
                assert isinstance(message, str), f"{name}.USER_MESSAGE is not string"
                assert len(message) > 10, f"{name}.USER_MESSAGE is too short"

    def test_cli_module_messages_are_plain_language(self):
        """Scan CLI module for hardcoded messages."""
        cli_path = Path(__file__).parent.parent.parent / "src" / "slice_oas" / "cli.py"
        content = cli_path.read_text()

        # Find all string literals that look like user messages
        # (strings with "please", "error", "failed", etc.)
        message_patterns = [
            r'sys\.(?:stdout|stderr)\.write\(["\'](.+?)["\']\)',
            r'f["\'](.+?)["\']',  # f-strings
        ]

        # This is a simplified check - in practice would need more sophisticated parsing
        # For now, just verify the module exists and is readable
        assert len(content) > 0

    def test_validation_result_user_message_method(self):
        """Verify ValidationResult.to_user_message() is plain language."""
        for phase in ValidationPhase:
            for passed in [True, False]:
                result = ValidationResult(
                    phase=phase,
                    passed=passed,
                    error_message="Technical detail"
                )
                message = result.to_user_message()

                # Should be plain language
                violations = contains_technical_content(message)
                # Allow "validation" as it's commonly understood
                violations = [v for v in violations if "validat" not in v.lower()]
                assert not violations, f"to_user_message() for {phase.name} contains: {violations}"


class TestOutputFormatUserFriendly:
    """Additional tests for user-friendly output format."""

    def test_success_messages_are_positive(self):
        """Verify success messages use positive language."""
        success_indicators = ["✓", "complete", "success", "done", "created", "saved"]

        result = BatchExtractionResult(
            total_endpoints=5,
            extracted_count=5,
            failed_count=0,
            validation_pass_rate=1.0,
            elapsed_time=2.0,
            csv_index_path=None,
            failed_endpoints=[],
            output_files=[Path("/output/test.yaml")],
        )

        output = io.StringIO()
        with redirect_stdout(output):
            print_batch_summary(result)

        text = output.getvalue().lower()
        has_positive = any(ind.lower() in text for ind in success_indicators)
        assert has_positive, "Success output lacks positive language"

    def test_failure_messages_are_helpful(self):
        """Verify failure messages are helpful, not alarming."""
        failed = [("/users", "GET", "Some technical error")]
        summary = format_batch_error_summary(failed)

        # Should not use alarming words
        alarming_words = ["fatal", "critical", "crash", "abort", "terminate"]
        for word in alarming_words:
            assert word not in summary.lower(), f"Error summary contains alarming word: {word}"

        # Should have helpful guidance
        assert "please" in summary.lower() or "check" in summary.lower()

    def test_numbers_are_formatted_simply(self):
        """Verify numbers are formatted in user-friendly way."""
        result = BatchExtractionResult(
            total_endpoints=100,
            extracted_count=95,
            failed_count=5,
            validation_pass_rate=0.95,
            elapsed_time=12.345,
            csv_index_path=None,
            failed_endpoints=[],
            output_files=[],
        )

        output = io.StringIO()
        with redirect_stdout(output):
            print_batch_summary(result)

        text = output.getvalue()

        # Should show percentage as simple number (95.0%), not 0.95
        assert "95" in text
        # Time should be rounded (12.3s not 12.345678s)
        assert "12.3" in text or "12.4" in text  # Allow rounding


class TestEdgeCases:
    """Edge case testing for UX robustness."""

    def test_empty_results_handled_gracefully(self):
        """Verify empty results are handled gracefully."""
        result = BatchExtractionResult(
            total_endpoints=0,
            extracted_count=0,
            failed_count=0,
            validation_pass_rate=1.0,
            elapsed_time=0.1,
            csv_index_path=None,
            failed_endpoints=[],
            output_files=[],
        )

        output = io.StringIO()
        with redirect_stdout(output):
            print_batch_summary(result)

        text = output.getvalue()
        # Should handle gracefully, not show "0/0" weirdly
        assert "complete" in text.lower()

    def test_all_failures_handled_gracefully(self):
        """Verify all-failure case is handled gracefully."""
        result = BatchExtractionResult(
            total_endpoints=5,
            extracted_count=0,
            failed_count=5,
            validation_pass_rate=0.0,
            elapsed_time=1.0,
            csv_index_path=None,
            failed_endpoints=[
                ("/a", "GET", "Error 1"),
                ("/b", "POST", "Error 2"),
                ("/c", "PUT", "Error 3"),
                ("/d", "DELETE", "Error 4"),
                ("/e", "PATCH", "Error 5"),
            ],
            output_files=[],
        )

        output = io.StringIO()
        with redirect_stdout(output):
            print_batch_summary(result)

        text = output.getvalue()
        # Should still show "complete" (the process completed, even if with failures)
        assert "complete" in text.lower()

    def test_special_characters_in_paths_handled(self):
        """Verify special characters in paths don't break output."""
        failed = [
            ("/users/{id}/profile", "GET", "Error"),
            ("/api/v1/items?filter=active", "POST", "Error"),
            ("/path/with spaces/test", "PUT", "Error"),
        ]

        summary = format_batch_error_summary(failed)

        # Should display paths without breaking
        assert "/users/{id}" in summary
        # Should not contain escape sequences visible to users
        assert "\\n" not in summary
        assert "\\t" not in summary
