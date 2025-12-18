# Implementation Plan: Complete Reference Resolution Fix

**Branch**: `002-slice-completeness-fix` | **Date**: 2025-12-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-slice-completeness-fix/spec.md`

## Summary

Fix critical gaps in the OAS slicer where only schema references (`#/components/schemas/*`) are resolved, leaving 7 other component types unresolved (headers, parameters, responses, requestBodies, securitySchemes, links, callbacks). Also implement Validation Phase 6 (payload equivalence) which currently returns true without comparison, and enable CSV index generation for single extractions.

**Technical Approach**: Extend the existing `ReferenceResolver` class to handle all 8 OpenAPI component types using the same BFS traversal pattern. Extend `EndpointSlicer` to copy all resolved components (not just schemas). Implement actual parent-child comparison in `EndpointValidator._validate_payload_equivalence()`. Add CSV generation hook to single extraction flow.

## Technical Context

**Language/Version**: Python 3.11+ (existing codebase)
**Primary Dependencies**: pydantic ^2.0, PyYAML ^6.0, openapi-spec-validator ^0.7, jsonschema ^4.20
**Storage**: File-based (local filesystem: input OAS files, output sliced files, CSV index)
**Testing**: pytest ^7.4, pytest-cov ^4.1 (TDD with commit-based verification)
**Target Platform**: CLI tool (cross-platform Python)
**Project Type**: Single project (existing structure)
**Performance Goals**: Single extraction <5s (SC-007), <10% increase from current baseline
**Constraints**: Zero regressions (195 existing tests), backward compatible
**Scale/Scope**: Handle OAS files with 1000+ endpoints (existing capability)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Black Box** | No code/technical details shown to users | ✅ PASS | Fix is internal; no UX changes |
| **II. Explicit Paths** | No auto-discovery | ✅ PASS | No path changes |
| **III. Complete Resolution** | ALL refs resolved (headers, schemas, params, etc.) | ❌ FAIL → FIX | This is the gap being fixed |
| **IV. Deterministic Validation** | 7-phase validation including Phase 6 | ❌ FAIL → FIX | Phase 6 currently a no-op |
| **V. CSV Indexing** | CSV updated for all extractions | ❌ FAIL → FIX | Single extractions skip CSV |

**Gate Status**: ✅ PASS - Violations are the gaps this feature fixes.

## Project Structure

### Documentation (this feature)

```text
specs/002-slice-completeness-fix/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal API contracts)
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
src/slice_oas/
├── __init__.py
├── __main__.py
├── cli.py               # CLI entry point (CSV hook for single extraction)
├── models.py            # Data models (extend ResolvedComponents)
├── parser.py            # OAS parsing
├── resolver.py          # ⚡ MODIFY: Handle all 8 component types
├── slicer.py            # ⚡ MODIFY: Copy all component types to output
├── validator.py         # ⚡ MODIFY: Implement Phase 6 comparison
├── generator.py         # Output generation
├── csv_manager.py       # CSV index management
├── batch_processor.py   # Batch extraction
├── converter.py         # Version conversion
├── filters.py           # Endpoint filtering
├── progress.py          # Progress reporting
├── output_manager.py    # File output
├── exceptions.py        # Custom exceptions
└── transformation_rules.json

tests/
├── unit/
│   ├── test_parser.py
│   ├── test_models.py
│   ├── test_cli.py
│   └── test_resolver.py     # ⚡ ADD: Tests for all component types
├── integration/
│   ├── test_single_extraction.py
│   ├── test_batch_extraction.py
│   ├── test_version_conversion.py
│   ├── test_csv_generation.py
│   ├── test_component_resolution.py  # ⚡ ADD: Per-component-type tests
│   └── test_payload_equivalence.py   # ⚡ ADD: Phase 6 validation tests
├── fixtures/
│   ├── oas_3_0_simple.yaml
│   ├── oas_3_0_complex.yaml
│   ├── oas_with_headers.yaml         # ⚡ ADD: Header ref fixtures
│   ├── oas_with_parameters.yaml      # ⚡ ADD: Parameter ref fixtures
│   ├── oas_with_responses.yaml       # ⚡ ADD: Response ref fixtures
│   ├── oas_with_all_components.yaml  # ⚡ ADD: Mixed component refs
│   └── ...
└── conftest.py
```

**Structure Decision**: Single project structure (existing). Modifications extend existing modules; no new top-level directories needed.

## Architecture Overview

### Component Resolution Flow (Current vs Fixed)

```
CURRENT (broken):
  Endpoint → scan $ref → find #/components/schemas/* only → copy schemas → output
                         ❌ MISS: headers, parameters, responses, etc.

FIXED:
  Endpoint → scan $ref → classify by component type → resolve ALL types → copy ALL → output
                         ✅ headers, parameters, responses, requestBodies,
                            securitySchemes, links, callbacks, schemas
```

### Key Classes to Modify

1. **ReferenceResolver** (`resolver.py`)
   - Current: `_extract_schema_name()` only handles `#/components/schemas/`
   - Fix: Add `_extract_component_ref()` that parses any `#/components/{type}/{name}`
   - Fix: Track resolved components by type in separate dictionaries

2. **EndpointSlicer** (`slicer.py`)
   - Current: Only copies `components.schemas` to output
   - Fix: Copy all component types from resolver results

3. **EndpointValidator** (`validator.py`)
   - Current: `_validate_payload_equivalence()` returns True always
   - Fix: Implement actual comparison of refs between parent and child

4. **CLI** (`cli.py`)
   - Current: CSV only in batch mode
   - Fix: Add CSV generation after single extraction success

## TDD Commit Strategy

Per FR-019/FR-020, each component type requires:

1. **RED commit**: Add failing tests for component type
2. **GREEN commit**: Implement resolution for that type

Sequence:
```
[RED]   Test headers resolution (expect fail)
[GREEN] Implement headers resolution
[RED]   Test parameters resolution (expect fail)
[GREEN] Implement parameters resolution
[RED]   Test responses resolution (expect fail)
[GREEN] Implement responses resolution
[RED]   Test requestBodies resolution (expect fail)
[GREEN] Implement requestBodies resolution
[RED]   Test securitySchemes resolution (expect fail)
[GREEN] Implement securitySchemes resolution
[RED]   Test links resolution (expect fail)
[GREEN] Implement links resolution
[RED]   Test callbacks resolution (expect fail)
[GREEN] Implement callbacks resolution
[RED]   Test Phase 6 validation (expect fail)
[GREEN] Implement Phase 6 validation
[RED]   Test single extraction CSV (expect fail)
[GREEN] Implement single extraction CSV
```

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Circular refs across component types | Medium | High | Extend visited set to include component type in key |
| Performance regression | Low | Medium | Profile before/after; target <10% increase |
| Test fixture complexity | Medium | Low | Create modular fixtures; compose from base files |
| Breaking existing tests | Low | High | Run full suite after each change; no skips |

## Dependencies

- No new external dependencies required
- All changes use existing libraries (PyYAML, pydantic, openapi-spec-validator)
- Extends existing internal architecture patterns

## Complexity Tracking

> No constitution violations requiring justification. All changes align with principles.

| Item | Complexity | Justification |
|------|------------|---------------|
| 8 component types | Moderate | Required by OpenAPI 3.x spec; no simplification possible |
| BFS for all types | Low | Reuses existing pattern from schema resolution |
| Phase 6 validation | Low | Straightforward ref comparison |
