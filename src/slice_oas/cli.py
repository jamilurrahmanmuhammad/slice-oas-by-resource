"""Black-box conversational CLI interface."""

import argparse
import sys
import time
from typing import Callable, Optional, List
from pathlib import Path
from slice_oas.models import ValidationResult, ValidationPhase, BatchExtractionRequest
from slice_oas.exceptions import InvalidOASError, MissingReferenceError, ConversionError, ValidationError
from slice_oas.parser import parse_oas, detect_oas_version
from slice_oas.slicer import EndpointSlicer
from slice_oas.validator import EndpointValidator
from slice_oas.generator import OASGenerator
from slice_oas.batch_processor import create_batch_processor
from slice_oas.progress import create_progress_callback


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments with conversational interface.

    Args:
        args: List of command-line arguments (defaults to sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Decompose large OpenAPI specifications into individual resource files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  slice-oas --input api.yaml
  slice-oas --input api.yaml --output-dir ./sliced --output-version 3.1.x
  slice-oas --input api.yaml --batch --filter /users
        """,
    )

    parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="Path to the OpenAPI specification file (JSON or YAML)",
        metavar="FILE"
    )

    parser.add_argument(
        "--output-dir",
        default=".",
        type=str,
        help="Directory for sliced resource files (default: current directory)",
        metavar="DIR"
    )

    parser.add_argument(
        "--output-version",
        default="auto",
        type=str,
        choices=["auto", "3.0.x", "3.1.x"],
        help="Target OpenAPI version for output files (default: auto-detect)",
        metavar="VERSION"
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all endpoints in batch mode"
    )

    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Filter endpoints by path pattern (e.g., /users) in batch mode",
        metavar="PATTERN"
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Number of parallel extraction threads in batch mode (default: 4, max: 16)",
        metavar="N"
    )

    parser.add_argument(
        "--format",
        type=str,
        default="yaml",
        choices=["yaml", "json"],
        help="Output format for extracted files (default: yaml)",
        metavar="FORMAT"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without writing files (batch mode only)"
    )

    return parser.parse_args(args)


def format_validation_error(result: ValidationResult) -> str:
    """Convert technical validation error to user-friendly message.

    Implements Principle I (Black Box): no code, JSON, YAML, or technical
    jargon exposed to users. All messages in plain language.

    Args:
        result: ValidationResult from any phase

    Returns:
        Plain-language user message
    """
    if result.passed:
        return f"Phase {result.phase.value} validation passed ✓"

    # User-friendly messages with no technical details
    messages = {
        ValidationPhase.FILE_STRUCTURE: (
            "The file format is invalid. Please check that it's a valid "
            "OpenAPI specification file."
        ),
        ValidationPhase.OPERATION_INTEGRITY: (
            "The endpoint definition is incomplete. Please verify the "
            "operation is properly defined."
        ),
        ValidationPhase.RESPONSE_INTEGRITY: (
            "The response definition has issues. Please check response "
            "codes and content types."
        ),
        ValidationPhase.REFERENCE_RESOLUTION: (
            "Some components referenced in the endpoint cannot be found. "
            "Please verify all schema references exist."
        ),
        ValidationPhase.COMPONENT_COMPLETENESS: (
            "Some required components are missing from the output. This is "
            "likely a tool issue—please contact support."
        ),
        ValidationPhase.PAYLOAD_EQUIVALENCE: (
            "The extracted endpoint doesn't match the original. Please try again."
        ),
        ValidationPhase.VERSION_VALIDATION: (
            "The output format doesn't match the requested OpenAPI version. "
            "Please try again."
        ),
    }

    return messages.get(
        result.phase,
        result.error_message or "Validation failed."
    )


def create_error_formatter(mode: str = "user") -> Callable[[Exception], str]:
    """Create an error formatter function.

    Args:
        mode: "user" for black-box messages, "debug" for technical details

    Returns:
        Callable that formats exceptions to strings
    """
    def user_formatter(exc: Exception) -> str:
        """Format exception for non-programmer users."""
        exc_type = type(exc).__name__

        # Map exception types to user-friendly messages
        user_messages = {
            "InvalidOASError": "The OpenAPI file format is not recognized.",
            "MissingReferenceError": "Some required components are missing.",
            "ConversionError": "The file could not be converted.",
            "ValidationError": "The file validation failed.",
            "FileNotFoundError": "The file was not found.",
            "PermissionError": "Permission denied accessing the file.",
        }

        return user_messages.get(
            exc_type,
            "An unexpected issue occurred. Please try again."
        )

    def debug_formatter(exc: Exception) -> str:
        """Format exception with full technical details."""
        return f"{type(exc).__name__}: {str(exc)}"

    if mode == "debug":
        return debug_formatter
    return user_formatter


def format_batch_error_summary(failed_endpoints: List[tuple]) -> str:
    """Format batch error summary for user (Principle I: Black Box).

    Args:
        failed_endpoints: List of (path, method, reason) tuples

    Returns:
        Plain-language summary without technical details
    """
    if not failed_endpoints:
        return ""

    lines = ["\nSome endpoints could not be extracted:"]
    for path, method, reason in failed_endpoints[:5]:  # Show first 5 errors
        lines.append(f"  • {method.upper()} {path}")

    if len(failed_endpoints) > 5:
        lines.append(f"  ... and {len(failed_endpoints) - 5} more")

    lines.append("\nPlease check that all paths and methods are valid.")
    return "\n".join(lines)


def print_batch_summary(result) -> None:
    """Print batch extraction summary (plain language, no technical details).

    Args:
        result: BatchExtractionResult from batch processor
    """
    sys.stdout.write("\n✓ Batch extraction complete!\n")
    sys.stdout.write(f"Extracted: {result.extracted_count}/{result.total_endpoints}\n")
    if result.failed_count > 0:
        sys.stdout.write(f"Failed: {result.failed_count}\n")
    sys.stdout.write(f"Success rate: {result.validation_pass_rate * 100:.1f}%\n")
    sys.stdout.write(f"Time: {result.elapsed_time:.1f}s\n")
    sys.stdout.write(f"Output directory: {result.output_files[0].parent if result.output_files else 'N/A'}\n")
    sys.stdout.write(f"Files created: {len(result.output_files)}\n")


def _extract_single_endpoint(args, doc: dict, oas_version: str) -> None:
    """Extract single endpoint (conversational mode).

    Args:
        args: Parsed arguments
        doc: OpenAPI document
        oas_version: Detected OAS version
    """
    # Step 1: Get endpoint path from user (conversational)
    sys.stdout.write("\nPlease specify the endpoint to extract.\n")
    sys.stdout.write("Available paths in specification:\n")
    paths = doc.get("paths", {})
    if not paths:
        sys.stderr.write(
            "No endpoints found in the specification. "
            "Please provide a valid OpenAPI file.\n"
        )
        sys.exit(1)

    # Show available paths
    for i, path in enumerate(paths.keys(), 1):
        sys.stdout.write(f"  {i}. {path}\n")

    sys.stdout.write("\nEnter the path to extract (e.g., /users/{id}): ")
    sys.stdout.flush()
    endpoint_path = sys.stdin.readline().strip()

    if not endpoint_path or endpoint_path not in paths:
        sys.stderr.write(
            "The path was not found in the specification. "
            "Please try again with a valid path.\n"
        )
        sys.exit(1)

    # Step 2: Get HTTP method from user (conversational)
    sys.stdout.write(
        f"\nAvailable methods for {endpoint_path}:\n"
    )
    path_item = paths[endpoint_path]
    methods = [m for m in path_item.keys() if m.lower() in
               ["get", "post", "put", "delete", "patch", "options", "head", "trace"]]

    if not methods:
        sys.stderr.write(
            "No HTTP methods found for this path. "
            "Please select a different endpoint.\n"
        )
        sys.exit(1)

    for i, method in enumerate(methods, 1):
        sys.stdout.write(f"  {i}. {method.upper()}\n")

    sys.stdout.write(
        f"\nEnter the HTTP method to extract (e.g., GET): "
    )
    sys.stdout.flush()
    endpoint_method = sys.stdin.readline().strip().lower()

    if endpoint_method not in methods:
        sys.stderr.write(
            "The method was not found for this path. "
            "Please try again with a valid method.\n"
        )
        sys.exit(1)

    # Step 3: Extract endpoint with reference resolution
    sys.stdout.write(
        f"\nExtracting {endpoint_method.upper()} {endpoint_path}...\n"
    )
    slicer = EndpointSlicer(doc, oas_version)
    try:
        extracted_doc = slicer.extract(endpoint_path, endpoint_method)
    except (KeyError, ValueError) as e:
        sys.stderr.write(
            "The endpoint could not be extracted. "
            "Please verify the path and method are correct.\n"
        )
        sys.exit(1)

    # Step 4: Validate extracted endpoint (7 phases)
    sys.stdout.write("Validating extracted endpoint...\n")
    validator = EndpointValidator(extracted_doc, oas_version, doc)
    validation_result = validator.validate()

    if not validation_result.passed:
        user_message = format_validation_error(validation_result)
        sys.stderr.write(f"Validation failed: {user_message}\n")
        sys.exit(1)

    sys.stdout.write("✓ Validation passed\n")

    # Step 5: Determine output format (JSON or YAML)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension based on format
    file_ext = args.format if hasattr(args, 'format') else "yaml"
    # Sanitize path for filename
    safe_path = endpoint_path.replace("{", "").replace("}", "").replace("/", "-").lstrip("-")
    output_filename = f"{safe_path}_{endpoint_method.upper()}.{file_ext}"
    output_path = output_dir / output_filename

    # Step 6: Generate output
    sys.stdout.write(f"Generating {file_ext.upper()} output...\n")
    generator = OASGenerator(extracted_doc, oas_version, file_ext)
    output_content = generator.generate()

    # Step 7: Write to file
    sys.stdout.write(f"Writing to {output_path}...\n")
    try:
        output_path.write_text(output_content)
    except (IOError, OSError) as e:
        sys.stderr.write(
            f"Could not write to output file. "
            f"Please check that the directory is writable.\n"
        )
        sys.exit(1)

    # Step 8: Report success
    sys.stdout.write(
        f"\n✓ Extraction complete!\n"
        f"Endpoint: {endpoint_method.upper()} {endpoint_path}\n"
        f"Output: {output_path}\n"
        f"Format: {file_ext.upper()}\n"
    )


def _extract_batch(args, doc: dict, oas_version: str) -> None:
    """Extract multiple endpoints in batch mode.

    Args:
        args: Parsed arguments
        doc: OpenAPI document
        oas_version: Detected OAS version
    """
    # Validate concurrency parameter
    concurrency = min(max(args.concurrency, 1), 16)  # Clamp to 1-16

    # Show what will be extracted (dry-run preview)
    if args.dry_run:
        sys.stdout.write("\n[DRY RUN] Preview of extraction:\n")

    # Create batch request
    batch_request = BatchExtractionRequest(
        input_file=Path(args.input),
        output_dir=Path(args.output_dir),
        filter_pattern=args.filter,
        filter_type="glob",  # Default to glob, could be extended later
        output_version=args.output_version,
        concurrency=concurrency,
        output_format=args.format,
        generate_csv=True,
        dry_run=args.dry_run,
    )

    # Create progress callback
    progress_callback = create_progress_callback(verbose=not args.dry_run)

    # Process batch
    sys.stdout.write(f"Starting batch extraction with {concurrency} parallel threads...\n")
    sys.stdout.flush()

    processor = create_batch_processor(batch_request, progress_callback)
    try:
        result = processor.process()
    except Exception as e:
        sys.stderr.write(f"Batch extraction failed: {str(e)}\n")
        sys.exit(1)

    # Report results
    if args.dry_run:
        sys.stdout.write(f"\n[DRY RUN] Would extract {result.extracted_count} endpoints:\n")
        if result.failed_endpoints:
            sys.stdout.write(f"Warning: {len(result.failed_endpoints)} endpoints could not be extracted\n")
    else:
        print_batch_summary(result)

        if result.failed_endpoints:
            error_summary = format_batch_error_summary(result.failed_endpoints)
            if error_summary:
                sys.stdout.write(error_summary + "\n")


def main():
    """Main CLI entry point supporting both single and batch extraction.

    Single extraction (default):
    1. Parse arguments
    2. Load and parse OAS file
    3. Request endpoint path and method (conversational)
    4. Extract with reference resolution
    5. Validate (7 phases)
    6. Generate and write output

    Batch extraction (--batch):
    1. Parse arguments including --filter, --concurrency, --format
    2. Load and parse OAS file
    3. Apply filter to get endpoints
    4. Process in parallel with ThreadPoolExecutor
    5. Report summary with success/failure counts
    """
    try:
        args = parse_arguments()

        # Validate input file exists
        input_path = Path(args.input)
        if not input_path.exists():
            sys.stderr.write(
                "The file was not found. Please check the file path "
                "and try again.\n"
            )
            sys.exit(1)

        # Parse OAS file
        sys.stdout.write(f"Reading OpenAPI specification from {args.input}...\n")
        doc = parse_oas(str(input_path))
        if not doc:
            sys.stderr.write(
                "The file format is not recognized. Please check that the file "
                "is a valid OpenAPI specification.\n"
            )
            sys.exit(1)

        # Detect OAS version
        oas_version = detect_oas_version(doc)
        if not oas_version:
            sys.stderr.write(
                "Could not detect OpenAPI version. Please ensure the file "
                "contains a valid 'openapi' field.\n"
            )
            sys.exit(1)

        sys.stdout.write(f"Detected OpenAPI version: {oas_version}\n")

        # Route to batch or single extraction
        if args.batch:
            _extract_batch(args, doc, oas_version)
        else:
            _extract_single_endpoint(args, doc, oas_version)

    except KeyboardInterrupt:
        sys.stderr.write("\nCancelled.\n")
        sys.exit(130)
    except Exception as exc:
        formatter = create_error_formatter("user")
        sys.stderr.write(f"Error: {formatter(exc)}\n")
        sys.exit(1)
