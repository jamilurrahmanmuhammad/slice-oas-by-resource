"""CSV index management for batch extraction with real-time streaming."""

import csv
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timezone

from .models import CSVIndexEntry


class CSVIndexManager:
    """Manages CSV index creation and thread-safe appending."""

    # CSV column headers (Constitution Principle V)
    HEADERS = [
        "path",
        "method",
        "summary",
        "description",
        "operation_id",
        "tags",
        "filename",
        "file_size_kb",
        "schema_count",
        "parameter_count",
        "response_codes",
        "security_required",
        "deprecated",
        "created_at",
        "output_oas_version",
    ]

    def __init__(self, csv_path: Path):
        """Initialize CSV manager.

        Args:
            csv_path: Path where CSV index will be written
        """
        self.csv_path = Path(csv_path)
        self.lock = threading.Lock()
        self._initialized = False
        self._entry_count = 0
        self._known_entries: Set[Tuple[str, str]] = set()  # (path, method) pairs

    def initialize(self, append_mode: bool = False) -> None:
        """Create CSV file with headers or prepare for append mode.

        Args:
            append_mode: If True, preserve existing entries if file exists
                        and has valid headers. If False, overwrite file.
        """
        with self.lock:
            if self._initialized:
                return

            # Append mode: check if file exists and has valid headers
            if append_mode and self.csv_path.exists():
                try:
                    with open(self.csv_path, "r", newline="") as f:
                        reader = csv.reader(f)
                        existing_headers = next(reader, None)
                        if existing_headers == self.HEADERS:
                            # Valid file exists, load existing entries for duplicate detection
                            self._load_existing_entries()
                            self._initialized = True
                            return
                except (IOError, csv.Error):
                    pass  # Fall through to create new file

            # Create new file with headers
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)

            self._entry_count = 0
            self._known_entries.clear()
            self._initialized = True

    def _load_existing_entries(self) -> None:
        """Load existing entries from CSV for duplicate detection."""
        self._known_entries.clear()
        self._entry_count = 0

        try:
            with open(self.csv_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    path = row.get("path", "")
                    method = row.get("method", "")
                    if path and method:
                        self._known_entries.add((path, method.upper()))
                        self._entry_count += 1
        except (IOError, csv.Error):
            pass  # Start fresh if file can't be read

    def has_duplicate(self, path: str, method: str) -> bool:
        """Check if path+method combination already exists in CSV.

        Args:
            path: OpenAPI path (e.g., "/users/{id}")
            method: HTTP method (e.g., "GET")

        Returns:
            True if entry already exists, False otherwise
        """
        return (path, method.upper()) in self._known_entries

    def append_entry(self, entry: CSVIndexEntry, skip_duplicates: bool = True) -> bool:
        """Append entry to CSV index (thread-safe).

        Args:
            entry: CSVIndexEntry to append
            skip_duplicates: If True, skip entries that already exist

        Returns:
            True if entry was added, False if skipped as duplicate
        """
        if not self._initialized:
            self.initialize()

        with self.lock:
            # Check for duplicate
            key = (entry.path, entry.method.upper())
            if skip_duplicates and key in self._known_entries:
                return False

            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(entry.to_csv_row())

            # Track the new entry
            self._known_entries.add(key)
            self._entry_count += 1
            return True

    @property
    def entry_count(self) -> int:
        """Return the number of entries in the CSV."""
        return self._entry_count

    def append_batch(self, entries: List[CSVIndexEntry], skip_duplicates: bool = True) -> int:
        """Append multiple entries to CSV index (thread-safe).

        Args:
            entries: List of CSVIndexEntry objects
            skip_duplicates: If True, skip entries that already exist

        Returns:
            Number of entries actually added (excluding duplicates)
        """
        if not self._initialized:
            self.initialize()

        added_count = 0
        with self.lock:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                for entry in entries:
                    key = (entry.path, entry.method.upper())
                    if skip_duplicates and key in self._known_entries:
                        continue

                    writer.writerow(entry.to_csv_row())
                    self._known_entries.add(key)
                    self._entry_count += 1
                    added_count += 1

        return added_count

    def read_entries(self) -> List[Dict[str, Any]]:
        """Read all entries from CSV index.

        Returns:
            List of dictionaries (one per row)
        """
        if not self.csv_path.exists():
            return []

        entries = []
        with open(self.csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)

        return entries


def create_csv_index_entry(
    path: str,
    method: str,
    summary: Optional[str],
    description: Optional[str],
    operation_id: Optional[str],
    tags: List[str],
    filename: str,
    file_size_kb: float,
    schema_count: int,
    parameter_count: int,
    response_codes: str,
    security_required: bool,
    deprecated: bool,
    output_oas_version: str,
) -> CSVIndexEntry:
    """Factory function for creating CSV index entries.

    Args:
        path: OpenAPI path
        method: HTTP method
        summary: Operation summary
        description: Operation description
        operation_id: Operation ID
        tags: List of tags
        filename: Output filename
        file_size_kb: File size in KB
        schema_count: Number of schemas referenced
        parameter_count: Number of parameters
        response_codes: Comma-separated response codes
        security_required: Whether security is required
        deprecated: Whether endpoint is deprecated
        output_oas_version: Output OAS version (3.0.x or 3.1.x)

    Returns:
        CSVIndexEntry instance
    """
    return CSVIndexEntry(
        path=path,
        method=method,
        summary=summary,
        description=description,
        operation_id=operation_id,
        tags=",".join(tags) if tags else "",
        filename=filename,
        file_size_kb=file_size_kb,
        schema_count=schema_count,
        parameter_count=parameter_count,
        response_codes=response_codes,
        security_required=security_required,
        deprecated=deprecated,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        output_oas_version=output_oas_version,
    )


# Metadata extraction utilities (T077)


def count_schemas(doc: Dict[str, Any]) -> int:
    """Count the number of schemas in a sliced document.

    Args:
        doc: Sliced OAS document

    Returns:
        Number of schemas in components/schemas
    """
    components = doc.get("components", {})
    schemas = components.get("schemas", {})
    return len(schemas)


def count_parameters(doc: Dict[str, Any], path: str, method: str) -> int:
    """Count parameters for an operation.

    Includes both path-level and operation-level parameters.

    Args:
        doc: OAS document (original or sliced)
        path: OpenAPI path
        method: HTTP method

    Returns:
        Total parameter count
    """
    count = 0

    paths = doc.get("paths", {})
    path_item = paths.get(path, {})

    # Path-level parameters
    path_params = path_item.get("parameters", [])
    count += len(path_params)

    # Operation-level parameters
    operation = path_item.get(method.lower(), {})
    op_params = operation.get("parameters", [])
    count += len(op_params)

    return count


def has_security_requirement(operation: Dict[str, Any], doc: Dict[str, Any]) -> bool:
    """Check if operation has security requirements.

    Checks both operation-level and global security.

    Args:
        operation: Operation object from OAS
        doc: Full OAS document (for global security)

    Returns:
        True if security is required, False otherwise
    """
    # Check operation-level security
    op_security = operation.get("security")
    if op_security is not None:
        # Empty array means no security required
        return len(op_security) > 0

    # Fall back to global security
    global_security = doc.get("security")
    if global_security is not None:
        return len(global_security) > 0

    return False


def extract_response_codes(operation: Dict[str, Any]) -> str:
    """Extract response codes from operation as comma-separated string.

    Args:
        operation: Operation object from OAS

    Returns:
        Comma-separated response codes (e.g., "200,400,404")
    """
    responses = operation.get("responses", {})
    codes = sorted(responses.keys())
    return ",".join(codes)


def extract_csv_metadata(
    doc: Dict[str, Any],
    path: str,
    method: str,
    output_path: Path,
    output_version: str,
) -> Dict[str, Any]:
    """Extract all metadata needed for CSV entry from a sliced document.

    Args:
        doc: Sliced OAS document
        path: OpenAPI path
        method: HTTP method
        output_path: Path to the output file
        output_version: Output OAS version (e.g., "3.0.x" or "3.1.x")

    Returns:
        Dictionary with all CSV column values
    """
    operation = doc.get("paths", {}).get(path, {}).get(method.lower(), {})

    # Calculate file size
    try:
        file_size_kb = round(output_path.stat().st_size / 1024, 2)
    except (OSError, IOError):
        file_size_kb = 0.0

    return {
        "path": path,
        "method": method.upper(),
        "summary": operation.get("summary", ""),
        "description": operation.get("description", ""),
        "operation_id": operation.get("operationId", ""),
        "tags": operation.get("tags", []),
        "filename": output_path.name,
        "file_size_kb": file_size_kb,
        "schema_count": count_schemas(doc),
        "parameter_count": count_parameters(doc, path, method),
        "response_codes": extract_response_codes(operation),
        "security_required": has_security_requirement(operation, doc),
        "deprecated": operation.get("deprecated", False),
        "output_oas_version": output_version,
    }
