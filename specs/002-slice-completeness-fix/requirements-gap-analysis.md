# Requirements Gap Analysis: slice-oas-by-resource

**Date**: 2025-12-18
**Reviewer**: Claude Opus 4.5
**Feature**: 001-slice-oas-by-resource
**Status**: Post-Implementation Review

## Executive Summary

After comprehensive review of the specification, constitution, and implementation, **critical gaps** have been identified between what was required and what was actually built. The core issue: the tool only resolves schema references (`#/components/schemas/*`) but ignores all other component types, violating the constitution's "Complete Reference Resolution" principle.

---

## Gap 1: Incomplete Component Resolution (CRITICAL)

### Requirement (Constitution Principle III)

> "Every sliced OpenAPI file MUST include all transitively referenced components while preserving the semantics of the requested OAS version. Response headers, schemas, parameters, security schemes, and all nested references must be recursively resolved."

> "MUST scan and include all response header references (common defect)"

> "Response headers in `responses[*].headers[*].$ref` are frequently missed. These MUST be explicitly scanned and included in `components.headers`"

### What Was Built

**resolver.py:108-120** - Only handles schema references:
```python
def _extract_schema_name(self, ref_string: str) -> str:
    if ref_string.startswith("#/components/schemas/"):
        return ref_string.replace("#/components/schemas/", "")
    return ref_string  # Other refs returned as-is but NOT processed
```

**slicer.py:64-70** - Only copies schemas to output:
```python
if resolved_schema_names or self.resolver.schemas:
    extracted["components"] = {"schemas": {}}
    for schema_name in resolved_schema_names:
        # Only schemas are copied
```

### Missing Component Types

| Component Type | Required | Implemented |
|----------------|----------|-------------|
| `#/components/schemas/*` | ✅ Yes | ✅ Yes |
| `#/components/headers/*` | ✅ Yes | ❌ **NO** |
| `#/components/parameters/*` | ✅ Yes | ❌ **NO** |
| `#/components/responses/*` | ✅ Yes | ❌ **NO** |
| `#/components/requestBodies/*` | ✅ Yes | ❌ **NO** |
| `#/components/securitySchemes/*` | ✅ Yes | ❌ **NO** |
| `#/components/links/*` | ✅ Yes | ❌ **NO** |
| `#/components/callbacks/*` | ✅ Yes | ❌ **NO** |

### Impact

Any OAS file using `$ref: "#/components/headers/X-Rate-Limit"` or similar non-schema references will produce **invalid output** with unresolved references.

---

## Gap 2: Validator Phase 6 is a No-Op (CRITICAL)

### Requirement (Constitution Principle IV)

> "Phase 6: Payload equivalence (operation matches parent spec exactly)"

### What Was Built

**validator.py:280-287**:
```python
def _validate_payload_equivalence(self) -> ValidationResult:
    # This phase is optional if original_doc not provided
    if not self.original_doc:
        return ValidationResult(phase=ValidationPhase.PAYLOAD_EQUIVALENCE, passed=True)

    # Basic check: extracted paths match structure of original
    return ValidationResult(phase=ValidationPhase.PAYLOAD_EQUIVALENCE, passed=True)
```

**Always returns True** - no actual comparison is performed between parent and child documents.

### Impact

Incomplete extractions pass validation because there's no verification that the extracted endpoint contains everything from the parent.

---

## Gap 3: Validator Phase 4 Only Checks Schema Refs

### Requirement

Validate that **all** `$ref` entries resolve within the sliced file.

### What Was Built

**validator.py:234-237**:
```python
if ref.startswith("#/components/schemas/"):
    schema_name = ref.replace("#/components/schemas/", "")
    if schema_name not in schemas:
        return f"Reference '{ref}' not found in components.schemas"
```

Only validates `#/components/schemas/*` references. References to headers, parameters, etc. are **not validated**.

### Impact

Broken references to non-schema components go undetected.

---

## Gap 4: Tests Did Not Follow True TDD

### Evidence

1. **Test for headers (T021)** tests schema refs IN headers, not header component refs:
   ```python
   # What the test checks:
   "headers": {"X-Rate-Limit": {"schema": {"$ref": "#/components/schemas/RateLimit"}}}

   # What the constitution requires:
   "headers": {"X-Rate-Limit": {"$ref": "#/components/headers/X-Rate-Limit"}}
   ```

2. **Phase 6 validation** was marked as tested but implementation is empty.

3. **Tests verify what was built**, not what should have been built.

### Root Cause

Tests were written alongside implementation, not before. When the implementation had gaps, the tests reflected those gaps.

---

## Gap 5: CSV Index Path Requirement

### Requirement (Constitution Principle V)

> "A CSV index file MUST be maintained at `{output_directory}/sliced-resources-index.csv`"

### What Was Built

CSV generation is implemented correctly in `batch_processor.py` but:
1. Only created during **batch** operations
2. Single extractions via CLI do not create a CSV
3. CSV is created at correct path: `{output_dir}/sliced-resources-index.csv`

### Impact

Single extraction operations produce no CSV index, which may confuse users expecting consistent behavior.

---

## Summary of Gaps

| Gap | Severity | Component | Issue |
|-----|----------|-----------|-------|
| Gap 1 | **CRITICAL** | resolver.py, slicer.py | Only schemas resolved; headers, params, etc. ignored |
| Gap 2 | **CRITICAL** | validator.py | Phase 6 payload equivalence not implemented |
| Gap 3 | **HIGH** | validator.py | Phase 4 only validates schema refs |
| Gap 4 | **HIGH** | tests/*.py | TDD not followed; tests reflect implementation gaps |
| Gap 5 | **MEDIUM** | cli.py | CSV not created for single extractions |

---

## Recommended Fix Strategy

### New Feature: 002-slice-completeness-fix

1. **Extend resolver.py** to handle ALL component types:
   - `#/components/headers/*`
   - `#/components/parameters/*`
   - `#/components/responses/*`
   - `#/components/requestBodies/*`
   - `#/components/securitySchemes/*`
   - `#/components/links/*`
   - `#/components/callbacks/*`

2. **Extend slicer.py** to copy ALL resolved components to output.

3. **Implement Phase 6** - actual parent-child comparison:
   - Extract refs from parent operation
   - Verify all refs present in child
   - Compare operation structure

4. **Extend Phase 4** to validate ALL ref types.

5. **Add CSV generation** to single extraction workflow.

6. **Write TRUE TDD tests** that test the requirements first, then verify implementation.

---

## Test Cases That Should Have Existed

```yaml
# Test 1: Header component reference
responses:
  "200":
    headers:
      X-Rate-Limit:
        $ref: "#/components/headers/X-Rate-Limit"

# Test 2: Parameter reference
parameters:
  - $ref: "#/components/parameters/PaginationOffset"

# Test 3: Response reference
responses:
  "404":
    $ref: "#/components/responses/NotFound"

# Test 4: RequestBody reference
requestBody:
  $ref: "#/components/requestBodies/UserInput"

# Test 5: SecurityScheme reference
security:
  - api_key: []

# Test 6: Link reference
responses:
  "200":
    links:
      GetUser:
        $ref: "#/components/links/GetUserById"
```

None of these scenarios are tested in the current test suite.

---

## Conclusion

The implementation passes its tests but **fails to meet the specification**. The tests were designed around the implementation rather than the requirements. A new feature must be created to fix these critical gaps before the tool can be considered production-ready.
