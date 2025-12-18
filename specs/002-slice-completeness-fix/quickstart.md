# Quickstart: Complete Reference Resolution Fix

**Feature**: 002-slice-completeness-fix
**Time to First Test**: ~15 minutes

## Prerequisites

- Python 3.11+
- Poetry installed
- Existing codebase cloned

## Setup

```bash
# Navigate to project
cd /repos/slice-oas-by-resource

# Install dependencies
poetry install

# Verify existing tests pass (baseline)
poetry run pytest -v
# Expected: 195 passed, 1 skipped
```

## TDD Workflow

### Step 1: Create Test Fixture for Headers

Create a minimal OAS fixture with header references:

```yaml
# tests/fixtures/oas_with_header_refs.yaml
openapi: "3.0.0"
info:
  title: "Header Test API"
  version: "1.0.0"
paths:
  /resources:
    get:
      summary: "Get resources"
      responses:
        "200":
          description: "Success"
          headers:
            X-Rate-Limit:
              $ref: "#/components/headers/X-Rate-Limit"
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
components:
  headers:
    X-Rate-Limit:
      description: "Rate limit header"
      schema:
        type: integer
```

### Step 2: Write Failing Test (RED)

```python
# tests/integration/test_component_resolution.py
import pytest
from slice_oas.slicer import EndpointSlicer
from slice_oas.parser import parse_oas

class TestHeaderResolution:
    """Test header component reference resolution."""

    @pytest.fixture
    def spec_with_headers(self):
        return parse_oas("tests/fixtures/oas_with_header_refs.yaml")

    def test_header_ref_is_resolved(self, spec_with_headers):
        """Header $ref should be included in extracted output."""
        slicer = EndpointSlicer(spec_with_headers, "3.0.0")
        result = slicer.extract("/resources", "GET")

        # This WILL FAIL initially - headers not resolved
        assert "components" in result
        assert "headers" in result["components"]
        assert "X-Rate-Limit" in result["components"]["headers"]
```

### Step 3: Run Test and Verify Failure

```bash
poetry run pytest tests/integration/test_component_resolution.py -v
# Expected: FAILED - KeyError: 'headers' not in components
```

### Step 4: Implement Fix (GREEN)

Modify `resolver.py` to handle header refs, then `slicer.py` to copy them.

### Step 5: Run Test and Verify Pass

```bash
poetry run pytest tests/integration/test_component_resolution.py -v
# Expected: PASSED
```

### Step 6: Verify No Regressions

```bash
poetry run pytest -v
# Expected: 196+ passed (195 existing + new tests)
```

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/slice_oas/resolver.py` | Add component type parsing and resolution |
| `src/slice_oas/slicer.py` | Copy all component types to output |
| `src/slice_oas/validator.py` | Implement Phase 6 comparison |
| `src/slice_oas/cli.py` | Add CSV hook for single extractions |

## Commit Strategy

Each component type gets two commits:

```bash
# Example for headers
git add tests/
git commit -m "test(headers): add failing tests for header resolution

RED phase: Tests expect header refs to be resolved in output.
Currently fails because resolver only handles schemas."

# After implementation
git add src/
git commit -m "feat(headers): implement header reference resolution

GREEN phase: Resolver now handles #/components/headers/* refs.
Slicer copies resolved headers to output components.

Closes: partial fix for #002-slice-completeness-fix"
```

## Verification Checklist

- [ ] All 195 existing tests still pass
- [ ] New tests for each component type (headers, parameters, etc.)
- [ ] Each component type has RED commit followed by GREEN commit
- [ ] Phase 6 validation actually compares parent/child
- [ ] Single extractions generate CSV index
- [ ] No performance regression (extraction < 5s)

## Common Issues

### Issue: Tests pass without implementation

**Cause**: Test fixture doesn't actually use the component ref
**Fix**: Verify fixture has `$ref: "#/components/{type}/{name}"` syntax

### Issue: Circular reference infinite loop

**Cause**: Visited set doesn't include component type
**Fix**: Use `(component_type, component_name)` tuple as key

### Issue: Missing security schemes

**Cause**: Security uses name-based reference, not $ref
**Fix**: Special handling in `resolve_security_schemes()`
