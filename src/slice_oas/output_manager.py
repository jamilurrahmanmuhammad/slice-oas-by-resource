"""Output file management with atomic operations and path sanitization."""

import tempfile
import re
from pathlib import Path
from typing import Union


def sanitize_path(path: str) -> str:
    """Convert OpenAPI path to safe filename.

    Examples:
        "/users/{id}" -> "users-id"
        "/api/v1/products/{id}/reviews" -> "api-v1-products-id-reviews"
        "/users" -> "users"

    Args:
        path: OpenAPI path string

    Returns:
        Sanitized filename (alphanumeric + hyphens only)
    """
    # Remove leading slash
    if path.startswith("/"):
        path = path[1:]

    # Replace {param} with -param-
    path = re.sub(r"\{([^}]+)\}", r"-\1", path)

    # Replace / with -
    path = path.replace("/", "-")

    # Replace . with -
    path = path.replace(".", "-")

    # Remove consecutive hyphens
    path = re.sub(r"-+", "-", path)

    # Remove leading/trailing hyphens
    path = path.strip("-")

    # Convert to lowercase for consistency
    path = path.lower()

    # Ensure non-empty
    return path or "root"


def write_output_file(output_path: Union[Path, str], content: str) -> None:
    """Write content to file with atomic operations.

    Uses temp file + rename pattern to ensure atomic writes:
    1. Write to temporary file in same directory
    2. Rename temp file to target path (atomic on most filesystems)

    Args:
        output_path: Target file path
        content: File content to write
    """
    output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file in same directory (ensures same filesystem for atomic rename)
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=output_path.parent,
        delete=False,
        suffix=output_path.suffix,
    ) as tmp_file:
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    # Atomic rename
    try:
        tmp_path.replace(output_path)
    except Exception as e:
        # Clean up temp file if rename fails
        if tmp_path.exists():
            tmp_path.unlink()
        raise IOError(f"Failed to write output file: {output_path}") from e


def validate_output_dir(output_dir: Union[Path, str]) -> None:
    """Validate and create output directory.

    Args:
        output_dir: Directory path

    Raises:
        IOError: If directory cannot be created or is not writable
    """
    output_dir = Path(output_dir)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Test writability
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        raise IOError(f"Output directory {output_dir} is not writable") from e
