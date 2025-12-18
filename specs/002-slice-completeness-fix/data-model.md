# Data Model: Complete Reference Resolution Fix

**Feature**: 002-slice-completeness-fix
**Date**: 2025-12-18

## Entities

### ComponentReference

Represents a parsed `$ref` pointer to an OpenAPI component.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `ref_string` | `str` | Original `$ref` value | Must match `#/components/{type}/{name}` |
| `component_type` | `ComponentType` | Type of component | One of 8 valid types |
| `component_name` | `str` | Name of the component | Non-empty string |
| `resolved` | `bool` | Whether successfully resolved | Default: False |

**Validation Rules**:
- `ref_string` must start with `#/components/`
- `component_type` must be valid OpenAPI 3.x type
- `component_name` cannot contain `/` characters

---

### ComponentType (Enum)

Enumeration of valid OpenAPI 3.x component types.

| Value | Description |
|-------|-------------|
| `SCHEMAS` | Data structure definitions |
| `HEADERS` | Response header definitions |
| `PARAMETERS` | Reusable parameter definitions |
| `RESPONSES` | Reusable response definitions |
| `REQUEST_BODIES` | Reusable request body definitions |
| `SECURITY_SCHEMES` | Authentication/authorization definitions |
| `LINKS` | Links to related operations |
| `CALLBACKS` | Callback definitions for webhooks |

**String Mappings**:
```
schemas -> SCHEMAS
headers -> HEADERS
parameters -> PARAMETERS
responses -> RESPONSES
requestBodies -> REQUEST_BODIES
securitySchemes -> SECURITY_SCHEMES
links -> LINKS
callbacks -> CALLBACKS
```

---

### ResolvedComponents

Collection of all resolved components organized by type.

| Field | Type | Description |
|-------|------|-------------|
| `schemas` | `Dict[str, Any]` | Resolved schema definitions |
| `headers` | `Dict[str, Any]` | Resolved header definitions |
| `parameters` | `Dict[str, Any]` | Resolved parameter definitions |
| `responses` | `Dict[str, Any]` | Resolved response definitions |
| `request_bodies` | `Dict[str, Any]` | Resolved request body definitions |
| `security_schemes` | `Dict[str, Any]` | Resolved security scheme definitions |
| `links` | `Dict[str, Any]` | Resolved link definitions |
| `callbacks` | `Dict[str, Any]` | Resolved callback definitions |

**Methods**:
- `add(component_type, name, definition)` - Add a resolved component
- `has(component_type, name)` - Check if component already resolved
- `get(component_type, name)` - Retrieve resolved component
- `to_components_dict()` - Convert to OpenAPI `components` structure
- `is_empty()` - Check if no components resolved

---

### ValidationResult

Result of a single validation phase.

| Field | Type | Description |
|-------|------|-------------|
| `phase` | `ValidationPhase` | Which phase ran |
| `passed` | `bool` | Whether validation passed |
| `error_message` | `Optional[str]` | Error details if failed |
| `missing_refs` | `List[str]` | List of unresolved refs (Phase 4/6) |

---

### PayloadEquivalenceResult (New)

Specific result for Phase 6 validation.

| Field | Type | Description |
|-------|------|-------------|
| `passed` | `bool` | All refs resolve correctly |
| `missing_components` | `List[ComponentReference]` | Components in refs but not in output |
| `total_refs_checked` | `int` | Total number of refs validated |

---

## Relationships

```
┌─────────────────┐       ┌──────────────────┐
│ ReferenceResolver│──────▶│ ResolvedComponents│
└─────────────────┘       └──────────────────┘
        │                          │
        │ scans                    │ contains
        ▼                          ▼
┌─────────────────┐       ┌──────────────────┐
│ComponentReference│       │   Component      │
│  (parsed ref)   │       │  (definition)    │
└─────────────────┘       └──────────────────┘
        │
        │ typed as
        ▼
┌─────────────────┐
│  ComponentType  │
│    (enum)       │
└─────────────────┘
```

---

## State Transitions

### ComponentReference Lifecycle

```
[DISCOVERED] ──parse──▶ [PARSED] ──resolve──▶ [RESOLVED]
                             │
                             │ (if not found)
                             ▼
                        [UNRESOLVED] ──▶ ValidationError
```

### Resolution Process State

```
[START] ──▶ [SCANNING] ──▶ [RESOLVING] ──▶ [COMPLETE]
                │               │
                │ (circular)    │ (missing)
                ▼               ▼
           [SKIPPED]      [FAILED]
```

---

## Data Volume Assumptions

| Metric | Expected Range | Design Impact |
|--------|----------------|---------------|
| Components per type | 0-500 | Dict storage sufficient |
| Refs per operation | 0-50 | Linear scan acceptable |
| Transitive depth | 1-10 levels | BFS with visited set |
| Total components | 0-2000 | In-memory processing OK |

---

## Constraints

1. **Immutability**: Resolved components are deepcopied from source; no mutation of original spec
2. **Uniqueness**: Each (component_type, component_name) pair appears at most once in ResolvedComponents
3. **Completeness**: If a component is referenced, it must be resolved or validation fails
4. **Ordering**: Components are stored in insertion order (Python dict maintains order)
