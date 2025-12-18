"""Endpoint slicer for extracting single resources with dependencies.

Orchestrates reference resolution, validation, and output generation.
"""

from typing import Dict, Any, Set
from copy import deepcopy
from slice_oas.resolver import ReferenceResolver


class EndpointSlicer:
    """Extracts a single endpoint with all resolved dependencies."""

    def __init__(self, doc: Dict[str, Any], version: str):
        """Initialize slicer with OAS document and version.

        Args:
            doc: Parsed OAS document
            version: OAS version string
        """
        self.doc = doc
        self.version = version
        self.resolver = ReferenceResolver(doc, version)

    def extract(self, path: str, method: str) -> Dict[str, Any]:
        """Extract single endpoint with all dependencies.

        Args:
            path: Endpoint path (e.g., "/users/{id}")
            method: HTTP method (GET, POST, etc.)

        Returns:
            Standalone OAS document with just this endpoint

        Raises:
            KeyError: If endpoint or method not found
            ValueError: If extraction fails
        """
        # Validate endpoint and method exist
        paths = self.doc.get("paths", {})
        if path not in paths:
            raise KeyError(f"Path not found: {path}")

        path_item = paths[path]
        method_lower = method.lower()
        if method_lower not in path_item:
            raise KeyError(f"Method not found: {method_lower} for {path}")

        # Create standalone OAS document
        extracted = {
            "openapi": self.doc.get("openapi", "3.0.0"),
            "info": deepcopy(self.doc.get("info", {"title": "Extracted", "version": "1.0.0"})),
            "paths": {
                path: {
                    method_lower: deepcopy(path_item[method_lower])
                }
            }
        }

        # Resolve all reference dependencies
        resolved_schema_names = self.resolver.resolve_endpoint_refs(path, method)

        # Include resolved components
        if resolved_schema_names or self.resolver.schemas:
            extracted["components"] = {"schemas": {}}
            for schema_name in resolved_schema_names:
                if schema_name in self.resolver.schemas:
                    extracted["components"]["schemas"][schema_name] = deepcopy(
                        self.resolver.schemas[schema_name]
                    )

        return extracted
