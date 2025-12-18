# Feature Specification: Complete Reference Resolution Fix

**Feature Branch**: `002-slice-completeness-fix`
**Created**: 2025-12-18
**Status**: Draft
**Input**: User description: "Fix critical gaps in slice-oas-by-resource: incomplete component resolution (only schemas handled, missing headers/parameters/responses/etc.), unimplemented payload equivalence validation, and missing CSV generation for single extractions. Ensure all OpenAPI component types are resolved and validated per constitution requirements."

## Clarifications

### Session 2025-12-18

- Q: Should this fix feature include Docker containerization? → A: No Docker - keep existing native CLI execution model.
- Q: How should we verify that TDD is actually followed? → A: Commit-based - require separate commits: tests first (failing), then implementation.
- Q: What CLI automation capabilities should be added? → A: No additional CLI - existing CLI and pytest sufficient.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Header Resolution (Priority: P1)

An API architect extracts an endpoint that uses response headers defined in `components/headers` via `$ref`. The extracted file must include all referenced header definitions so the output is a valid, self-contained OpenAPI specification.

**Why this priority**: This is the most commonly reported defect. Header references are frequently used in production APIs for rate limiting, pagination cursors, and cache control. Missing headers make the output invalid and unusable.

**Independent Test**: Extract an endpoint with `$ref: "#/components/headers/X-Rate-Limit"` in its response headers. Verify the output file contains the header definition in `components/headers` and passes OpenAPI validation.

**Acceptance Scenarios**:

1. **Given** an OAS file with `responses.200.headers.X-Rate-Limit.$ref: "#/components/headers/X-Rate-Limit"`, **When** the user extracts that endpoint, **Then** the output file includes `components.headers.X-Rate-Limit` with the complete header definition.

2. **Given** an OAS file with multiple header references across different response codes, **When** the user extracts that endpoint, **Then** all referenced headers are included in the output.

3. **Given** a header definition that itself references a schema (e.g., `schema.$ref`), **When** the user extracts the endpoint, **Then** both the header and its transitive schema dependencies are included.

---

### User Story 2 - Complete Parameter Resolution (Priority: P1)

A developer extracts an endpoint that uses shared parameter definitions from `components/parameters`. The extracted file must include all parameter definitions to be usable by code generators and documentation tools.

**Why this priority**: Shared parameters (pagination, filtering, common path params) are an OpenAPI best practice. Failing to resolve them breaks downstream tooling.

**Independent Test**: Extract an endpoint with `parameters: [{$ref: "#/components/parameters/PaginationOffset"}]`. Verify the output includes the parameter definition.

**Acceptance Scenarios**:

1. **Given** an endpoint with `$ref: "#/components/parameters/userId"` in its parameters array, **When** the user extracts that endpoint, **Then** the output file includes `components.parameters.userId`.

2. **Given** a path-level parameter reference (not operation-level), **When** the user extracts any method from that path, **Then** the path-level parameter reference is resolved.

3. **Given** a parameter that references a schema, **When** extracted, **Then** both parameter and schema are included.

---

### User Story 3 - Complete Response Resolution (Priority: P1)

A technical writer extracts an endpoint that uses shared response definitions for common error responses (404, 500, etc.). The extracted file must include all response definitions.

**Why this priority**: Shared responses for error handling are extremely common in well-designed APIs. Missing response definitions create invalid output.

**Independent Test**: Extract an endpoint with `responses.404.$ref: "#/components/responses/NotFound"`. Verify the output includes the response definition.

**Acceptance Scenarios**:

1. **Given** an endpoint with `responses.404.$ref: "#/components/responses/NotFound"`, **When** extracted, **Then** `components.responses.NotFound` is included in output.

2. **Given** a shared response that includes headers and content schemas, **When** extracted, **Then** all transitive dependencies (response → headers → schemas) are resolved.

---

### User Story 4 - Complete RequestBody Resolution (Priority: P2)

A developer extracts a POST/PUT endpoint that uses shared request body definitions. The extracted file must include the request body definition.

**Why this priority**: Request body sharing is common but less frequent than parameters and responses. Still critical for valid output.

**Independent Test**: Extract an endpoint with `requestBody.$ref: "#/components/requestBodies/UserInput"`. Verify the output includes the request body definition.

**Acceptance Scenarios**:

1. **Given** an endpoint with `requestBody.$ref: "#/components/requestBodies/CreateUser"`, **When** extracted, **Then** `components.requestBodies.CreateUser` is included.

2. **Given** a request body with multiple content types each referencing different schemas, **When** extracted, **Then** all schemas are included.

---

### User Story 5 - Complete SecurityScheme Resolution (Priority: P2)

A security engineer extracts an endpoint with security requirements. The extracted file must include all referenced security scheme definitions.

**Why this priority**: Security schemes are essential for tools that generate authentication code or documentation. Missing schemes create incomplete specifications.

**Independent Test**: Extract an endpoint with `security: [{api_key: []}]`. Verify `components.securitySchemes.api_key` is included.

**Acceptance Scenarios**:

1. **Given** an endpoint with operation-level security referencing `api_key`, **When** extracted, **Then** `components.securitySchemes.api_key` is included.

2. **Given** global security defined at the spec root, **When** any endpoint is extracted, **Then** the global security schemes are included.

3. **Given** an endpoint with multiple security requirements (e.g., OAuth2 + API key), **When** extracted, **Then** all referenced security schemes are included.

---

### User Story 6 - Payload Equivalence Validation (Priority: P1)

A quality engineer runs the tool and expects validation to detect when the extracted endpoint is missing components that exist in the parent specification. The validation should fail if any referenced component is not included.

**Why this priority**: Without this validation, broken extractions are silently accepted. This is a fundamental quality gate.

**Independent Test**: Create an extraction scenario where a component is intentionally not copied. Verify validation Phase 6 fails with a clear error message.

**Acceptance Scenarios**:

1. **Given** a parent OAS file and an extracted endpoint, **When** validation runs, **Then** Phase 6 compares all `$ref` in the extracted file against the parent to verify completeness.

2. **Given** an extraction missing a required header definition, **When** validation runs, **Then** it fails with message indicating the missing component.

3. **Given** a complete extraction, **When** validation runs, **Then** Phase 6 passes confirming payload equivalence.

---

### User Story 7 - CSV Index for Single Extractions (Priority: P3)

A governance team member extracts a single endpoint and expects to find it in the CSV index for tracking and auditing purposes.

**Why this priority**: While batch operations create CSV, single extractions should also maintain the audit trail for consistency. Lower priority as it doesn't affect output validity.

**Independent Test**: Run single endpoint extraction. Verify CSV index is created/updated at `{output_dir}/sliced-resources-index.csv`.

**Acceptance Scenarios**:

1. **Given** a single endpoint extraction (not batch), **When** extraction completes, **Then** a CSV index entry is created.

2. **Given** an existing CSV index, **When** extracting another single endpoint, **Then** the new entry is appended without duplicates.

---

### Edge Cases

- What happens when a `$ref` points to a component type not yet supported (e.g., `#/components/examples/Sample`)?
- How does the system handle `$ref` to `#/components/links/*` and `#/components/callbacks/*`?
- What happens when a security scheme references an external OAuth2 authorization URL?
- How does the system handle vendor extensions (`x-*`) in components?
- What happens when the same component is referenced multiple times through different paths?
- How does the system handle `$ref` chains (component A → component B → schema C)?

## Requirements *(mandatory)*

### Functional Requirements

#### Reference Resolution

- **FR-001**: System MUST resolve `$ref` entries pointing to `#/components/headers/*` and include them in output `components.headers`
- **FR-002**: System MUST resolve `$ref` entries pointing to `#/components/parameters/*` and include them in output `components.parameters`
- **FR-003**: System MUST resolve `$ref` entries pointing to `#/components/responses/*` and include them in output `components.responses`
- **FR-004**: System MUST resolve `$ref` entries pointing to `#/components/requestBodies/*` and include them in output `components.requestBodies`
- **FR-005**: System MUST resolve `$ref` entries pointing to `#/components/securitySchemes/*` and include them in output `components.securitySchemes`
- **FR-006**: System MUST resolve `$ref` entries pointing to `#/components/links/*` and include them in output `components.links`
- **FR-007**: System MUST resolve `$ref` entries pointing to `#/components/callbacks/*` and include them in output `components.callbacks`
- **FR-008**: System MUST recursively resolve transitive dependencies across all component types (e.g., response → header → schema)
- **FR-009**: System MUST handle circular references across component types without infinite loops

#### Validation

- **FR-010**: Validation Phase 4 MUST check ALL `$ref` types (not just schemas) for resolution within the output file
- **FR-011**: Validation Phase 6 MUST compare extracted endpoint against parent to verify all required components are included
- **FR-012**: Validation Phase 6 MUST fail with specific error message when a component is missing
- **FR-013**: System MUST validate that security scheme references resolve to existing definitions

#### CSV Index

- **FR-014**: Single endpoint extraction MUST create/update the CSV index at `{output_dir}/sliced-resources-index.csv`
- **FR-015**: CSV index MUST maintain duplicate detection for single extractions

#### Testing Requirements

- **FR-016**: Test suite MUST include tests for each component type (`headers`, `parameters`, `responses`, `requestBodies`, `securitySchemes`, `links`, `callbacks`)
- **FR-017**: Tests MUST be written BEFORE implementation changes (true TDD)
- **FR-018**: Tests MUST fail initially, then pass after implementation
- **FR-019**: TDD verification via commit sequence: test commits (showing failures) MUST precede implementation commits
- **FR-020**: Each component type MUST have a dedicated "red" commit (failing tests) followed by "green" commit (implementation)

### Key Entities

- **Component Reference**: A `$ref` pointer to any OpenAPI component type. Attributes: reference path, component type (schema, header, parameter, etc.), resolved status.

- **Component Types**: The 8 component categories defined by OpenAPI 3.x:
  - `schemas` - Data structure definitions
  - `headers` - Header definitions for responses
  - `parameters` - Reusable parameter definitions
  - `responses` - Reusable response definitions
  - `requestBodies` - Reusable request body definitions
  - `securitySchemes` - Authentication/authorization definitions
  - `links` - Links to related operations
  - `callbacks` - Callback definitions for webhooks

- **Resolution Result**: The outcome of resolving all references for an endpoint. Attributes: resolved components by type, unresolved references, circular references detected.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of `$ref` entries in extracted files resolve successfully within the file (all 8 component types)
- **SC-002**: Validation Phase 6 catches 100% of missing component scenarios (verified by intentional omission tests)
- **SC-003**: All extracted files pass external OpenAPI validator (openapi-spec-validator) without errors
- **SC-004**: Test suite includes at least 2 test cases per component type (16+ new tests minimum)
- **SC-005**: Single extractions produce CSV index entries in 100% of successful cases
- **SC-006**: Zero regressions in existing test suite (195 tests continue to pass)
- **SC-007**: Extraction of endpoints with mixed component references completes in under 5 seconds

## Assumptions

1. **Component Location**: All `$ref` entries point to components within the same file (external `$ref` to URLs or other files remains out of scope per original feature).

2. **OpenAPI 3.x Only**: The fix applies to OpenAPI 3.0.x and 3.1.x. Swagger 2.0 is out of scope.

3. **Backward Compatibility**: Existing functionality for schema resolution remains unchanged; new component resolution extends the existing capability.

4. **Performance**: Adding resolution for 7 additional component types should not significantly impact performance (target: <10% increase in extraction time).

5. **CSV Format**: CSV format remains unchanged per Constitution Principle V; only the trigger point changes to include single extractions.

## Dependencies

1. **Existing Resolver**: Changes build on the existing `ReferenceResolver` class in `resolver.py`.

2. **Existing Validator**: Changes extend the existing `EndpointValidator` class in `validator.py`.

3. **Existing Slicer**: Changes extend the existing `EndpointSlicer` class in `slicer.py`.

4. **Constitution Compliance**: All changes must comply with Constitution Principles I-V, particularly Principle III (Complete Reference Resolution).

## Out of Scope

1. **External References**: Resolution of `$ref` pointing to external URLs or other files
2. **New Component Types**: Any component types not defined in OpenAPI 3.x specification
3. **Performance Optimization**: Parallel resolution of different component types (sequential is acceptable)
4. **UI Changes**: No changes to CLI prompts or user-facing messages (unless required for new error scenarios)
5. **Docker/Containerization**: No Docker packaging or containerization; tool remains native CLI
