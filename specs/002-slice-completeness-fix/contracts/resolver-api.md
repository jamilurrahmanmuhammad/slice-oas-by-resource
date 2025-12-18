# Internal API Contract: ReferenceResolver

**Module**: `src/slice_oas/resolver.py`
**Version**: 2.0.0 (extends existing 1.x)

## Class: ReferenceResolver

### Constructor

```python
def __init__(self, doc: Dict[str, Any], version: str) -> None:
    """Initialize resolver with OAS document and version.

    Args:
        doc: Parsed OAS document (full specification)
        version: OAS version string (e.g., "3.0.0", "3.1.0")

    Post-conditions:
        - self.doc is set to doc
        - self.version is set to version
        - self.schemas is initialized to doc["components"]["schemas"] or {}
        - self.headers is initialized to doc["components"]["headers"] or {}
        - self.parameters is initialized to doc["components"]["parameters"] or {}
        - self.responses is initialized to doc["components"]["responses"] or {}
        - self.request_bodies is initialized to doc["components"]["requestBodies"] or {}
        - self.security_schemes is initialized to doc["components"]["securitySchemes"] or {}
        - self.links is initialized to doc["components"]["links"] or {}
        - self.callbacks is initialized to doc["components"]["callbacks"] or {}
    """
```

### Public Methods

#### resolve_endpoint_refs (Modified)

```python
def resolve_endpoint_refs(self, path: str, method: str) -> ResolvedComponents:
    """Resolve all component references for an endpoint.

    Args:
        path: OpenAPI path (e.g., "/users/{id}")
        method: HTTP method (case-insensitive)

    Returns:
        ResolvedComponents containing all resolved components by type

    Raises:
        KeyError: If path or method not found in document

    Algorithm:
        1. Get operation from doc[paths][path][method]
        2. Initialize empty ResolvedComponents
        3. BFS scan for all $ref in operation
        4. For each $ref:
           a. Parse component type and name
           b. If not already resolved, add to queue
           c. Recursively scan component definition for nested refs
        5. Handle security scheme references (not $ref based)
        6. Return ResolvedComponents

    Contract:
        - All returned components exist in source document
        - Circular references handled (no infinite loops)
        - Transitive dependencies fully resolved
    """
```

#### parse_component_ref (New)

```python
def parse_component_ref(self, ref_string: str) -> Optional[Tuple[str, str]]:
    """Parse a $ref string into component type and name.

    Args:
        ref_string: The $ref value (e.g., "#/components/headers/X-Rate-Limit")

    Returns:
        Tuple of (component_type, component_name) or None if not a component ref

    Examples:
        "#/components/schemas/User" -> ("schemas", "User")
        "#/components/headers/X-Rate-Limit" -> ("headers", "X-Rate-Limit")
        "#/components/parameters/userId" -> ("parameters", "userId")
        "#/definitions/User" -> None (not OAS 3.x format)
        "https://example.com/schemas/User" -> None (external ref)
    """
```

#### get_component (New)

```python
def get_component(self, component_type: str, name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a component definition by type and name.

    Args:
        component_type: One of: schemas, headers, parameters, responses,
                        requestBodies, securitySchemes, links, callbacks
        name: Component name

    Returns:
        Component definition dict, or None if not found

    Contract:
        - Returns deepcopy of original (no mutation of source)
    """
```

#### resolve_security_schemes (New)

```python
def resolve_security_schemes(self, operation: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve security scheme references for an operation.

    Args:
        operation: The operation object from OAS

    Returns:
        Dict of security scheme name -> definition

    Algorithm:
        1. Check operation["security"] (operation-level)
        2. If not present, check doc["security"] (global)
        3. For each security requirement, extract scheme names
        4. Look up each scheme in components/securitySchemes
        5. Return resolved schemes

    Contract:
        - Empty security array means no security (don't inherit global)
        - Missing security key means inherit global
    """
```

### Private Methods

#### _scan_for_refs (Modified)

```python
def _scan_for_refs(self, obj: Any, visited: Set[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Recursively scan object for $ref entries.

    Args:
        obj: Any JSON-compatible object to scan
        visited: Set of (component_type, component_name) already processed

    Returns:
        List of (component_type, component_name) tuples found

    Contract:
        - Handles nested dicts and lists
        - Ignores non-component refs (external, JSON Pointer to non-components)
        - Does not mutate visited set (caller manages)
    """
```

## Error Handling

| Error | Condition | Response |
|-------|-----------|----------|
| `KeyError` | Path not in document | Raised with path in message |
| `KeyError` | Method not on path | Raised with method and path |
| `ValueError` | Invalid component type | Log warning, skip ref |

## Backward Compatibility

- Existing `resolve_endpoint_refs()` signature unchanged (return type extended)
- Existing `schemas` attribute preserved
- New attributes added for other component types
