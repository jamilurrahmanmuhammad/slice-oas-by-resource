# Internal API Contract: EndpointValidator

**Module**: `src/slice_oas/validator.py`
**Version**: 2.0.0 (extends existing 1.x)

## Class: EndpointValidator

### Constructor

```python
def __init__(
    self,
    extracted_doc: Dict[str, Any],
    version: str,
    original_doc: Optional[Dict[str, Any]] = None
) -> None:
    """Initialize validator with extracted and optionally original document.

    Args:
        extracted_doc: The sliced/extracted OAS document
        version: OAS version string
        original_doc: Original parent document (required for Phase 6)

    Post-conditions:
        - self.doc is set to extracted_doc
        - self.version is set to version
        - self.original_doc is set to original_doc
    """
```

### Public Methods

#### validate (Unchanged signature)

```python
def validate(self) -> ValidationResult:
    """Run all validation phases.

    Returns:
        ValidationResult with overall pass/fail and details

    Phases executed:
        1. File structure
        2. Operation integrity
        3. Response integrity
        4. Reference resolution (ALL component types)
        5. Component completeness
        6. Payload equivalence (if original_doc provided)
        7. Version validation

    Contract:
        - Phases run in order
        - Stops at first failure
        - Returns specific error for failed phase
    """
```

### Private Methods (Modified)

#### _validate_reference_resolution (Modified)

```python
def _validate_reference_resolution(self) -> ValidationResult:
    """Phase 4: Validate ALL $ref entries resolve within document.

    Returns:
        ValidationResult for Phase 4

    Algorithm:
        1. Collect all $ref strings from extracted document
        2. For each $ref:
           a. Parse component type and name
           b. Check if component exists in extracted doc's components
           c. If missing, record as unresolved
        3. If any unresolved, fail with list of missing refs

    Contract (MODIFIED):
        - MUST check schemas, headers, parameters, responses,
          requestBodies, securitySchemes, links, callbacks
        - NOT just schemas (previous behavior)
    """
```

#### _validate_payload_equivalence (Modified - Was No-Op)

```python
def _validate_payload_equivalence(self) -> ValidationResult:
    """Phase 6: Validate extracted endpoint matches parent.

    Returns:
        ValidationResult for Phase 6

    Pre-conditions:
        - self.original_doc must be set (or phase is skipped)

    Algorithm:
        1. If no original_doc, return PASS (backward compatible)
        2. Extract all $ref from extracted document
        3. For each $ref:
           a. Parse component type and name
           b. Verify component exists in original_doc
           c. Verify component exists in extracted doc
           d. If extracted is missing a component from original, FAIL
        4. Verify security schemes are complete
        5. If all checks pass, return PASS

    Contract (NEW - WAS NO-OP):
        - MUST perform actual comparison
        - MUST fail if any required component is missing
        - MUST provide specific error message with missing component
    """
```

### New Methods

#### _collect_all_refs (New)

```python
def _collect_all_refs(self, doc: Dict[str, Any]) -> List[str]:
    """Collect all $ref strings from a document.

    Args:
        doc: OAS document to scan

    Returns:
        List of all $ref string values found

    Contract:
        - Recursively scans entire document
        - Returns only $ref values, not paths to them
        - Includes refs in all locations (paths, components, etc.)
    """
```

#### _check_component_exists (New)

```python
def _check_component_exists(
    self,
    doc: Dict[str, Any],
    component_type: str,
    component_name: str
) -> bool:
    """Check if a component exists in a document.

    Args:
        doc: OAS document to check
        component_type: Type of component (schemas, headers, etc.)
        component_name: Name of the component

    Returns:
        True if component exists, False otherwise
    """
```

## Validation Phase Summary

| Phase | Name | What it validates | Modified? |
|-------|------|-------------------|-----------|
| 1 | File structure | Valid JSON/YAML, root keys | No |
| 2 | Operation integrity | Single path, single method | No |
| 3 | Response integrity | Response codes, headers | No |
| 4 | Reference resolution | ALL $ref types resolve | **YES** |
| 5 | Component completeness | No orphaned refs | No |
| 6 | Payload equivalence | Matches parent spec | **YES** |
| 7 | Version validation | Correct OAS version syntax | No |

## Error Messages

### Phase 4 Errors

```
"Reference '#/components/headers/X-Rate-Limit' not found in extracted document"
"Reference '#/components/parameters/userId' not found in extracted document"
```

### Phase 6 Errors

```
"Component 'headers/X-Rate-Limit' exists in parent but missing from extracted document"
"Security scheme 'api_key' required by operation but not included in extraction"
```

## Backward Compatibility

- Constructor signature unchanged (original_doc was already optional)
- validate() return type unchanged
- New behavior only activates when original_doc is provided
- Existing tests continue to pass (original_doc = None case)
