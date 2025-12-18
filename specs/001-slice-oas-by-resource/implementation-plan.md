# Implementation Plan: Skill-Driven Execution Strategy

**Feature**: 001-slice-oas-by-resource | **Branch**: 001-slice-oas-by-resource | **Date**: 2025-12-18

---

## Executive Summary

This document maps Claude skills to implementation tasks, ensuring comprehensive coverage of quality gates, edge cases, and integration points. The strategy follows the corrected TDD execution order from tasks.md and leverages **five specialized skills** to guarantee output quality through verification (unit/integration tests) and validation (acceptance testing with the actual tool).

---

## Skill Deployment Strategy

### Skill 0: `slice-oas-by-resource` (Acceptance Testing)
**Purpose**: Validate the actual tool works as intended; acceptance testing for real-world scenarios

**When applied**: After implementation tasks complete in each phase (post-implementation validation)
**Impact**: Confirms tool works end-to-end for users; catches integration issues before moving to next phase

**Pattern** (Standard Architecture):
1. Implement code + write unit/integration tests (verification)
2. **Use skill to extract real OAS files** (validation/acceptance)
3. Verify outputs match expectations
4. Proceed to next phase

**Tasks affected**:
- Phase 3: T034+ (after unit/integration tests pass, use skill to extract real endpoint)
- Phase 4: T053+ (after tests pass, use skill on 100+ endpoint file)
- Phase 5: T071+ (after tests pass, use skill with version conversion)
- Phase 6: T088+ (after tests pass, verify CSV with skill outputs)
- Phase 8: T102 (E2E workflow using skill as acceptance test)

**Acceptance Testing Workflow**:
```
T025-T033: Implement + Unit/Integration tests
    ↓
T034: Run all tests pass ✓
    ↓
[ACTIVATE SKILL]: slice-oas-by-resource
    → Extract real OpenAPI 3.0 file
    → Verify output is valid standalone OAS
    → Check response headers resolved
    → Verify circular refs handled
    → Confirm CSV entry accurate
    ↓
Phase 3 COMPLETE (Ready for Phase 4)
```

---

### Skill 1: `test-coverage`
**Purpose**: Write comprehensive tests early; use TDD to catch issues before implementation

**When applied**: Beginning of each phase (unit tests first)
**Impact**: Ensures 100% test coverage, catches bugs early, validates acceptance criteria

**Tasks affected**:
- Phase 2: T012-T013 (write unit tests for parser/models BEFORE module creation)
- Phase 3-7: Unit test tasks in each user story (T032-T033, T050-T051, T068-T069, T087, T100)

---

### Skill 2: `implementation-completeness`
**Purpose**: Ensure comprehensive implementation covering all edge cases and error paths

**When applied**: During implementation and Phase 8 validation
**Impact**: No incomplete features, all edge cases handled, all error paths covered

**Tasks affected**:
- Phase 1: T001-T007 (scaffold complete project structure)
- Phase 2: T008-T016 (create all foundational modules completely)
- Phase 3-7: Implementation tasks (T025-T031, T043-T049, T062-T067, T080-T086, T094-T099)
- Phase 8: T102-T115 (integration testing, performance validation, edge cases)

---

### Skill 3: `cross-artifact-consistency`
**Purpose**: Keep specs, plans, tasks in sync to avoid contradictions

**When applied**: After each phase completion and before integration
**Impact**: No specification drift, all requirements remain in sync, no breaking changes

**Tasks affected**:
- Phase 2 checkpoint (T016 - CLI error handling must align with spec FR-033-FR-036)
- Phase 3 completion (T034 - verify US1 matches spec acceptance criteria)
- Phase 8: T115 (final verification against all 5 constitutional principles)

---

### Skill 4: `integration-issues`
**Purpose**: Properly configure integration points and test environment setup

**When applied**: Phase 2 and Phase 3 (foundational integration)
**Impact**: Pytest fixtures work correctly, reference resolver integrates with slicer, validators gate properly

**Tasks affected**:
- Phase 2: T007 (pytest conftest.py with proper fixtures)
- Phase 2: T010 (test fixtures for OAS 3.0/3.1 files)
- Phase 3: T027 (slicer orchestrator - integration point)
- Phase 3: T031 (CLI integration flow)

---

## Execution Sequence with Skill Activation

### Phase 1: Setup (T001-T007)
**Skill**: `implementation-completeness`

| Task | Description | Skill Role | TDD Order | Deliverable |
|------|-------------|-----------|-----------|-------------|
| T001 | Project structure | Ensure all dirs created | 1 | `src/`, `tests/`, `docs/` |
| T002 | Poetry pyproject.toml | Verify dependencies complete | 2 | pyproject.toml with all deps |
| T003-T004 | Base modules | Create empty stubs | 3-4 | Module structure ready |
| T005 | CLI __main__.py | Implement entry point | 5 | Executable with --help |
| T006 | Custom exceptions | Define all error classes | 6 | exceptions.py complete |
| T007 | Pytest conftest.py | Set up test infrastructure | 7 | Fixtures available for Phase 2 |

**Checkpoint**: All directories created, Poetry lockfile generated, basic structure in place

---

### Phase 2: Foundation (T008-T016)
**Skills**: `test-coverage` + `cross-artifact-consistency` + `integration-issues`

| Task | Description | Skill Role | TDD Order | Dependencies |
|------|-------------|-----------|-----------|-------------|
| T010 | Test fixtures | `integration-issues`: Create OAS files for testing | 1st (do first) | ✓ Enables T012-T013 |
| T012-T013 | Unit tests | `test-coverage`: Write failing tests for parser/models | 2nd (before code) | ✓ T010 provides fixtures |
| T008-T009 | Parser + Models | `implementation-completeness`: Implement to pass tests | 3rd (code after tests) | ✓ T012-T013 define expectations |
| T011 | Version detection | `implementation-completeness`: Add logic for 3.0/3.1 | 4th | ✓ Extends T009 |
| T014-T016 | CLI + Error handling | `cross-artifact-consistency`: Verify FR-031-FR-036 covered | 5th | ✓ Aligns with spec |

**Checkpoint**: Foundation complete
- [ ] All unit tests passing
- [ ] OAS parser detects versions correctly
- [ ] Error messages match spec requirements
- [ ] No spec-to-code drift

---

### Phase 3: User Story 1 - Single Endpoint Extraction (T017-T034)
**Skills**: `test-coverage` + `implementation-completeness` + `integration-issues`

#### TDD Execution Sequence (corrected order)

| Sequence | Tasks | Skill | Description |
|----------|-------|-------|-------------|
| 1st | T032-T033 | `test-coverage` | Write failing unit tests for resolver & slicer |
| 2nd | T025-T031 | `implementation-completeness` | Implement code to pass unit tests |
| 3rd | T017-T024 | `integration-issues` | Write integration tests for end-to-end flow |
| 4th | T034 | `test-coverage` | Run all tests → verify 100% pass |

#### Skill Application Details

**T032-T033 (Unit Tests)** - `test-coverage`
- Write failing tests for resolver (BFS traversal, circular detection, response header scanning)
- Write failing tests for slicer (endpoint extraction, dependency collection)
- Tests define expectations for implementation

**T025-T031 (Implementation)** - `implementation-completeness`
- T025: Reference resolver with visited set (handles circular refs)
- T026: Response header scanning (constitutional requirement - critical detail)
- T027: Slicer orchestrator
- T028-T030: Validator (6 phases) + file output + OAS generation
- T031: CLI integration

**T017-T024 (Integration Tests)** - `integration-issues`
- Test simple extraction, schema refs, transitive dependencies, circular refs
- Test response headers with $ref (constitutional requirement)
- Test JSON/YAML output formats
- Test error handling (endpoint not found)

**T034 (Verification)** - `test-coverage`
- All 8 integration tests pass
- All 2 unit test suites pass
- No regressions

**Checkpoint**: Single endpoint extraction working end-to-end
- [ ] 100% unit test pass rate
- [ ] 100% integration test pass rate
- [ ] Response headers correctly resolved
- [ ] Output files valid OpenAPI 3.0.x/3.1.x

---

### Phase 4: User Story 2 - Batch Slicing (T035-T053)
**Skills**: `test-coverage` + `implementation-completeness`

| Sequence | Tasks | Skill |
|----------|-------|-------|
| 1st | T050-T051 | `test-coverage`: Unit tests for batch processor & CSV generator |
| 2nd | T043-T049 | `implementation-completeness`: Batch processor + filters + CSV logic |
| 3rd | T035-T042 | `test-coverage`: Integration tests for batch operations |
| 4th | T053 | `test-coverage`: Verify all pass |

**Critical Tasks**:
- T048: CSV deduplication (handles re-runs correctly)
- T049: Error resilience (skip failed extractions, continue)

**Checkpoint**: Batch processing 100 endpoints in <3 minutes, CSV index accurate

---

### Phase 5: User Story 3 - Version Conversion (T054-T071)
**Skills**: `test-coverage` + `implementation-completeness`

| Sequence | Tasks | Skill |
|----------|-------|-------|
| 1st | T068-T069 | `test-coverage`: Unit tests for converter & version validation |
| 2nd | T062-T067 | `implementation-completeness`: Transformation rules, error handling |
| 3rd | T054-T061 | `test-coverage`: Integration tests for all conversion scenarios |
| 4th | T071 | `test-coverage`: Verify deterministic output |

**Critical Edge Cases** (per constitution):
- Nullable ↔ type arrays conversion
- Webhooks handling (3.0 vs 3.1)
- mutualTLS scheme removal (3.1→3.0 only)
- JSON Schema conditionals rejection (fail gracefully)

**Checkpoint**: Version conversion deterministic and reversible

---

### Phase 6: User Story 4 - CSV Governance (T072-T088)
**Skills**: `test-coverage` + `implementation-completeness`

| Sequence | Tasks | Skill |
|----------|-------|-------|
| 1st | T087 | `test-coverage`: Unit tests for CSV formatting |
| 2nd | T080-T086 | `implementation-completeness`: All CSV columns (15 exact), RFC 4180 compliance |
| 3rd | T072-T079 | `test-coverage`: Integration tests for CSV structure & spreadsheet compatibility |
| 4th | T088 | `test-coverage`: Verify all pass |

**CSV Columns** (constitutional requirement - exact order):
path, method, summary, description, operationId, tags, filename, file_size_kb, schema_count, parameter_count, response_codes, security_required, deprecated, created_at, output_oas_version

**Checkpoint**: CSV compatible with Excel/Google Sheets, deduplication working

---

### Phase 7: User Story 5 - Black Box UX (T089-T101)
**Skills**: `test-coverage` + `implementation-completeness`

| Sequence | Tasks | Skill |
|----------|-------|-------|
| 1st | T100 | `test-coverage`: Unit tests scanning for code/JSON/YAML patterns |
| 2nd | T094-T099 | `implementation-completeness`: Prompt templates, error messages, progress reporters |
| 3rd | T089-T093 | `test-coverage`: Integration tests for plain language, conversational tone |
| 4th | T101 | `test-coverage`: Verify no technical jargon exposed |

**Constitutional Requirement** (Principle I):
- Zero code shown to users
- No JSON/YAML structures displayed
- Algorithm details hidden
- Error messages actionable and plain language

**Checkpoint**: Non-programmer can complete workflow without seeing technical details

---

### Phase 8: Integration & Polish (T102-T115)
**Skills**: `cross-artifact-consistency` + `implementation-completeness`

| Task | Skill | Purpose |
|------|-------|---------|
| T102 | `integration-issues` | E2E workflow test (input → extraction → validation → output → CSV) |
| T103 | `implementation-completeness` | Performance benchmarks (<5s single, <3min batch 100) |
| T104 | `implementation-completeness` | Large file handling (1000+ endpoints, memory validation) |
| T105 | `test-coverage` | Edge case tests (circular refs, missing components, malformed input) |
| T106-T109 | `implementation-completeness` | Documentation (USAGE, VERSION_CONVERSION, VALIDATION_PHASES, README) |
| T110-T111 | `implementation-completeness` | Project metadata (pyproject.toml, .gitignore) |
| T112-T113 | `test-coverage` | Full test suite (100% pass, >90% coverage) |
| T114 | `implementation-completeness` | CI/CD workflow (.github/workflows/test.yml) |
| T115 | `cross-artifact-consistency` | **FINAL GATE**: Verify all 5 constitutional principles met |

**Final Checkpoint (T115)** - Must verify:
- [ ] Principle I: Black Box ✓
- [ ] Principle II: Explicit Paths ✓
- [ ] Principle III: Complete Resolution ✓
- [ ] Principle IV: Deterministic Validation ✓
- [ ] Principle V: CSV Indexing ✓

---

## Critical Decision Points

### Decision 1: CSV Real-Time Updates (Phase 2 Design)
**Task**: T047 (Real-time CSV append)
**Issue**: File locking vs buffer-with-flush strategy for concurrent writes
**Resolution**: Use append-mode with process-local writes (safe by default)
**Skill**: `integration-issues` will validate approach

### Decision 2: Response Header Resolution (Phase 3)
**Task**: T026 (Response header $ref scanning)
**Issue**: Constitutional requirement - commonly missed pattern
**Resolution**: Explicit task + unit test (T032) + integration test (T021)
**Skill**: `test-coverage` will ensure comprehensive edge case testing

### Decision 3: Version Conversion Edge Cases (Phase 5)
**Task**: T067 (Error handling for unconvertible structures)
**Issue**: JSON Schema conditionals (3.1→3.0 conversion fails)
**Resolution**: Fail gracefully with user-friendly message
**Skill**: `implementation-completeness` ensures all error paths covered

### Decision 4: Black Box UX Validation (Phase 7)
**Task**: T100 (UX validation tests)
**Issue**: How to verify zero code exposure?
**Resolution**: Regex-based pattern matching (scan for code keywords)
**Skill**: `test-coverage` with comprehensive pattern library

---

## Success Criteria by Phase

| Phase | Success Metric | Verification Task | Skill |
|-------|----------------|-------------------|-------|
| 1 | All directories, Poetry lockfile created | `ls -R src/` | `implementation-completeness` |
| 2 | All unit tests passing, no spec drift | `pytest tests/unit/` | `test-coverage` |
| 3 | Single extraction <5s, CSV entry created | `pytest tests/integration/test_single_extraction.py` | `test-coverage` |
| 4 | Batch 100 endpoints <3min, CSV deduplicated | `pytest tests/integration/test_batch_extraction.py` | `test-coverage` |
| 5 | Version conversion deterministic & reversible | `pytest tests/integration/test_version_conversion.py` | `test-coverage` |
| 6 | CSV spreadsheet-compatible, RFC 4180 | `pytest tests/integration/test_csv_tracking.py` | `test-coverage` |
| 7 | Zero code exposed to users | `pytest tests/integration/test_ux_validation.py` | `test-coverage` |
| 8 | 100% test coverage, all principles verified | `pytest` + `T115` gate | `cross-artifact-consistency` |

---

## Execution Flow Diagram

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundation) ← test-coverage, cross-artifact-consistency, integration-issues
    ↓
Phase 3 (US1): Implement → Unit/Integration Tests → [ACTIVATE: slice-oas-by-resource]
    ↓
Phase 4 (US2): Implement → Tests → [ACTIVATE: slice-oas-by-resource on 100+ endpoints]
    ↓
Phase 5 (US3): Implement → Tests → [ACTIVATE: slice-oas-by-resource with version conversion]
    ↓
Phase 6 (US4): Implement → Tests → [ACTIVATE: slice-oas-by-resource, verify CSV]
    ↓
Phase 7 (US5): Implement → Tests (no skill invocation needed - UX validation)
    ↓
Phase 8 (Integration) ← cross-artifact-consistency, implementation-completeness
    ├─ T102: E2E workflow [ACTIVATE: slice-oas-by-resource for final acceptance test]
    ├─ T103-T104: Performance benchmarks
    └─ T115: Final constitutional principles gate
```

**Legend**:
- Skill activations in brackets indicate acceptance testing checkpoints
- Each phase gates are: Unit Tests Pass → Integration Tests Pass → Acceptance Test (skill) Pass

---

## Implementation Guardrails

1. **No task starts until dependencies complete** (TDD execution order)
2. **Every test failure blocks implementation** (TDD discipline)
3. **Every phase end requires skill verification** (quality gate)
4. **Constitutional principles checked continuously** (T115 is NOT first-time check)
5. **Spec-to-code drift detected early** (Phase 2 checkpoint via cross-artifact-consistency)

---

## Next Actions

Ready to execute `/sp.implement` with:
- ✅ Five skills mapped to phases (test-coverage, implementation-completeness, cross-artifact-consistency, integration-issues, slice-oas-by-resource)
- ✅ Acceptance testing pattern integrated (skill invocations at T034, T053, T071, T088, T102)
- ✅ TDD execution order clarified (unit tests → implementation → integration tests → acceptance test)
- ✅ Critical decision points identified
- ✅ Quality gates defined per phase (verification + validation)
- ✅ Constitutional principles verified at each milestone
- ✅ Execution flow diagrammed with skill activation points

**Standard Architecture Applied**:
- Verification: Unit/Integration tests (pytest)
- Validation: Acceptance tests (slice-oas-by-resource skill)
- Each phase gates: Tests Pass → Skill Validation Pass → Next Phase

**Ready to execute `/sp.implement` Phase 1 using `implementation-completeness` skill**

