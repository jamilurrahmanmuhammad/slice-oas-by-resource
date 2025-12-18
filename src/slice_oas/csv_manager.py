"""CSV index management for batch extraction with real-time streaming."""

import csv
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import CSVIndexEntry


class CSVIndexManager:
    """Manages CSV index creation and thread-safe appending."""

    # CSV column headers
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

    def initialize(self) -> None:
        """Create CSV file with headers.

        Must be called before appending entries.
        """
        with self.lock:
            if self._initialized:
                return

            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)

            self._initialized = True

    def append_entry(self, entry: CSVIndexEntry) -> None:
        """Append entry to CSV index (thread-safe).

        Args:
            entry: CSVIndexEntry to append
        """
        if not self._initialized:
            self.initialize()

        with self.lock:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(entry.to_csv_row())

    def append_batch(self, entries: List[CSVIndexEntry]) -> None:
        """Append multiple entries to CSV index (thread-safe).

        Args:
            entries: List of CSVIndexEntry objects
        """
        if not self._initialized:
            self.initialize()

        with self.lock:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                for entry in entries:
                    writer.writerow(entry.to_csv_row())

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
        created_at=datetime.utcnow().isoformat() + "Z",
        output_oas_version=output_oas_version,
    )
