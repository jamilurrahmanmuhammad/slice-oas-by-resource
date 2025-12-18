"""Endpoint slicer for extracting single resources with dependencies.

Orchestrates reference resolution, validation, and output generation.
Supports all 8 OpenAPI component types per Constitutional Requirement III.
"""

from typing import Dict, Any, Set
from copy import deepcopy
from slice_oas.resolver import ReferenceResolver
from slice_oas.models import ResolvedComponents


class EndpointSlicer:
    """Extracts a single endpoint with all resolved dependencies.

    Resolves and includes all 8 OpenAPI component types:
    schemas, headers, parameters, responses, requestBodies,
    securitySchemes, links, callbacks.
    """

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
            Standalone OAS document with just this endpoint and ALL
            resolved component types (not just schemas)

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

        # Include path-level parameters if present
        if "parameters" in path_item:
            extracted["paths"][path]["parameters"] = deepcopy(path_item["parameters"])

        # Resolve ALL component references (not just schemas)
        resolved = self.resolver.resolve_all_refs(path, method)

        # Build components section with ALL resolved types (T017)
        components = self._build_components_section(resolved)
        if components:
            extracted["components"] = components

        return extracted

    def _build_components_section(
        self,
        resolved: ResolvedComponents
    ) -> Dict[str, Dict[str, Any]]:
        """Build the components section from resolved components.

        Args:
            resolved: ResolvedComponents from resolver

        Returns:
            Dict suitable for extracted["components"], only including non-empty sections
        """
        return resolved.to_components_dict()
