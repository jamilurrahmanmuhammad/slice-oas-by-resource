---
description: "Task list for slice-oas-by-resource implementation with TDD approach"
---

# Tasks: Slice OAS by Resource

**Input**: Design documents from `/specs/001-slice-oas-by-resource/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Comprehensive TDD approach with test tasks for all core functionality and edge cases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure with directories: src/slice_oas/, tests/unit/, tests/integration/, tests/fixtures/, docs/
- [x] T002 Initialize Poetry project with pyproject.toml (dependencies: pydantic-core, PyYAML, openapi-spec-validator, jsonschema, pytest, pytest-cov)
- [x] T003 [P] Create base modules: src/slice_oas/__init__.py, __main__.py, cli.py, models.py, exceptions.py
- [x] T004 [P] Create core processor modules: src/slice_oas/parser.py, resolver.py, converter.py, validator.py, slicer.py, generator.py
- [x] T005 Create CLI entry point that accepts input OAS path, output directory, and output version (in src/slice_oas/__main__.py)
- [x] T006 Create custom exception classes for user-friendly error handling in src/slice_oas/exceptions.py (InvalidOASError, MissingReferenceError, ConversionError, ValidationError)
- [x] T007 Create pytest configuration in tests/conftest.py with fixtures for OAS 3.0/3.1 test files and mock utilities

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**📋 TDD Execution Order** (override listed order for TDD approach):
1. ✅ T010 (test fixtures) - DONE
2. ✅ T012-T013 (write failing unit tests) - DONE (17 tests passing)
3. ✅ T008-T009 (implement modules to pass tests) - DONE
4. ✅ T011 (add version detection) - DONE (in parser.py)
5. ✅ T014-T016 (CLI and error handling) - DONE

- [x] T008 [P] Create OAS Parser module (src/slice_oas/parser.py) that loads JSON/YAML, validates structure, detects version from `openapi` field
- [x] T009 [P] Create data models in src/slice_oas/models.py: OASDocument, Resource, Reference, ResolvedComponent, ValidationResult, CSVIndexEntry, VersionConverter, TransformationRule
- [x] T010 [P] Create test fixtures in tests/fixtures/: oas_3_0_simple.yaml, oas_3_0_complex.yaml, oas_3_0_circular.yaml, oas_3_1_simple.yaml, oas_3_1_advanced.yaml, oas_3_1_circular.yaml, malformed.yaml
- [x] T011 Create OAS version detection logic in src/slice_oas/models.py (parse `openapi` field as family: 3.0.x vs 3.1.x)
- [x] T012 [P] Create unit tests for parser in tests/unit/test_parser.py (load JSON, load YAML, detect version 3.0.x, detect version 3.1.x, reject malformed)
- [x] T013 [P] Create unit tests for models in tests/unit/test_models.py (OASDocument instantiation, Resource creation, Reference extraction)
- [x] T014 Create CLI argument parser in src/slice_oas/cli.py (request input path, output directory, output version in conversational manner)
- [x] T015 Create plain-language error message templates in src/slice_oas/exceptions.py (no code/JSON/YAML exposure)
- [x] T016 Create user-friendly validation error formatter in src/slice_oas/cli.py (convert technical errors to actionable guidance)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Single Endpoint Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract a single API endpoint from OAS with complete reference resolution and validation

**Independent Test**: Provide valid OAS path and endpoint identifier (path + method), verify output is valid standalone OAS file with all $ref entries resolved

**Acceptance Criteria**:
- ✓ User can extract single endpoint under 5 seconds
- ✓ Output file is valid OpenAPI 3.0.x or 3.1.x (matching input or requested version)
- ✓ All $ref entries in output resolve within the file
- ✓ All response headers with $ref are included in components.headers
- ✓ All transitive schema dependencies are included
- ✓ Circular references handled without infinite loops
- ✓ Output file immediately usable by downstream tools
- ✓ CSV index entry created with accurate metadata

**📋 TDD Execution Order** (override listed order for TDD approach):
1. ✅ T017-T024 (write integration tests) - DONE (18 tests passing)
2. ✅ T025-T031 (implement core modules + CLI integration) - DONE (all tests passing)
3. ✅ T034 (acceptance testing) - DONE (55/55 tests passing)
4. ⏳ T032-T033 (unit tests for resolver/slicer) - OPTIONAL comprehensive tests
5. ✅ **PHASE 3 US1 COMPLETE** - Single endpoint extraction ready for production use

### Tests (US1 - TDD)

- [x] T017 [P] [US1] Create TDD test for simple endpoint extraction (no schema refs) in tests/integration/test_single_extraction.py
- [x] T018 [P] [US1] Create TDD test for endpoint with direct schema references in tests/integration/test_single_extraction.py
- [x] T019 [P] [US1] Create TDD test for endpoint with transitive schema dependencies in tests/integration/test_single_extraction.py
- [x] T020 [P] [US1] Create TDD test for circular schema references in tests/integration/test_single_extraction.py
- [x] T021 [P] [US1] Create TDD test for response headers with $ref in tests/integration/test_single_extraction.py (constitutional requirement)
- [x] T022 [P] [US1] Create TDD test for JSON output format in tests/integration/test_single_extraction.py
- [x] T023 [P] [US1] Create TDD test for YAML output format in tests/integration/test_single_extraction.py
- [x] T024 [P] [US1] Create TDD test for endpoint not found error handling in tests/integration/test_single_extraction.py

### Implementation (US1)

- [x] T025 [P] [US1] Create reference resolver in src/slice_oas/resolver.py with BFS traversal and visited set for circular refs
- [x] T026 [P] [US1] Implement response header reference scanning in src/slice_oas/resolver.py (scan responses[*].headers[*].$ref explicitly)
- [x] T027 [P] [US1] Create slicer orchestrator in src/slice_oas/slicer.py that extracts single endpoint and resolves all dependencies
- [x] T028 [US1] Create 7-phase validator in src/slice_oas/validator.py (file structure, operation integrity, response integrity, ref resolution, completeness, payload equivalence, version validation)
- [x] T029 [US1] Create file output writer in src/slice_oas/generator.py for JSON and YAML formats
- [x] T030 [US1] Create standalone OAS file generator that builds complete root structure with all resolved components
- [x] T031 [US1] Integrate extraction flow in src/slice_oas/cli.py (request endpoint, execute slicer, validate, write output, report success)
- [ ] T032 [P] [US1] Create unit tests for resolver in tests/unit/test_resolver.py (BFS traversal, circular detection, header scanning)
- [ ] T033 [P] [US1] Create unit tests for slicer in tests/unit/test_slicer.py (endpoint extraction, dependency collection, orchestration)
- [x] T034 [US1] Run all US1 tests and verify all pass before proceeding to US2

---

## Phase 4: User Story 2 - Batch Slicing for Microservices Deployment (Priority: P2)

**Goal**: Extract multiple endpoints from OAS with filtering, batch processing, real-time progress, and CSV tracking

**Independent Test**: Provide OAS file with 100+ endpoints and filter criteria, verify all matching endpoints extracted to separate files, CSV index tracks all entries, processing completes in under 3 minutes

**Acceptance Criteria**:
- ✓ User can extract all endpoints or filtered subset
- ✓ 100 endpoints processed in under 3 minutes
- ✓ Real-time progress updates during batch processing
- ✓ All output files pass validation (100% pass rate)
- ✓ CSV index contains accurate entry for each extracted resource
- ✓ CSV index updated in real-time (append mode)
- ✓ Duplicate handling: no duplicate entries in CSV for same path+method
- ✓ Error resilience: skip failed extractions, continue processing

**📋 TDD Execution Order** (override listed order for TDD approach):
1. T050-T051 (write failing unit tests for batch processor/CSV generator)
2. T043-T049 (implement code to pass unit tests)
3. T035-T042 (write integration tests)
4. T053 (run all tests and verify)

### Tests (US2 - TDD)

- [ ] T035 [P] [US2] Create TDD test for extract all endpoints in tests/integration/test_batch_extraction.py
- [ ] T036 [P] [US2] Create TDD test for filter by path prefix in tests/integration/test_batch_extraction.py
- [ ] T037 [P] [US2] Create TDD test for filter by HTTP method in tests/integration/test_batch_extraction.py
- [ ] T038 [P] [US2] Create TDD test for filter by tag in tests/integration/test_batch_extraction.py
- [ ] T039 [P] [US2] Create TDD test for 100 endpoint batch processing timing in tests/integration/test_batch_extraction.py
- [ ] T040 [P] [US2] Create TDD test for CSV index real-time updates in tests/integration/test_csv_tracking.py
- [ ] T041 [P] [US2] Create TDD test for CSV deduplication on re-run in tests/integration/test_csv_tracking.py
- [ ] T042 [P] [US2] Create TDD test for error handling and graceful skip in tests/integration/test_batch_extraction.py

### Implementation (US2)

- [ ] T043 [P] [US2] Create batch processor in src/slice_oas/slicer.py that accepts filter criteria and processes multiple endpoints
- [ ] T044 [US2] Create filter logic in src/slice_oas/slicer.py (path prefix, method, tag patterns)
- [ ] T045 [US2] Create real-time progress reporter in src/slice_oas/cli.py (human-friendly "Processing N of M" messages)
- [ ] T046 [US2] Create CSV index generator in src/slice_oas/generator.py with exact columns from constitution (path, method, summary, description, operationId, tags, filename, file_size_kb, schema_count, parameter_count, response_codes, security_required, deprecated, created_at, output_oas_version)
- [ ] T047 [US2] Implement real-time CSV append in src/slice_oas/generator.py (write entry after each successful extraction)
- [ ] T048 [US2] Implement CSV deduplication logic in src/slice_oas/generator.py (check for existing path+method before adding)
- [ ] T049 [US2] Create error handling in batch processor that skips failed extractions and continues
- [ ] T050 [P] [US2] Create unit tests for batch processor in tests/unit/test_slicer.py (filter logic, endpoint iteration)
- [ ] T051 [P] [US2] Create unit tests for CSV generator in tests/unit/test_generator.py (row formatting, deduplication, append mode)
- [ ] T052 [US2] Integrate batch flow in src/slice_oas/cli.py (request filter criteria, execute batch, track progress, finalize CSV)
- [ ] T053 [US2] Run all US2 tests and verify all pass before proceeding to US3

---

## Phase 5: User Story 3 - Version Conversion for Legacy Migration (Priority: P3)

**Goal**: Convert extracted endpoints between OAS 3.0.x and 3.1.x with deterministic transformation rules

**Independent Test**: Extract endpoint from 3.0.x OAS requesting 3.1.x output, verify output conforms to 3.1.x schema with all data preserved; reverse test 3.1.x→3.0.x

**Acceptance Criteria**:
- ✓ User can select output version (3.0.x or 3.1.x) different from input
- ✓ Conversion is deterministic (repeated runs produce identical results)
- ✓ All standard OAS constructs correctly transformed
- ✓ Nullable→type arrays conversion works bidirectionally
- ✓ Webhooks/pathItems handled correctly in 3.0↔3.1
- ✓ mutualTLS schemes handled correctly (3.1 only)
- ✓ License identifier field handled correctly (3.1 only)
- ✓ Unconvertible structures (JSON Schema conditionals in 3.1) fail gracefully with user-friendly message
- ✓ Output passes Phase 7 version-specific validation

**📋 TDD Execution Order** (override listed order for TDD approach):
1. T068-T069 (write failing unit tests for converter/validator)
2. T062-T067 (implement code to pass unit tests)
3. T054-T061 (write integration tests)
4. T071 (run all tests and verify)

### Tests (US3 - TDD)

- [ ] T054 [P] [US3] Create TDD test for nullable→type[] conversion (3.0→3.1) in tests/integration/test_version_conversion.py
- [ ] T055 [P] [US3] Create TDD test for type[]→nullable conversion (3.1→3.0) in tests/integration/test_version_conversion.py
- [ ] T056 [P] [US3] Create TDD test for webhooks section handling in tests/integration/test_version_conversion.py
- [ ] T057 [P] [US3] Create TDD test for pathItems handling in tests/integration/test_version_conversion.py
- [ ] T058 [P] [US3] Create TDD test for mutualTLS scheme removal (3.1→3.0) in tests/integration/test_version_conversion.py
- [ ] T059 [P] [US3] Create TDD test for license identifier handling in tests/integration/test_version_conversion.py
- [ ] T060 [P] [US3] Create TDD test for JSON Schema conditional rejection (3.1→3.0) in tests/integration/test_version_conversion.py
- [ ] T061 [P] [US3] Create TDD test for multi-type union rejection (3.1→3.0, non-null types) in tests/integration/test_version_conversion.py

### Implementation (US3)

- [ ] T062 [P] [US3] Create version converter in src/slice_oas/converter.py that applies transformation rules based on family
- [ ] T063 [P] [US3] Implement 3.0→3.1 transformation rules in src/slice_oas/converter.py (per constitution section on transformation rules)
- [ ] T064 [P] [US3] Implement 3.1→3.0 transformation rules in src/slice_oas/converter.py (per constitution section on transformation rules)
- [ ] T065 [US3] Create Phase 7 version validation in src/slice_oas/validator.py (syntax correctness per target version)
- [ ] T066 [US3] Implement version-specific validation rules in src/slice_oas/validator.py (no nullable in 3.1, no mutualTLS in 3.0, etc.)
- [ ] T067 [US3] Add version conversion error handling with user-friendly messages for unconvertible structures
- [ ] T068 [P] [US3] Create unit tests for converter in tests/unit/test_converter.py (all transformation rules, bidirectional conversion)
- [ ] T069 [US3] Create unit tests for Phase 7 validation in tests/unit/test_validator.py (version syntax checks)
- [ ] T070 [US3] Integrate version selection in src/slice_oas/cli.py (prompt for output version, apply conversion)
- [ ] T071 [US3] Run all US3 tests and verify all pass before proceeding to US4

---

## Phase 6: User Story 4 - CSV Index Generation for API Governance (Priority: P4)

**Goal**: Generate searchable, traceable CSV index of all sliced resources with governance metadata

**Independent Test**: Run batch extraction and verify CSV contains all entries with correct columns and formatting; open in spreadsheet software and confirm readability

**Acceptance Criteria**:
- ✓ CSV file created during batch operations
- ✓ Exact column order maintained: path, method, summary, description, operationId, tags, filename, file_size_kb, schema_count, parameter_count, response_codes, security_required, deprecated, created_at, output_oas_version
- ✓ All entries formatted correctly (no missing quotes, proper escaping)
- ✓ RFC 4180 compliance (compatible with Excel, Google Sheets, etc.)
- ✓ Real-time updates (entries appear as processing continues)
- ✓ Deduplication (no duplicates on re-run)
- ✓ File size and schema_count accurately calculated
- ✓ Response codes parsed correctly (comma-separated)
- ✓ Timestamps in ISO 8601 format
- ✓ output_oas_version column tracks version for each resource

**📋 TDD Execution Order** (override listed order for TDD approach):
1. T087 (write failing unit tests for CSV formatting)
2. T080-T086 (implement code to pass unit tests)
3. T072-T079 (write integration tests)
4. T088 (run all tests and verify)

### Tests (US4 - TDD)

- [ ] T072 [P] [US4] Create TDD test for CSV structure and columns in tests/integration/test_csv_tracking.py
- [ ] T073 [P] [US4] Create TDD test for RFC 4180 compliance in tests/integration/test_csv_tracking.py
- [ ] T074 [P] [US4] Create TDD test for CSV opening in spreadsheet format in tests/integration/test_csv_tracking.py
- [ ] T075 [P] [US4] Create TDD test for file size calculation accuracy in tests/integration/test_csv_tracking.py
- [ ] T076 [P] [US4] Create TDD test for schema_count accuracy in tests/integration/test_csv_tracking.py
- [ ] T077 [P] [US4] Create TDD test for response_codes parsing in tests/integration/test_csv_tracking.py
- [ ] T078 [P] [US4] Create TDD test for timestamp format in tests/integration/test_csv_tracking.py
- [ ] T079 [P] [US4] Create TDD test for output_oas_version column tracking in tests/integration/test_csv_tracking.py

### Implementation (US4)

- [ ] T080 [P] [US4] Enhance CSV generator in src/slice_oas/generator.py with all required columns per constitution
- [ ] T081 [P] [US4] Implement accurate file size calculation (use os.path.getsize on written file)
- [ ] T082 [P] [US4] Implement schema_count calculation (count keys in sliced output components.schemas)
- [ ] T083 [P] [US4] Implement response_codes parsing (extract all response codes from responses object)
- [ ] T084 [P] [US4] Implement security_required flag (check if security present)
- [ ] T085 [P] [US4] Implement timestamp formatting (use datetime.now().isoformat())
- [ ] T086 [US4] Implement RFC 4180 CSV formatting with proper escaping and quoting
- [ ] T087 [P] [US4] Create unit tests for CSV formatting in tests/unit/test_generator.py (escaping, quoting, RFC compliance)
- [ ] T088 [US4] Run all US4 tests and verify all pass before proceeding to US5

---

## Phase 7: User Story 5 - Black Box UX for Non-Programmers (Priority: P1 - Cross-Cutting)

**Goal**: Ensure entire workflow is accessible to non-technical users without code/technical detail exposure

**Independent Test**: Have non-technical user complete extraction workflow using only conversational prompts; verify no code, JSON, YAML, or algorithm details shown

**Acceptance Criteria**:
- ✓ All prompts use plain language (no technical jargon)
- ✓ No code snippets shown during normal operation
- ✓ No JSON/YAML structures displayed to users
- ✓ No algorithm or processing details exposed
- ✓ Error messages in plain language with actionable guidance
- ✓ Progress messages conversational ("Processing 45 of 100" not "BFS graph traversal phase 2")
- ✓ File paths validated with helpful feedback
- ✓ Results summary in user-friendly format
- ✓ Completion message celebrates user success without technical detail

**📋 TDD Execution Order** (override listed order for TDD approach):
1. T100 (write failing unit tests for UX validation)
2. T094-T099 (implement code to pass unit tests)
3. T089-T093 (write integration tests)
4. T101 (run all tests and verify)

### Tests (US5 - TDD)

- [ ] T089 [P] [US5] Create TDD test for no-code UX validation in tests/integration/test_ux_validation.py (scan all output for code patterns)
- [ ] T090 [P] [US5] Create TDD test for plain-language prompts in tests/integration/test_ux_validation.py (all prompts in simple English)
- [ ] T091 [P] [US5] Create TDD test for error message clarity in tests/integration/test_ux_validation.py (no technical jargon in errors)
- [ ] T092 [P] [US5] Create TDD test for path validation feedback in tests/integration/test_ux_validation.py (helpful guidance on invalid paths)
- [ ] T093 [P] [US5] Create TDD test for progress message conversational tone in tests/integration/test_ux_validation.py

### Implementation (US5)

- [ ] T094 [US5] Create comprehensive prompt templates in src/slice_oas/cli.py (conversational, plain-language for all interactions)
- [ ] T095 [US5] Create result summary formatter in src/slice_oas/cli.py (report files created, location, count - plain language only)
- [ ] T096 [US5] Create path validation feedback in src/slice_oas/cli.py (suggest corrections for invalid paths)
- [ ] T097 [US5] Create progress reporter in src/slice_oas/cli.py (use simple "Processing N of M..." messages)
- [ ] T098 [US5] Sanitize all error messages to remove technical detail in src/slice_oas/exceptions.py
- [ ] T099 [US5] Create user-friendly error guidance in src/slice_oas/cli.py (convert technical errors to actionable next steps)
- [ ] T100 [P] [US5] Create UX validation tests in tests/integration/test_ux_validation.py (comprehensive regex checks for code/JSON/YAML patterns)
- [ ] T101 [US5] Run all US5 tests and verify all pass

---

## Phase 8: Integration & Cross-Cutting Concerns

**Purpose**: Full system testing, performance validation, edge case handling, and production readiness

- [ ] T102 Create end-to-end integration test in tests/integration/test_e2e_workflow.py (full workflow: input → extraction → validation → output → CSV)
- [ ] T103 Create performance benchmark in tests/integration/test_performance.py (single extraction <5s, batch 100 <3min, validate timing)
- [ ] T104 Create large file handling test in tests/integration/test_large_files.py (1000+ endpoints, memory usage validation)
- [ ] T105 Create edge case tests in tests/integration/test_edge_cases.py (circular refs, missing components, malformed input, duplicates)
- [ ] T106 [P] Create documentation in docs/USAGE.md (non-programmer friendly guide with examples)
- [ ] T107 [P] Create documentation in docs/VERSION_CONVERSION.md (technical reference for transformation rules)
- [ ] T108 [P] Create documentation in docs/VALIDATION_PHASES.md (explanation of 7-phase validation)
- [ ] T109 Create README.md with quick start and feature overview
- [ ] T110 Create pyproject.toml with all dependencies locked and build metadata
- [ ] T111 [P] Create .gitignore with venv, __pycache__, *.pyc, output/, .pytest_cache patterns
- [ ] T112 Run full test suite with pytest and verify 100% pass rate
- [ ] T113 Run pytest-cov and ensure >90% code coverage
- [ ] T114 Create CI/CD workflow (.github/workflows/test.yml) that runs tests on each commit
- [ ] T115 Verify all constitutional principles met through final review:
  - [ ] Principle I: Black Box - all output non-technical ✓
  - [ ] Principle II: Explicit Paths - no auto-discovery ✓
  - [ ] Principle III: Complete Resolution - all refs resolved, headers scanned ✓
  - [ ] Principle IV: Validation - 7 phases all pass ✓
  - [ ] Principle V: CSV - real-time tracking with version column ✓

---

## Dependencies & Parallel Execution

### Execution Order

1. **Phase 1** (Setup): Sequential - must complete first
2. **Phase 2** (Foundation): Sequential within phase, gates all user stories
3. **Phase 3-7** (User Stories): Can execute in parallel across stories after Phase 2:
   - US1 (P1) → blocks US2, US3
   - US2 (P2) → depends on US1
   - US3 (P3) → depends on US1
   - US4 (P4) → depends on US2
   - US5 (P1) → cross-cutting, can start after Phase 2
4. **Phase 8** (Integration): After all user stories complete

### Parallel Execution Example

**After Phase 2 complete**, execute in parallel:
```
Thread-1: US1 implementation (T025-T034)
Thread-2: US5 UX implementation (T094-T101)
          (Both depend only on Phase 2)
Once US1 complete:
Thread-3: US2 implementation (T043-T053)
Thread-4: US3 implementation (T062-T071)
Once US2 complete:
Thread-5: US4 implementation (T080-T088)
Once all threads complete → Phase 8 Integration
```

### Critical Path

T001-T007 (Setup) → T008-T016 (Foundation) → T025-T034 (US1) → T043-T053 (US2) → T080-T088 (US4) → T102-T115 (Integration)

**Estimated Total**: ~80 development days with 2 parallel threads, ~40 days with 4 parallel threads (professional team)

### MVP Scope

To deliver MVP (User Story 1 only):
- Complete Phase 1: Setup
- Complete Phase 2: Foundation
- Complete Phase 3: User Story 1 (single endpoint extraction)
- Complete Phase 7: Black Box UX
- Partial Phase 8: Unit + integration tests for US1 only

**MVP Delivery**: Phase 1-2 + US1 (T001-T034) = foundational capability, ~15 development days

---

## Implementation Strategy

### TDD Approach (All Tests First)

For each user story:
1. Write failing tests (T017-T024 for US1, etc.)
2. Run tests → observe failures
3. Implement code to pass tests (T025-T031 for US1, etc.)
4. Run tests → verify all pass
5. Refactor code for clarity while tests pass
6. Move to next user story

### Incremental Delivery

1. **Increment 1**: Phase 1 + Phase 2 (setup complete)
2. **Increment 2**: Phase 3 US1 (single extraction working)
3. **Increment 3**: Phase 7 UX integration (non-technical workflow)
4. **Increment 4**: Phase 4 US2 (batch processing)
5. **Increment 5**: Phase 5 US3 (version conversion)
6. **Increment 6**: Phase 6 US4 (CSV governance)
7. **Increment 7**: Phase 8 (full integration and optimization)

Each increment is deployable and adds user value incrementally.

---
