# Research: Complete Reference Resolution Fix

**Feature**: 002-slice-completeness-fix
**Date**: 2025-12-18
**Status**: Complete

## Research Questions

### RQ1: How should component types be classified from $ref strings?

**Decision**: Parse `#/components/{type}/{name}` pattern using regex

**Rationale**: OpenAPI 3.x defines a fixed set of component types. The `$ref` format is standardized, making regex parsing reliable and performant.

**Pattern**:
```python
COMPONENT_REF_PATTERN = r'^#/components/(schemas|headers|parameters|responses|requestBodies|securitySchemes|links|callbacks)/(.+)$'
```

**Alternatives considered**:
1. String split on `/` - Rejected: Less robust, doesn't validate format
2. JSON Pointer library - Rejected: Over-engineered for this use case
3. Hard-coded prefix checks - Rejected: Repetitive, error-prone

---

### RQ2: How should resolved components be tracked across types?

**Decision**: Dictionary of dictionaries, keyed by component type

**Rationale**: Allows O(1) lookup and maintains separation between types. Easy to iterate when building output.

**Data Structure**:
```python
resolved_components = {
    "schemas": {"User": {...}, "Error": {...}},
    "headers": {"X-Rate-Limit": {...}},
    "parameters": {"userId": {...}},
    "responses": {"NotFound": {...}},
    "requestBodies": {"CreateUser": {...}},
    "securitySchemes": {"api_key": {...}},
    "links": {"GetUserById": {...}},
    "callbacks": {"onEvent": {...}},
}
```

**Alternatives considered**:
1. Flat dictionary with type prefixes - Rejected: Harder to iterate by type
2. Named tuples - Rejected: More complex, no real benefit
3. Pydantic models - Considered, may use for validation but dict sufficient for storage

---

### RQ3: How should circular references across component types be handled?

**Decision**: Extend visited set key to include component type

**Rationale**: A schema named "User" and a response named "User" are different components. The visited set must distinguish them.

**Implementation**:
```python
# Current (broken for cross-type)
visited = {"User", "Error"}

# Fixed
visited = {("schemas", "User"), ("headers", "X-Rate-Limit"), ("responses", "User")}
```

**Alternatives considered**:
1. Separate visited sets per type - Rejected: More complex, same result
2. Full ref path as key - Rejected: Redundant with tuple approach

---

### RQ4: How should Phase 6 (payload equivalence) validation work?

**Decision**: Extract all `$ref` from child, verify each exists in parent and child has the component

**Rationale**: Simple, deterministic, and catches the exact failure mode (missing components in output).

**Algorithm**:
```
1. Collect all $ref strings from extracted document
2. For each $ref:
   a. Parse component type and name
   b. Verify component exists in extracted document's components
   c. If missing, fail with specific error message
3. If all refs resolve, pass
```

**Alternatives considered**:
1. Deep structural comparison - Rejected: Over-complex, not required by spec
2. Hash comparison - Rejected: Doesn't provide useful error messages
3. JSON diff - Rejected: Too verbose, not actionable

---

### RQ5: Where should CSV generation hook be added for single extractions?

**Decision**: Add to CLI `extract` command after successful extraction and validation

**Rationale**: Minimal change, follows existing pattern from batch processor.

**Implementation Location**: `cli.py` in the `extract_single()` or equivalent function, after `validator.validate()` succeeds.

**Alternatives considered**:
1. In EndpointSlicer - Rejected: Slicer shouldn't know about CSV (separation of concerns)
2. In Validator - Rejected: Validation shouldn't have side effects
3. New post-processor class - Rejected: Over-engineered for this change

---

### RQ6: What test fixtures are needed for each component type?

**Decision**: Create minimal, focused fixtures per component type

**Rationale**: Easier to debug failures, clear test intent, composable for integration tests.

**Fixtures Needed**:

| Component Type | Fixture Name | Contents |
|----------------|--------------|----------|
| headers | `oas_with_header_refs.yaml` | Response with `headers.X-Rate-Limit.$ref` |
| parameters | `oas_with_parameter_refs.yaml` | Operation with `parameters[].$ref` |
| responses | `oas_with_response_refs.yaml` | Operation with `responses.404.$ref` |
| requestBodies | `oas_with_requestbody_refs.yaml` | POST with `requestBody.$ref` |
| securitySchemes | `oas_with_security_refs.yaml` | Operation with security requirement |
| links | `oas_with_link_refs.yaml` | Response with `links.GetUser.$ref` |
| callbacks | `oas_with_callback_refs.yaml` | Operation with `callbacks.onEvent.$ref` |
| mixed | `oas_with_all_component_refs.yaml` | All types combined |

**Alternatives considered**:
1. Single large fixture - Rejected: Hard to debug, unclear which type fails
2. Generated fixtures - Rejected: Harder to maintain, less readable

---

### RQ7: How should security scheme references be detected?

**Decision**: Scan `security` array at operation and root level, extract scheme names

**Rationale**: Security schemes aren't referenced via `$ref` but by name in the `security` array.

**Detection Logic**:
```python
# Operation-level security
for security_req in operation.get("security", []):
    for scheme_name in security_req.keys():
        # scheme_name is the securityScheme to include

# Global security (applies if no operation-level security)
for security_req in spec.get("security", []):
    for scheme_name in security_req.keys():
        # scheme_name is the securityScheme to include
```

**Alternatives considered**:
1. Only operation-level - Rejected: Misses global security inheritance
2. Always include all schemes - Rejected: Bloats output unnecessarily

---

## Best Practices Identified

### From OpenAPI Spec

1. **Component Reuse**: All 8 component types can be referenced via `$ref`
2. **Security Inheritance**: Operation security overrides global; empty array disables
3. **Callback Structure**: Callbacks contain full path items, which can have their own refs
4. **Link Parameters**: Links can reference operation parameters via runtime expressions

### From Existing Codebase

1. **BFS Pattern**: Current schema resolution uses BFS with visited set - extend this
2. **Deepcopy**: All components are deepcopied to avoid mutation - maintain this
3. **Validation Order**: 7-phase validation runs in sequence - Phase 6 fits naturally
4. **CSV Manager**: Thread-safe, handles duplicates - reuse for single extractions

---

## Implementation Recommendations

1. **Start with headers**: Most commonly reported defect, high user impact
2. **Refactor resolver first**: Central change that enables all component types
3. **Maintain backward compatibility**: Schema resolution must continue working
4. **Test fixtures first**: Write fixtures before tests (TDD for fixtures)
5. **Profile performance**: Baseline before changes, measure after each type

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Should we parallelize component resolution? | No - out of scope per spec |
| Should we validate refs point to correct type? | Yes - include in Phase 4 validation |
| Should callbacks recurse into path items? | Yes - callbacks contain operations with refs |
