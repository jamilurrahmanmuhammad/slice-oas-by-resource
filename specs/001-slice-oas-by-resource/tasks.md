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
- ✓ Parallel processing (4x faster than sequential)
- ✓ Error resilience: skip failed extractions, continue processing

**STATUS**: ✅ **COMPLETE** (T035-T053, all 19 tasks done, 79/79 tests passing)

---

## Phase 5: User Story 3 - Version Conversion for Legacy Migration (Priority: P3)

**Goal**: Convert extracted endpoints between OAS 3.0.x and 3.1.x with deterministic transformation rules and batch processing integration

**Independent Test**: Extract endpoint from 3.0.x OAS requesting 3.1.x output, verify output conforms to 3.1.x schema with all data preserved; reverse test 3.1.x→3.0.x; verify batch conversion handles 100+ endpoints in <3min

**Acceptance Criteria**:
- ✓ User can select output version (3.0.x or 3.1.x) different from input
- ✓ Conversion is deterministic (repeated runs produce identical results)
- ✓ All standard OAS constructs correctly transformed (nullable, discriminator, webhooks)
- ✓ Nullable→type arrays conversion works bidirectionally
- ✓ Webhooks handled correctly (preserved in 3.1, removed with warning in 3.0)
- ✓ Discriminator properties updated correctly (propertyName→mapping in 3.1)
- ✓ Unconvertible structures fail gracefully with user-friendly messages
- ✓ Batch conversion with filtering (--batch --filter --convert-version)
- ✓ Output passes post-conversion validation (openapi-spec-validator)
- ✓ Performance: 100 endpoints converted in <180 seconds

**📋 TDD Execution Order** (override listed order for TDD approach):
1. T054 (transformation rules library)
2. T055-T056 (data models + converter implementation)
3. T057-T062 (CLI + batch integration + validation)
4. T063 (test framework setup)
5. T064-T073 (write integration tests, all passing)

### Implementation (T054-T063): Core Version Conversion

- [x] T054 [P] [US3] Create transformation rules library at `src/slice_oas/transformation_rules.json` ✅
  - 3.0→3.1 rules: nullable→type array, discriminator updates, webhooks support, schema composition
  - 3.1→3.0 rules: type array→nullable, webhooks removal, examples simplification
  - Format: JSON array of rule objects with pattern, action, scope
  - Example rules: "Nullable to Type Array" (pattern: nullable=true, action: convert to type array)

- [x] T055 [P] [US3] Extend data models in `src/slice_oas/models.py` ✅
  - Add `VersionConversionRequest` dataclass: source_version, target_version, transformation_rules, strict_mode, preserve_examples
  - Add `ConversionResult` dataclass: success, source_version, target_version, converted_document, warnings, errors, elapsed_time
  - Add `TransformationRule` dataclass: pattern, action, scope, priority
  - Pydantic validation for each model with sample inputs

- [x] T056 [US3] Implement version conversion logic in `src/slice_oas/converter.py` ✅
  - Create `VersionConverter` class with methods: convert_30_to_31(doc), convert_31_to_30(doc), apply_rule(doc, rule), validate_converted(doc, target_version)
  - Implement nullable transformation: detect `nullable: true`, convert to `type: [type, "null"]`
  - Implement discriminator updates: map propertyName to mapping (3.1 enhancement)
  - Implement webhook handling: preserve in 3.1, remove with warning in 3.0
  - Deterministic rule ordering: sort rules by priority for idempotent output
  - Return `ConversionResult` with success flag, warnings, errors

- [x] T057 [P] [US3] Extend CLI argument parsing in `src/slice_oas/cli.py` ✅
  - Add `--convert-version VERSION` argument (accepts 3.0 or 3.1 as target)
  - Add `--strict` flag for strict mode (fail on unconvertible constructs, default: permissive)
  - Add `--preserve-examples` flag (keep all examples, default: true)
  - Validation: Ensure target version is valid; check source vs target

- [x] T058 [P] [US3] Integrate version converter into batch processor in `src/slice_oas/batch_processor.py` ✅
  - Extend `BatchProcessor.process()` to call `VersionConverter` if `request.convert_version` is set
  - Add conversion step after extraction, before output writing
  - Update progress callback: "Converting 5/7 endpoints (71%): GET /users"
  - Handle conversion errors: collect per endpoint, continue processing

- [x] T059 [US3] Add conversion progress reporting in `src/slice_oas/progress.py` ✅
  - Extend `ProgressReporter` to track conversion phase: extraction → conversion → validation
  - Update callback format: "Extracting 3/7 (43%)" → "Converting 3/7 (43%)"
  - Phase transitions without breaking existing progress tracking

- [x] T060 [US3] Implement post-conversion validation in `src/slice_oas/validator.py` ✅
  - Add `validate_converted_document(doc, target_version)` function
  - Use `openapi-spec-validator` to validate against target OAS schema (3.0 or 3.1)
  - Return detailed error messages for validation failures
  - Fail conversion if validation fails (don't produce output)

- [x] T061 [US3] Add dry-run support for conversions in `src/slice_oas/cli.py` ✅
  - Extend `--dry-run` flag to work with `--convert-version`
  - Preview mode: show endpoints to be converted, target version, without writing files
  - Output: "DRY RUN: Would convert 5 endpoints from 3.0 to 3.1"

- [x] T062 [US3] Create conversion error reporting in `src/slice_oas/cli.py` ✅
  - Implement `format_conversion_error_summary(failed_conversions)` with plain-language messages
  - Implement `print_conversion_summary(result)` with converted count, warnings, elapsed time
  - Example: "3 endpoints failed conversion (nullable structures not supported in strict mode)"

- [x] T063 [US3] Set up integration test framework for version conversion in `tests/integration/test_version_conversion.py` ✅
  - Create test fixtures for 3.0 and 3.1 OAS documents
  - Implement test fixtures: `oas_30_simple` (3.0 format), `oas_31_simple` (3.1 format), `oas_31_with_webhooks` (3.1 with webhooks)
  - Implement helper functions: `convert_and_validate(doc, source_version, target_version, strict_mode)`, `extract_conversion_result(result)`
  - Configure pytest to discover and run conversion tests

### Testing (T064-T073): Integration Tests ✅ 23 Tests Passing

- [x] T064 [US3] Write integration test: Convert 3.0→3.1 simple endpoint in `tests/integration/test_version_conversion.py` ✅
  - Scenario: GET /users/{id} with nullable user_profile property in 3.0 → converted to 3.1 type array
  - Assertions: success==True, version==3.1.0, nullable→type arrays, all schemas resolved

- [x] T065 [US3] Write integration test: Convert 3.1→3.0 simple endpoint in `tests/integration/test_version_conversion.py` ✅
  - Scenario: GET /orders/{orderId} with type array in 3.1 → converted to 3.0 nullable
  - Assertions: success==True, type arrays→nullable, version==3.0.0, webhooks warning if present

- [x] T066 [US3] Write integration test: Handle nullable transformations in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Schema with multiple nullable properties (User with nullable email, phone, profile)
  - Assertions: All properties correctly converted, round-trip (3.0→3.1→3.0) produces identical original

- [x] T067 [US3] Write integration test: Batch conversion with filtering in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Convert multiple endpoints (/users/*, /api/v1/*) from 3.0→3.1 with glob filter
  - Assertions: Only 3 /users/* endpoints converted, all successful, CSV index generated

- [x] T068 [US3] Write integration test: Error handling for unconvertible constructs in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Try to convert 3.1 doc with webhooks to 3.0 (unsupported)
  - Assertions (Permissive): succeeds, warnings contain "Webhooks removed", no webhooks in output
  - Assertions (Strict): fails, errors contain "Webhooks not supported"

- [x] T069 [US3] Write integration test: Determinism (repeated conversions produce identical output) in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Convert same document 3 times; verify identical output each time (hash verification)
  - Assertions: hash(run_1) == hash(run_2) == hash(run_3), rule ordering deterministic

- [x] T070 [US3] Write integration test: Performance benchmark (<3min for 100 endpoints) in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Create synthetic OAS with 100 endpoints; measure conversion time
  - Assertions: Completes in <180 seconds, per-endpoint average <1.8s, parallel faster than sequential

- [x] T071 [US3] Write integration test: Acceptance (converted endpoints usable) in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Convert endpoint, extract it again (Phase 4), verify extraction works
  - Assertions: No validation errors, can be re-extracted (round-trip works)

- [x] T072 [US3] Write integration test: Edge case - Complex schemas in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Schema with oneOf, anyOf, allOf composition
  - Assertions: Schema composition preserved, nested references resolved consistently, no data loss

- [x] T073 [US3] Write integration test: Edge case - Discriminator and security in `tests/integration/test_version_conversion.py` ✅
  - Scenario: Schema with discriminator (polymorphic types) and security schemes
  - Assertions: discriminator.propertyName→mapping in 3.1, security schemes preserved, round-trip maintains mapping

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

## Phase Completion Status

| Phase | User Story | Description | Tasks | Status |
|-------|-----------|-------------|-------|--------|
| Phase 1 | Setup | Project initialization | T001-T007 | ✅ COMPLETE |
| Phase 2 | Foundation | Core infrastructure | T008-T016 | ✅ COMPLETE |
| Phase 3 | US1 (P1) | Single endpoint extraction | T017-T034 | ✅ COMPLETE (55/55 tests) |
| Phase 4 | US2 (P2) | Batch processing & filtering | T035-T053 | ✅ COMPLETE (79/79 tests) |
| Phase 5 | US3 (P3) | Version conversion (3.0↔3.1) | T054-T073 | ⏳ PENDING (20 tasks) |
| Phase 6 | US4 (P4) | CSV governance | T074-T088 | ⏳ PENDING |
| Phase 7 | US5 (P1) | Black Box UX | T089-T101 | ⏳ PENDING |
| Phase 8 | Integration | Cross-cutting & optimization | T102-T115 | ⏳ PENDING |

---

## Dependencies & Parallel Execution

### Execution Order

1. **Phase 1** (Setup): ✅ COMPLETE
2. **Phase 2** (Foundation): ✅ COMPLETE - gates all user stories
3. **Phase 3** (US1 - P1): ✅ COMPLETE - blocks US2, US3
4. **Phase 4** (US2 - P2): ✅ COMPLETE - blocks US4
5. **Phase 5** (US3 - P3): ⏳ **NEXT** - can run in parallel with US5 (T054-T073)
6. **Phase 6** (US4 - P4): ⏳ Blocked by Phase 4
7. **Phase 7** (US5 - P1): ⏳ Can run in parallel with Phase 5
8. **Phase 8** (Integration): ⏳ After all user stories complete

### Next Execution Plan

**Immediate (Phase 5 - T054-T073)**:
```
T054: Transformation rules (3.0↔3.1 rule library)      ↓
T055-T056: Data models + Converter implementation       ↓
T057-T062: CLI + batch integration + validation         ↓
T063: Test framework setup                              ↓
T064-T073: Integration tests (10 test scenarios)        ↓
[Parallel with US5 UX refinements - T089-T101]
```

**Parallel Opportunities**:
- T054 + T055 (rules + models) → independent, can run together ✅ **[P]**
- T057 + T059 (CLI + progress) → independent ✅ **[P]**
- T064-T073 (all tests) → can run in parallel ✅ **[P]**
- Phase 5 (US3) + Phase 7 (US5 UX) → independent after Phase 4 ✅ **[P]**

### Critical Path (Current)

**Completed Path**: T001-T007 (Setup) → T008-T016 (Foundation) → T025-T034 (US1) → T035-T053 (US2) → ✅ **COMPLETE** (79/79 tests passing)

**Current Path**: **T054-T073 (Phase 5 US3 Version Conversion)** → T074-T088 (Phase 6 US4 CSV Governance) → T102-T115 (Phase 8 Integration)

**Estimated Phase 5 Effort**: 20 tasks × 30-45 min/task = ~2-3 days with parallel execution

### MVP+ Scope Achieved

**MVP** (Phases 1-3, US1 only):
- ✅ Single endpoint extraction with reference resolution
- ✅ Complete 7-phase validation
- ✅ 55 comprehensive tests

**MVP+** (Phases 1-4, US1+US2):
- ✅ Batch extraction with filtering (glob + regex)
- ✅ Real-time progress reporting
- ✅ CSV index generation
- ✅ Parallel processing (4x faster)
- ✅ 79 comprehensive tests

**Next Increment**: Phase 5 (US3 - Version Conversion)
- ⏳ Bidirectional OAS 3.0↔3.1 conversion
- ⏳ Deterministic transformation rules
- ⏳ 10 integration tests for conversion scenarios

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
