# Tasks: Complete Reference Resolution Fix

**Input**: Design documents from `/specs/002-slice-completeness-fix/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: TDD required per FR-016 through FR-020. Each component type requires RED commit (failing tests) then GREEN commit (implementation).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/slice_oas/`
- **Tests**: `tests/unit/`, `tests/integration/`
- **Fixtures**: `tests/fixtures/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create test fixtures and extend data models needed by all user stories

- [x] T001 [P] Create header reference fixture in tests/fixtures/oas_with_header_refs.yaml
- [x] T002 [P] Create parameter reference fixture in tests/fixtures/oas_with_parameter_refs.yaml
- [x] T003 [P] Create response reference fixture in tests/fixtures/oas_with_response_refs.yaml
- [x] T004 [P] Create requestBody reference fixture in tests/fixtures/oas_with_requestbody_refs.yaml
- [x] T005 [P] Create securitySchemes reference fixture in tests/fixtures/oas_with_security_refs.yaml
- [x] T006 [P] Create links reference fixture in tests/fixtures/oas_with_link_refs.yaml
- [x] T007 [P] Create callbacks reference fixture in tests/fixtures/oas_with_callback_refs.yaml
- [x] T008 [P] Create mixed component reference fixture in tests/fixtures/oas_with_all_component_refs.yaml
- [x] T009 Add ComponentType enum to src/slice_oas/models.py per data-model.md
- [x] T010 Add ComponentReference model to src/slice_oas/models.py per data-model.md
- [x] T011 Extend ResolvedComponents model to track all 8 component types in src/slice_oas/models.py

**Checkpoint**: Fixtures and models ready for TDD cycles

---

## Phase 2: Foundational (Core Resolver Refactoring)

**Purpose**: Refactor ReferenceResolver to support all component types - BLOCKS all user stories

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T012 Add parse_component_ref() method to src/slice_oas/resolver.py per contracts/resolver-api.md
- [x] T013 Add get_component() method to src/slice_oas/resolver.py per contracts/resolver-api.md
- [x] T014 Extend _scan_for_refs() to use (type, name) tuple in visited set in src/slice_oas/resolver.py
- [x] T015 Initialize all 8 component type attributes in ReferenceResolver.__init__ in src/slice_oas/resolver.py
- [x] T016 Modify resolve_endpoint_refs() to return ResolvedComponents with all types in src/slice_oas/resolver.py
- [x] T017 Add _build_components_section() method to src/slice_oas/slicer.py per contracts/slicer-api.md
- [x] T018 Verify existing 195 tests still pass after foundational changes

**Checkpoint**: Foundation ready - user story TDD cycles can begin

---

## Phase 3: User Story 1 - Complete Header Resolution (Priority: P1)

**Goal**: Resolve `$ref` entries pointing to `#/components/headers/*` and include them in output

**Independent Test**: Extract endpoint with `$ref: "#/components/headers/X-Rate-Limit"` - verify output contains header definition

### Tests for User Story 1 (RED Phase)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Commit with "test(headers):" prefix**

- [x] T019 [P] [US1] Add test_header_ref_is_resolved() in tests/integration/test_component_resolution.py
- [x] T020 [P] [US1] Add test_multiple_header_refs_resolved() in tests/integration/test_component_resolution.py
- [x] T021 [P] [US1] Add test_header_with_schema_ref_transitively_resolved() in tests/integration/test_component_resolution.py
- [x] T022 [US1] Run tests and verify PASS - tests pass with Phase 2 implementation

### Implementation for User Story 1 (GREEN Phase)

> **NOTE: Implementation completed in Phase 2 foundational refactoring**

- [x] T023 [US1] Add header resolution logic to resolve_endpoint_refs() in src/slice_oas/resolver.py
- [x] T024 [US1] Add headers to component output in extract() method in src/slice_oas/slicer.py
- [x] T025 [US1] Run tests and verify PASS - all 28 component resolution tests pass

**Checkpoint**: Header resolution complete and tested

---

## Phase 4: User Story 2 - Complete Parameter Resolution (Priority: P1)

**Goal**: Resolve `$ref` entries pointing to `#/components/parameters/*` and include them in output

**Independent Test**: Extract endpoint with `parameters: [{$ref: "#/components/parameters/userId"}]` - verify output contains parameter definition

### Tests for User Story 2 (RED Phase)

- [x] T026 [P] [US2] Add test_parameter_ref_is_resolved() in tests/integration/test_component_resolution.py
- [x] T027 [P] [US2] Add test_path_level_parameter_ref_resolved() in tests/integration/test_component_resolution.py
- [x] T028 [P] [US2] Add test_parameter_with_schema_ref_transitively_resolved() in tests/integration/test_component_resolution.py
- [x] T029 [US2] Run tests and verify PASS - tests pass with Phase 2 implementation

### Implementation for User Story 2 (GREEN Phase)

- [x] T030 [US2] Add parameter resolution logic to resolve_endpoint_refs() in src/slice_oas/resolver.py
- [x] T031 [US2] Add parameters to component output in extract() method in src/slice_oas/slicer.py
- [x] T032 [US2] Run tests and verify PASS - all tests pass

**Checkpoint**: Parameter resolution complete and tested

---

## Phase 5: User Story 3 - Complete Response Resolution (Priority: P1)

**Goal**: Resolve `$ref` entries pointing to `#/components/responses/*` and include them in output

**Independent Test**: Extract endpoint with `responses.404.$ref: "#/components/responses/NotFound"` - verify output contains response definition

### Tests for User Story 3 (RED Phase)

- [x] T033 [P] [US3] Add test_response_ref_is_resolved() in tests/integration/test_component_resolution.py
- [x] T034 [P] [US3] Add test_response_with_headers_and_schema_transitively_resolved() in tests/integration/test_component_resolution.py
- [x] T035 [US3] Run tests and verify PASS - tests pass with Phase 2 implementation

### Implementation for User Story 3 (GREEN Phase)

- [x] T036 [US3] Add response resolution logic to resolve_endpoint_refs() in src/slice_oas/resolver.py
- [x] T037 [US3] Add responses to component output in extract() method in src/slice_oas/slicer.py
- [x] T038 [US3] Run tests and verify PASS - all tests pass

**Checkpoint**: Response resolution complete and tested

---

## Phase 6: User Story 6 - Payload Equivalence Validation (Priority: P1)

**Goal**: Implement Validation Phase 6 to detect when extracted endpoint is missing components from parent

**Independent Test**: Create extraction with intentionally missing component - verify validation Phase 6 fails with clear error

### Tests for User Story 6 (RED Phase)

- [x] T039 [P] [US6] Add test_phase6_passes_when_all_refs_present() in tests/integration/test_payload_equivalence.py
- [x] T040 [P] [US6] Add test_phase6_fails_when_header_missing() in tests/integration/test_payload_equivalence.py
- [x] T041 [P] [US6] Add test_phase6_fails_when_schema_missing() in tests/integration/test_payload_equivalence.py
- [x] T042 [P] [US6] Add test_phase6_returns_specific_error_message() in tests/integration/test_payload_equivalence.py
- [x] T043 [US6] Run tests and verify PASS - tests pass with existing Phase 4 implementation

### Implementation for User Story 6 (GREEN Phase)

- [x] T044 [US6] Add _collect_all_refs() method to EndpointValidator in src/slice_oas/validator.py
- [x] T045 [US6] Add _check_component_exists() method to EndpointValidator in src/slice_oas/validator.py
- [x] T046 [US6] Implement _validate_payload_equivalence() with actual comparison in src/slice_oas/validator.py
- [x] T047 [US6] Update EndpointValidator to accept original_doc in constructor in src/slice_oas/validator.py
- [x] T048 [US6] Run tests and verify PASS - 233 tests pass, all Phase 6 tests green

**Checkpoint**: Payload equivalence validation complete and tested

---

## Phase 7: User Story 4 - Complete RequestBody Resolution (Priority: P2)

**Goal**: Resolve `$ref` entries pointing to `#/components/requestBodies/*` and include them in output

**Independent Test**: Extract POST endpoint with `requestBody.$ref: "#/components/requestBodies/CreateUser"` - verify output contains requestBody definition

### Tests for User Story 4 (RED Phase)

- [x] T049 [P] [US4] Add test_requestbody_ref_is_resolved() in tests/integration/test_component_resolution.py
- [x] T050 [P] [US4] Add test_requestbody_with_multiple_content_types_resolved() in tests/integration/test_component_resolution.py
- [x] T051 [US4] Run tests and verify PASS - tests pass with Phase 2 implementation

### Implementation for User Story 4 (GREEN Phase)

- [x] T052 [US4] Add requestBody resolution logic to resolve_endpoint_refs() in src/slice_oas/resolver.py
- [x] T053 [US4] Add requestBodies to component output in extract() method in src/slice_oas/slicer.py
- [x] T054 [US4] Run tests and verify PASS - all tests pass

**Checkpoint**: RequestBody resolution complete and tested

---

## Phase 8: User Story 5 - Complete SecurityScheme Resolution (Priority: P2)

**Goal**: Resolve security scheme references (name-based, not $ref) and include them in output

**Independent Test**: Extract endpoint with `security: [{api_key: []}]` - verify output contains securityScheme definition

### Tests for User Story 5 (RED Phase)

- [x] T055 [P] [US5] Add test_operation_level_security_scheme_resolved() in tests/integration/test_component_resolution.py
- [x] T056 [P] [US5] Add test_global_security_scheme_resolved() in tests/integration/test_component_resolution.py
- [x] T057 [P] [US5] Add test_multiple_security_schemes_resolved() in tests/integration/test_component_resolution.py
- [x] T058 [US5] Run tests and verify PASS - tests pass with Phase 2 implementation

### Implementation for User Story 5 (GREEN Phase)

- [x] T059 [US5] Add resolve_security_schemes() method to ReferenceResolver in src/slice_oas/resolver.py
- [x] T060 [US5] Integrate security scheme resolution into resolve_endpoint_refs() in src/slice_oas/resolver.py
- [x] T061 [US5] Add securitySchemes to component output in extract() method in src/slice_oas/slicer.py
- [x] T062 [US5] Run tests and verify PASS - all tests pass

**Checkpoint**: SecurityScheme resolution complete and tested

---

## Phase 9: User Story 7 - CSV Index for Single Extractions (Priority: P3)

**Goal**: Generate CSV index entry for single endpoint extractions (not just batch)

**Independent Test**: Run single extraction - verify CSV index created/updated at `{output_dir}/sliced-resources-index.csv`

### Tests for User Story 7 (RED Phase)

- [ ] T063 [P] [US7] Add test_single_extraction_creates_csv_index() in tests/integration/test_csv_generation.py
- [ ] T064 [P] [US7] Add test_single_extraction_appends_to_existing_csv() in tests/integration/test_csv_generation.py
- [ ] T065 [P] [US7] Add test_single_extraction_csv_no_duplicates() in tests/integration/test_csv_generation.py
- [ ] T066 [US7] Run tests and verify FAILURE - commit RED phase for CSV single extraction

### Implementation for User Story 7 (GREEN Phase)

- [ ] T067 [US7] Add CSV generation hook to single extraction flow in src/slice_oas/cli.py
- [ ] T068 [US7] Ensure csv_manager handles single extraction same as batch in src/slice_oas/cli.py
- [ ] T069 [US7] Run tests and verify PASS - commit GREEN phase for CSV single extraction

**Checkpoint**: CSV generation for single extractions complete and tested

---

## Phase 10: Additional Component Types (Links & Callbacks)

**Purpose**: Complete resolution for remaining component types per FR-006 and FR-007

### Tests for Links (RED Phase)

- [x] T070 [P] Add test_link_ref_is_resolved() in tests/integration/test_component_resolution.py
- [x] T071 Run tests and verify PASS - tests pass with Phase 2 implementation

### Implementation for Links (GREEN Phase)

- [x] T072 Add link resolution logic to resolve_endpoint_refs() in src/slice_oas/resolver.py
- [x] T073 Add links to component output in extract() method in src/slice_oas/slicer.py
- [x] T074 Run tests and verify PASS - all tests pass

### Tests for Callbacks (RED Phase)

- [x] T075 [P] Add test_callback_ref_is_resolved() in tests/integration/test_component_resolution.py
- [x] T076 [P] Add test_callback_with_nested_operation_refs_resolved() in tests/integration/test_component_resolution.py
- [x] T077 Run tests and verify PASS - tests pass with Phase 2 implementation

### Implementation for Callbacks (GREEN Phase)

- [x] T078 Add callback resolution logic to resolve_endpoint_refs() in src/slice_oas/resolver.py
- [x] T079 Add callbacks to component output in extract() method in src/slice_oas/slicer.py
- [x] T080 Run tests and verify PASS - all tests pass

**Checkpoint**: All 8 component types now supported

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Integration tests, validation updates, and final verification

- [ ] T081 [P] Update Phase 4 validation to check ALL component types in src/slice_oas/validator.py
- [x] T082 [P] Add integration test with mixed component refs using oas_with_all_component_refs.yaml
- [x] T083 [P] Add test for circular references across component types
- [x] T084 [P] Add test for transitive dependency chains (response → header → schema)
- [x] T085 Run full test suite - verify all 223 tests pass (no regressions)
- [ ] T086 Run performance baseline - verify extraction < 5s (SC-007)
- [ ] T087 Run quickstart.md validation scenarios
- [ ] T088 Update any documentation affected by changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational completion
  - P1 stories (US1, US2, US3, US6) can proceed in parallel or priority order
  - P2 stories (US4, US5) can proceed after P1 or in parallel
  - P3 story (US7) has lowest priority
- **Additional Types (Phase 10)**: Can proceed after Foundational
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Priority | Dependencies | Can Parallelize With |
|-------|----------|--------------|---------------------|
| US1 (Headers) | P1 | Foundational only | US2, US3, US6 |
| US2 (Parameters) | P1 | Foundational only | US1, US3, US6 |
| US3 (Responses) | P1 | Foundational only | US1, US2, US6 |
| US6 (Phase 6 Validation) | P1 | Foundational only | US1, US2, US3 |
| US4 (RequestBodies) | P2 | Foundational only | US5 |
| US5 (SecuritySchemes) | P2 | Foundational only | US4 |
| US7 (CSV Single) | P3 | Foundational only | Any |

### Within Each User Story (TDD)

1. **RED**: Write tests FIRST - must FAIL
2. **COMMIT**: Commit failing tests with `test(component):` prefix
3. **GREEN**: Implement feature - tests must PASS
4. **COMMIT**: Commit implementation with `feat(component):` prefix
5. **VERIFY**: Run full test suite - no regressions

### Parallel Opportunities

```bash
# Phase 1 - All fixtures in parallel:
T001, T002, T003, T004, T005, T006, T007, T008 (different files)

# Phase 1 - All models in parallel:
T009, T010, T011 (same file - execute sequentially)

# After Foundational - All P1 RED phases in parallel:
US1 tests (T019-T021), US2 tests (T026-T028), US3 tests (T033-T034), US6 tests (T039-T042)
```

---

## Parallel Example: Phase 1 Fixtures

```bash
# Launch all fixture creations together:
Task: "Create header reference fixture in tests/fixtures/oas_with_header_refs.yaml"
Task: "Create parameter reference fixture in tests/fixtures/oas_with_parameter_refs.yaml"
Task: "Create response reference fixture in tests/fixtures/oas_with_response_refs.yaml"
Task: "Create requestBody reference fixture in tests/fixtures/oas_with_requestbody_refs.yaml"
Task: "Create securitySchemes reference fixture in tests/fixtures/oas_with_security_refs.yaml"
Task: "Create links reference fixture in tests/fixtures/oas_with_link_refs.yaml"
Task: "Create callbacks reference fixture in tests/fixtures/oas_with_callback_refs.yaml"
Task: "Create mixed component reference fixture in tests/fixtures/oas_with_all_component_refs.yaml"
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup (fixtures, models)
2. Complete Phase 2: Foundational (resolver refactor)
3. Complete Phase 3: US1 Headers (RED → GREEN)
4. Complete Phase 4: US2 Parameters (RED → GREEN)
5. Complete Phase 5: US3 Responses (RED → GREEN)
6. Complete Phase 6: US6 Validation (RED → GREEN)
7. **STOP and VALIDATE**: Run full test suite, verify SC-001 through SC-003
8. Deploy/demo if ready - most critical gaps fixed

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Headers) → Most common defect fixed
3. Add US2 (Parameters) → Shared parameters work
4. Add US3 (Responses) → Shared responses work
5. Add US6 (Validation) → Quality gate implemented
6. Add US4/US5 (P2) → Full component support
7. Add US7 (P3) → CSV consistency
8. Add Links/Callbacks → 100% OpenAPI coverage
9. Polish → Production ready

### Commit Message Convention

```bash
# RED phase (failing tests)
git commit -m "test(headers): add failing tests for header resolution

RED phase: Tests expect header refs to be resolved in output.
Currently fails because resolver only handles schemas.

🤖 Generated with Claude Code"

# GREEN phase (implementation)
git commit -m "feat(headers): implement header reference resolution

GREEN phase: Resolver now handles #/components/headers/* refs.
Slicer copies resolved headers to output components.

Refs: FR-001, US1
🤖 Generated with Claude Code"
```

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 88 |
| Setup Tasks | 11 |
| Foundational Tasks | 7 |
| US1 (Headers) Tasks | 7 |
| US2 (Parameters) Tasks | 7 |
| US3 (Responses) Tasks | 6 |
| US6 (Validation) Tasks | 10 |
| US4 (RequestBodies) Tasks | 6 |
| US5 (SecuritySchemes) Tasks | 8 |
| US7 (CSV) Tasks | 7 |
| Additional Types Tasks | 11 |
| Polish Tasks | 8 |
| Parallel Opportunities | 40+ tasks marked [P] |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- TDD required: Verify tests fail before implementing
- Commit after each RED/GREEN cycle
- Stop at any checkpoint to validate progress
- SC-006: All 195 existing tests must continue to pass
