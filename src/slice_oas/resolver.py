"""Reference resolver for OAS files.

Resolves $ref dependencies with BFS traversal and circular reference detection.
Implements Constitutional Requirement III: Complete Resolution - all refs resolved, headers scanned.

Supports all 8 OpenAPI 3.x component types:
- schemas, headers, parameters, responses, requestBodies, securitySchemes, links, callbacks
"""

from typing import Dict, List, Any, Set, Optional, Tuple
from collections import deque
from copy import deepcopy

from slice_oas.models import ComponentType, ResolvedComponents


class ReferenceResolver:
    """Resolves all $ref dependencies in an OAS endpoint.

    Uses BFS traversal with visited set for circular reference handling.
    Supports all 8 OpenAPI component types per Constitutional Requirement III.
    """

    def __init__(self, doc: Dict[str, Any], version: str):
        """Initialize resolver with OAS document and version.

        Args:
            doc: Parsed OAS document
            version: OAS version string (e.g., "3.0.0", "3.1.0")

        Post-conditions:
            - All 8 component type attributes initialized from doc
        """
        self.doc = doc
        self.version = version
        self.components = doc.get("components", {})

        # Initialize all 8 component types (T015)
        self.schemas = self.components.get("schemas", {})
        self.headers = self.components.get("headers", {})
        self.parameters = self.components.get("parameters", {})
        self.responses = self.components.get("responses", {})
        self.request_bodies = self.components.get("requestBodies", {})
        self.security_schemes = self.components.get("securitySchemes", {})
        self.links = self.components.get("links", {})
        self.callbacks = self.components.get("callbacks", {})

    def resolve_endpoint_refs(self, path: str, method: str) -> List[str]:
        """Resolve all $ref dependencies for an endpoint (legacy schema-only).

        DEPRECATED: Use resolve_all_refs() for complete component resolution.

        Args:
            path: Endpoint path (e.g., "/users/{id}")
            method: HTTP method (GET, POST, etc.)

        Returns:
            List of resolved schema references (schema names only)
        """
        resolved = self.resolve_all_refs(path, method)
        return list(resolved.schemas.keys())

    def resolve_all_refs(self, path: str, method: str) -> ResolvedComponents:
        """Resolve all component references for an endpoint.

        Uses BFS traversal with visited set for circular reference handling.
        Resolves ALL 8 component types per Constitutional Requirement III.

        Args:
            path: Endpoint path (e.g., "/users/{id}")
            method: HTTP method (case-insensitive)

        Returns:
            ResolvedComponents containing all resolved components by type

        Raises:
            KeyError: If path or method not found in document
        """
        # Extract endpoint operation
        paths = self.doc.get("paths", {})
        if path not in paths:
            raise KeyError(f"Path not found: {path}")

        path_item = paths[path]
        method_lower = method.lower()
        if method_lower not in path_item:
            raise KeyError(f"Method not found: {method_lower} for {path}")

        operation = path_item[method_lower]

        # Initialize result and tracking
        resolved = ResolvedComponents()
        # Use (component_type, component_name) tuple for visited set (T014)
        visited: Set[Tuple[str, str]] = set()
        refs_to_process: deque = deque()

        # Scan path-level parameters
        path_params = path_item.get("parameters", [])
        self._scan_for_refs(path_params, refs_to_process)

        # Scan operation for all refs
        self._scan_for_refs(operation, refs_to_process)

        # Resolve security schemes (name-based, not $ref)
        self._resolve_security_schemes(operation, resolved, visited)

        # BFS traversal to follow transitive dependencies
        while refs_to_process:
            ref_string = refs_to_process.popleft()
            parsed = self.parse_component_ref(ref_string)

            if parsed is None:
                continue

            component_type, component_name = parsed

            # Detect circular references using (type, name) tuple
            visit_key = (component_type.value, component_name)
            if visit_key in visited:
                continue
            visited.add(visit_key)

            # Get component definition and add to resolved set
            component_def = self.get_component(component_type, component_name)
            if component_def is not None:
                resolved.add(component_type, component_name, deepcopy(component_def))
                # Scan component for nested refs
                self._scan_for_refs(component_def, refs_to_process)

        return resolved

    def parse_component_ref(self, ref_string: str) -> Optional[Tuple[ComponentType, str]]:
        """Parse a $ref string into component type and name.

        Args:
            ref_string: The $ref value (e.g., "#/components/headers/X-Rate-Limit")

        Returns:
            Tuple of (ComponentType, component_name) or None if not a component ref
        """
        if not ref_string.startswith("#/components/"):
            return None

        parts = ref_string.split("/")
        if len(parts) < 4:
            return None

        type_str = parts[2]
        component_name = "/".join(parts[3:])  # Handle names with slashes

        component_type = ComponentType.from_ref_path(ref_string)
        if component_type is None:
            return None

        return (component_type, component_name)

    def get_component(self, component_type: ComponentType, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a component definition by type and name.

        Args:
            component_type: One of the 8 component types
            name: Component name

        Returns:
            Component definition dict, or None if not found
        """
        type_to_attr = {
            ComponentType.SCHEMAS: self.schemas,
            ComponentType.HEADERS: self.headers,
            ComponentType.PARAMETERS: self.parameters,
            ComponentType.RESPONSES: self.responses,
            ComponentType.REQUEST_BODIES: self.request_bodies,
            ComponentType.SECURITY_SCHEMES: self.security_schemes,
            ComponentType.LINKS: self.links,
            ComponentType.CALLBACKS: self.callbacks,
        }
        return type_to_attr.get(component_type, {}).get(name)

    def resolve_security_schemes(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve security scheme references for an operation.

        Security schemes are referenced by name (not $ref) in the security array.

        Args:
            operation: The operation object from OAS

        Returns:
            Dict of security scheme name -> definition
        """
        result = {}
        resolved = ResolvedComponents()
        visited: Set[Tuple[str, str]] = set()
        self._resolve_security_schemes(operation, resolved, visited)
        return resolved.security_schemes

    def _resolve_security_schemes(
        self,
        operation: Dict[str, Any],
        resolved: ResolvedComponents,
        visited: Set[Tuple[str, str]]
    ) -> None:
        """Internal: Resolve security schemes for operation.

        Handles both operation-level and global security requirements.
        Empty security array means no security (don't inherit global).

        Args:
            operation: The operation object
            resolved: ResolvedComponents to add schemes to
            visited: Visited set to prevent duplicates
        """
        # Check operation-level security first
        security = operation.get("security")

        # If operation has explicit security (even empty array), use it
        if security is None:
            # Inherit global security
            security = self.doc.get("security", [])

        # Empty array means explicitly no security
        if not security:
            return

        # Extract scheme names from security requirements
        for security_req in security:
            if isinstance(security_req, dict):
                for scheme_name in security_req.keys():
                    visit_key = (ComponentType.SECURITY_SCHEMES.value, scheme_name)
                    if visit_key in visited:
                        continue
                    visited.add(visit_key)

                    if scheme_name in self.security_schemes:
                        resolved.add(
                            ComponentType.SECURITY_SCHEMES,
                            scheme_name,
                            deepcopy(self.security_schemes[scheme_name])
                        )

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
