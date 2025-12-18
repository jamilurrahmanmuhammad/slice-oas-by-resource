# Validation Phases

The OAS Slicer validates every extracted endpoint through 7 phases to ensure quality and correctness.

## Overview

Each extracted endpoint passes through validation to guarantee:

- The output is a valid OpenAPI specification
- All references are properly resolved
- No information is lost during extraction
- The endpoint can be used immediately by downstream tools

## The 7 Validation Phases

### Phase 1: File Structure

**What it checks:**
- Valid OpenAPI document structure
- Required fields present (`openapi`, `info`, `paths`)
- Proper nesting and formatting

**Common issues:**
- Missing required fields
- Invalid OpenAPI version string
- Malformed document structure

**User message on failure:**
> The file format is invalid. Please check that it's a valid OpenAPI specification file.

---

### Phase 2: Operation Integrity

**What it checks:**
- The endpoint operation is complete
- Required operation fields present
- Valid HTTP method

**Common issues:**
- Missing responses section
- Invalid operation structure
- Incomplete endpoint definition

**User message on failure:**
> The endpoint definition is incomplete. Please verify the operation is properly defined.

---

### Phase 3: Response Integrity

**What it checks:**
- All response codes are valid
- Response content types are properly defined
- Response schemas are present where expected

**Common issues:**
- Invalid HTTP status codes
- Missing content type definitions
- Incomplete response structures

**User message on failure:**
> The response definition has issues. Please check response codes and content types.

---

### Phase 4: Reference Resolution

**What it checks:**
- All `$ref` pointers resolve to existing components
- No broken internal references
- External references handled appropriately

**Common issues:**
- References to non-existent schemas
- Typos in reference paths
- Missing components section

**User message on failure:**
> Some components referenced in the endpoint cannot be found. Please verify all required definitions exist in the file.

---

### Phase 5: Component Completeness

**What it checks:**
- All required components are included in output
- Transitive dependencies are resolved
- No orphaned references

**Common issues:**
- Missing transitive dependencies
- Incomplete component extraction
- Tool-level extraction errors

**User message on failure:**
> Some required components are missing from the output. This is likely a tool issue—please contact support.

---

### Phase 6: Payload Equivalence

**What it checks:**
- Extracted endpoint matches the original
- No data loss during extraction
- Operation semantics preserved

**Common issues:**
- Extraction algorithm errors
- Data transformation issues
- Unexpected modifications

**User message on failure:**
> The extracted endpoint doesn't match the original. Please try again.

---

### Phase 7: Version Validation

**What it checks:**
- Output conforms to requested OpenAPI version
- Version-specific syntax is correct
- Conversion rules properly applied

**Common issues:**
- Invalid version format
- Unconverted version-specific constructs
- Schema validation failures

**User message on failure:**
> The output format doesn't match the requested OpenAPI version. Please try again.

---

## Validation Flow

```
Input Spec
    │
    ▼
┌─────────────────┐
│ Extract Endpoint │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Phase 1: File       │──▶ FAIL ──▶ Stop & Report
│ Structure           │
└────────┬────────────┘
         │ PASS
         ▼
┌─────────────────────┐
│ Phase 2: Operation  │──▶ FAIL ──▶ Stop & Report
│ Integrity           │
└────────┬────────────┘
         │ PASS
         ▼
┌─────────────────────┐
│ Phase 3: Response   │──▶ FAIL ──▶ Stop & Report
│ Integrity           │
└────────┬────────────┘
         │ PASS
         ▼
┌─────────────────────┐
│ Phase 4: Reference  │──▶ FAIL ──▶ Stop & Report
│ Resolution          │
└────────┬────────────┘
         │ PASS
         ▼
┌─────────────────────┐
│ Phase 5: Component  │──▶ FAIL ──▶ Stop & Report
│ Completeness        │
└────────┬────────────┘
         │ PASS
         ▼
┌─────────────────────┐
│ Phase 6: Payload    │──▶ FAIL ──▶ Stop & Report
│ Equivalence         │
└────────┬────────────┘
         │ PASS
         ▼
┌─────────────────────┐
│ Phase 7: Version    │──▶ FAIL ──▶ Stop & Report
│ Validation          │
└────────┬────────────┘
         │ PASS
         ▼
    Write Output
```

## Batch Processing Behavior

During batch extraction:

1. **Fail-fast per endpoint**: Each endpoint is validated independently
2. **Continue on failure**: Failed endpoints don't stop the batch
3. **Track failures**: All failures are recorded and reported
4. **CSV exclusion**: Failed endpoints are not added to the CSV index

### Batch Summary Example

```
Processing complete!

Results:
  - Total endpoints found: 50
  - Successfully extracted: 48
  - Failed: 2
  - Validation pass rate: 96.0%

Failed endpoints:
  - GET /broken-ref: Reference resolution failed
  - POST /invalid-schema: File structure validation failed

Output location: ./output/
CSV index: ./output/sliced-resources-index.csv
```

## Troubleshooting Validation Failures

### Phase 1 Failures

Check your input file:
1. Is it valid YAML or JSON?
2. Does it have an `openapi` version field?
3. Are all required sections present?

### Phase 4 Failures (Most Common)

Reference resolution failures usually indicate:
1. A typo in a `$ref` path
2. A referenced component that doesn't exist
3. A circular reference that wasn't handled

To diagnose:
```bash
# Try extracting in dry-run mode to see what references are detected
slice-oas api.yaml --path /problematic --method GET --dry-run
```

### Phase 5 Failures

Component completeness failures are usually tool-level issues. Please report these with:
1. The input specification (or a minimal reproduction)
2. The endpoint path and method
3. The exact error message

### Phase 7 Failures

Version validation failures during conversion:
1. Check if the construct is convertible (see VERSION_CONVERSION.md)
2. Try strict mode to identify specific issues
3. Consider keeping the original version

## Performance Impact

Validation adds minimal overhead:
- Phases 1-3: < 10ms per endpoint
- Phase 4: Depends on reference count (~1ms per reference)
- Phases 5-6: < 20ms per endpoint
- Phase 7: < 50ms per endpoint (includes schema validation)

Total validation overhead is typically under 100ms per endpoint.
