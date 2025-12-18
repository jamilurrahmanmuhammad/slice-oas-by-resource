"""Reference resolver for OAS files.

Resolves $ref dependencies with BFS traversal and circular reference detection.
Implements Constitutional Requirement III: Complete Resolution - all refs resolved, headers scanned.
"""

from typing import Dict, List, Any, Set, Optional
from collections import deque


class ReferenceResolver:
    """Resolves all $ref dependencies in an OAS endpoint.

    Uses BFS traversal with visited set for circular reference handling.
    Explicitly scans response headers for $ref (Constitutional Requirement).
    """

    def __init__(self, doc: Dict[str, Any], version: str):
        """Initialize resolver with OAS document and version.

        Args:
            doc: Parsed OAS document
            version: OAS version string (e.g., "3.0.0", "3.1.0")
        """
        self.doc = doc
        self.version = version
        self.components = doc.get("components", {})
        self.schemas = self.components.get("schemas", {})

    def resolve_endpoint_refs(self, path: str, method: str) -> List[str]:
        """Resolve all $ref dependencies for an endpoint.

        Uses BFS traversal with visited set for circular reference handling.

        Args:
            path: Endpoint path (e.g., "/users/{id}")
            method: HTTP method (GET, POST, etc.)

        Returns:
            List of resolved schema references (schema names)
        """
        # Extract endpoint operation
        paths = self.doc.get("paths", {})
        if path not in paths:
            return []

        operation = paths[path].get(method.lower())
        if not operation:
            return []

        # Collect all refs from operation using BFS
        visited = set()
        refs_to_process = deque()
        resolved_refs = []

        # Scan responses and headers for $ref (Constitutional Requirement)
        responses = operation.get("responses", {})
        self._scan_for_refs(responses, refs_to_process)

        # BFS traversal to follow transitive dependencies
        while refs_to_process:
            ref_string = refs_to_process.popleft()
            schema_name = self._extract_schema_name(ref_string)

            # Detect circular references (visited set)
            if schema_name in visited:
                continue
            visited.add(schema_name)
            resolved_refs.append(schema_name)

            # Get the schema and scan for nested refs
            if schema_name in self.schemas:
                schema = self.schemas[schema_name]
                self._scan_for_refs(schema, refs_to_process)

        return resolved_refs

    def _scan_for_refs(self, obj: Any, refs_queue: deque) -> None:
        """Recursively scan object for $ref entries.

        Explicitly scans response headers for $ref (Constitutional Requirement III).

        Args:
            obj: Object to scan (dict, list, or primitive)
            refs_queue: Queue of references found
        """
        if isinstance(obj, dict):
            # Check for $ref directly
            if "$ref" in obj:
                refs_queue.append(obj["$ref"])

            # Scan all values
            for key, value in obj.items():
                # Explicitly scan response headers (Constitutional Requirement)
                if key == "headers" and isinstance(value, dict):
                    for header_name, header_def in value.items():
                        if isinstance(header_def, dict) and "$ref" in header_def:
                            refs_queue.append(header_def["$ref"])
                        elif isinstance(header_def, dict):
                            self._scan_for_refs(header_def, refs_queue)

                self._scan_for_refs(value, refs_queue)

        elif isinstance(obj, list):
            for item in obj:
                self._scan_for_refs(item, refs_queue)

    def _extract_schema_name(self, ref_string: str) -> str:
        """Extract schema name from $ref string.

        Args:
            ref_string: Reference string (e.g., "#/components/schemas/User")

        Returns:
            Schema name (e.g., "User")
        """
        # Parse #/components/schemas/User format
        if ref_string.startswith("#/components/schemas/"):
            return ref_string.replace("#/components/schemas/", "")
        return ref_string
