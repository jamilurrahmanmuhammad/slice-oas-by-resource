# Internal API Contract: EndpointSlicer

**Module**: `src/slice_oas/slicer.py`
**Version**: 2.0.0 (extends existing 1.x)

## Class: EndpointSlicer

### Constructor (Unchanged)

```python
def __init__(self, doc: Dict[str, Any], version: str) -> None:
    """Initialize slicer with OAS document and version.

    Args:
        doc: Parsed OAS document
        version: OAS version string
    """
```

### Public Methods

#### extract (Modified)

```python
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

    Algorithm (MODIFIED):
        1. Validate endpoint and method exist
        2. Create base extracted document structure:
           - openapi: version from source
           - info: deepcopy from source
           - paths: {path: {method: operation}}
        3. Call resolver.resolve_endpoint_refs(path, method)
        4. Build components section with ALL resolved component types:
           - schemas (existing)
           - headers (NEW)
           - parameters (NEW)
           - responses (NEW)
           - requestBodies (NEW)
           - securitySchemes (NEW)
           - links (NEW)
           - callbacks (NEW)
        5. Only include component sections that have entries
        6. Return complete extracted document

    Contract (MODIFIED):
        - Output MUST include ALL component types referenced by endpoint
        - NOT just schemas (previous behavior)
        - Empty component types MUST be omitted (no empty dicts)
    """
```

### Private Methods (New)

#### _build_components_section (New)

```python
def _build_components_section(
    self,
    resolved: ResolvedComponents
) -> Dict[str, Dict[str, Any]]:
    """Build the components section from resolved components.

    Args:
        resolved: ResolvedComponents from resolver

    Returns:
        Dict suitable for extracted["components"]

    Contract:
        - Only includes non-empty component types
        - Component types use correct OAS key names:
          schemas, headers, parameters, responses,
          requestBodies, securitySchemes, links, callbacks
        - All values are deepcopied
    """
```

## Output Document Structure

### Before (v1.x - Broken)

```yaml
openapi: "3.0.0"
info: {...}
paths:
  /users/{id}:
    get: {...}
components:
  schemas:          # Only schemas included
    User: {...}
  # MISSING: headers, parameters, responses, etc.
```

### After (v2.0 - Fixed)

```yaml
openapi: "3.0.0"
info: {...}
paths:
  /users/{id}:
    get: {...}
components:
  schemas:          # Always included if referenced
    User: {...}
  headers:          # NEW: Included if referenced
    X-Rate-Limit: {...}
  parameters:       # NEW: Included if referenced
    userId: {...}
  responses:        # NEW: Included if referenced
    NotFound: {...}
  requestBodies:    # NEW: Included if referenced
    CreateUser: {...}
  securitySchemes:  # NEW: Included if referenced
    api_key: {...}
  links:            # NEW: Included if referenced
    GetUserById: {...}
  callbacks:        # NEW: Included if referenced
    onEvent: {...}
```

## Component Type Mapping

| Resolver Attribute | OAS Key | Notes |
|-------------------|---------|-------|
| `schemas` | `schemas` | Existing |
| `headers` | `headers` | NEW |
| `parameters` | `parameters` | NEW |
| `responses` | `responses` | NEW |
| `request_bodies` | `requestBodies` | NEW (note camelCase in OAS) |
| `security_schemes` | `securitySchemes` | NEW (note camelCase in OAS) |
| `links` | `links` | NEW |
| `callbacks` | `callbacks` | NEW |

## Backward Compatibility

- Constructor signature unchanged
- extract() return type unchanged (still Dict[str, Any])
- Output structure is a superset of previous output
- Existing tests expecting only schemas will pass (schemas still included)
- New tests verify additional component types
