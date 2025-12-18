# Feature Specification: Slice OAS by Resource

**Feature Branch**: `001-slice-oas-by-resource`
**Created**: 2025-12-17
**Status**: Draft
**Input**: User description: "The slice-oas-by-resource skill is an interactive tool that decomposes large OpenAPI specifications into individual, self-contained OAS files—one for each path and HTTP method combination. The skill enables API teams and technical writers to manage, export, and document individual API endpoints as standalone specifications while maintaining complete fidelity with the parent specification."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single Endpoint Extraction for Documentation (Priority: P1)

An API architect needs to extract a specific endpoint (e.g., GET /users/{id}) from a large OpenAPI specification file and generate a standalone OAS file that includes all necessary schemas, parameters, and security definitions. This extracted file will be shared with external partners without exposing the full API surface.

**Why this priority**: This is the core value proposition and most common use case. A user should be able to extract a single endpoint and get immediate value without any additional configuration or complex workflows.

**Independent Test**: Can be fully tested by providing a valid OAS file path and a single resource identifier (path + method), then verifying the output is a valid, standalone OAS file with all references resolved.

**Acceptance Scenarios**:

1. **Given** a valid OpenAPI 3.0.x specification file at a user-provided path, **When** the user specifies a single resource (path and HTTP method), **Then** the system produces a standalone OAS file containing only that endpoint with all referenced schemas, parameters, headers, and security schemes included.

2. **Given** the user selects JSON output format, **When** the extraction completes, **Then** the output file is valid JSON and passes OpenAPI validation.

3. **Given** the user selects YAML output format, **When** the extraction completes, **Then** the output file is valid YAML and passes OpenAPI validation.

4. **Given** an extracted endpoint file, **When** validated against OpenAPI specification standards, **Then** all $ref entries resolve successfully within the file.

5. **Given** the extraction process completes, **When** the user reviews the CSV index, **Then** the extracted resource is logged with accurate metadata (path, method, version, timestamp, output file location).

---

### User Story 2 - Batch Slicing for Microservices Deployment (Priority: P2)

A DevOps engineer needs to decompose a monolithic API specification containing 100+ endpoints into multiple service-specific OAS files. Each output file should contain only the endpoints relevant to a specific microservice, with complete schema resolution.

**Why this priority**: Batch operations unlock the tool's scalability and enable enterprise workflows. However, this depends on the single extraction working correctly first (P1).

**Independent Test**: Can be fully tested by providing an OAS file and a filter criteria (e.g., path prefix pattern), then verifying that all matching endpoints are extracted into separate files and all files pass validation.

**Acceptance Scenarios**:

1. **Given** a valid OpenAPI specification with 100+ endpoints, **When** the user selects "extract all resources", **Then** the system generates one standalone OAS file per path+method combination.

2. **Given** batch extraction is in progress, **When** processing 100 endpoints, **Then** all extractions complete within 3 minutes.

3. **Given** batch extraction completes, **When** the user reviews the CSV index, **Then** all extracted resources are logged with accurate metadata and real-time progress updates were provided during processing.

4. **Given** the user provides a filter pattern (e.g., "/users/*"), **When** batch extraction runs, **Then** only endpoints matching the pattern are extracted.

5. **Given** all batch-extracted files, **When** each file is validated, **Then** 100% pass OpenAPI validation with all references resolved.

---

### User Story 3 - Version Conversion for Legacy Migration (Priority: P3)

An integration team needs to extract endpoints from an OpenAPI 3.0.x specification and convert them to OpenAPI 3.1.x format for compatibility with newer toolchains. The conversion must maintain data integrity and correctly resolve all references.

**Why this priority**: Version conversion is a specialized use case that adds significant value but is not required for basic extraction workflows. It depends on P1 working correctly and adds transformation capabilities.

**Independent Test**: Can be fully tested by extracting an endpoint from a 3.0.x spec, requesting 3.1.x output, and verifying the output conforms to 3.1.x schema with all data preserved.

**Acceptance Scenarios**:

1. **Given** a valid OpenAPI 3.0.x specification, **When** the user requests extraction with OpenAPI 3.1.x output format, **Then** the system produces a valid 3.1.x file with all standard constructs correctly converted.

2. **Given** a valid OpenAPI 3.1.x specification, **When** the user requests extraction with OpenAPI 3.0.x output format, **Then** the system produces a valid 3.0.x file with all compatible constructs correctly converted.

3. **Given** version conversion is requested, **When** the conversion completes, **Then** the output is deterministic (repeated runs produce identical results) and all data integrity is maintained.

4. **Given** an OAS file with complex schema structures, **When** version conversion is performed, **Then** all schema references, oneOf/anyOf/allOf constructs, and security schemes are correctly transformed.

---

### User Story 4 - CSV Index Generation for API Governance (Priority: P4)

A technical writer or governance team needs to generate a CSV index of all API endpoints from multiple OAS files for tracking, documentation, and bulk operations across different API versions.

**Why this priority**: CSV indexing is a reporting/observability feature that enhances the core extraction capability but is not essential for the primary use cases.

**Independent Test**: Can be fully tested by running batch extraction and verifying the CSV file contains accurate entries for all processed endpoints with correct metadata fields.

**Acceptance Scenarios**:

1. **Given** a batch extraction operation, **When** processing completes, **Then** a CSV index file is generated with columns: path, method, OAS version, source file, output file, timestamp, validation status.

2. **Given** extraction is in progress, **When** each endpoint is processed, **Then** the CSV index is updated in real-time with the new entry.

3. **Given** a CSV index file, **When** opened in standard spreadsheet software, **Then** all data is properly formatted and readable.

4. **Given** multiple extraction sessions, **When** the user reviews historical CSV files, **Then** each session produces a unique timestamped CSV for traceability.

---

### User Story 5 - Black Box UX for Non-Programmers (Priority: P1)

A technical writer with no programming background needs to extract API endpoint documentation without seeing code, algorithms, or technical implementation details. The entire workflow should be conversational and guided.

**Why this priority**: This is a critical requirement that affects the entire user experience. If non-programmers cannot use the tool, it fails a core design goal. This is tied to P1 because the UX must be in place from the first use case.

**Independent Test**: Can be fully tested by having a non-technical user complete the entire extraction workflow using only natural language prompts, without being exposed to code or technical jargon.

**Acceptance Scenarios**:

1. **Given** a non-programmer user, **When** they initiate the skill, **Then** they are presented with clear, conversational prompts asking for input file path and desired endpoint.

2. **Given** the user provides input, **When** any validation errors occur, **Then** error messages are presented in plain language with actionable guidance (e.g., "The file path you provided doesn't exist. Please check the path and try again.").

3. **Given** the extraction process is running, **When** the user views progress updates, **Then** no code, JSON structures, or algorithm details are shown - only plain language status messages.

4. **Given** the process completes successfully, **When** the user reviews the results, **Then** they see a summary in plain language (e.g., "Successfully extracted GET /users/{id} to /output/users-get.yaml") without technical details.

5. **Given** the user needs to specify file paths, **When** prompted, **Then** the system validates the path and provides helpful feedback if the path is invalid or the file is not found.

---

### Edge Cases

- What happens when the input OAS file contains circular references in schemas (e.g., Schema A references Schema B, which references Schema A)?
- How does the system handle endpoints with no referenced schemas (e.g., a simple GET request with no parameters or response body)?
- What happens when the user specifies a path+method combination that doesn't exist in the source OAS file?
- How does the system handle OAS files with external $ref links pointing to remote URLs or other local files?
- What happens when the output file already exists at the target location? Should it overwrite, prompt, or create a versioned filename?
- How does the system handle malformed or invalid OAS input files?
- What happens when an endpoint references deprecated or vendor-specific extensions (e.g., x-amazon-apigateway-*)?
- How does the system handle very large OAS files (e.g., 10MB+ with thousands of endpoints)?
- What happens when schema names collide during extraction (e.g., two different schemas both named "User" in different contexts)?
- How does the system handle endpoints with complex security schemes (multiple requirements, OAuth scopes, API key + JWT combinations)?
- What happens when batch extraction runs out of disk space or encounters filesystem permission errors?
- How does the system validate that all 7 validation phases pass before accepting output?

## Requirements *(mandatory)*

### Functional Requirements

#### Core Slicing Capabilities

- **FR-001**: System MUST accept an explicit file path to an OpenAPI specification file (JSON or YAML format) as input
- **FR-002**: System MUST support OpenAPI versions 3.0.x and 3.1.x as input
- **FR-003**: System MUST allow users to specify a single resource by path and HTTP method (e.g., "/users/{id}", "GET")
- **FR-004**: System MUST generate a standalone, valid OpenAPI specification file containing only the specified endpoint
- **FR-005**: System MUST include all referenced schemas in the output file (all $ref entries must resolve within the output file)
- **FR-006**: System MUST include all referenced parameters (path, query, header, cookie) in the output file
- **FR-007**: System MUST include all referenced response schemas and headers in the output file
- **FR-008**: System MUST include all referenced security schemes in the output file
- **FR-009**: System MUST preserve the original OpenAPI version of the source file in the output file by default

#### Batch Processing

- **FR-010**: System MUST support batch extraction mode to slice all endpoints from a source OAS file
- **FR-011**: System MUST support filter patterns to extract multiple endpoints matching specific criteria (e.g., path prefix, tag, operation ID pattern)
- **FR-012**: System MUST process batch extraction of 100 endpoints within 3 minutes
- **FR-013**: System MUST provide real-time progress updates during batch processing (e.g., "Processing 45 of 100...")

#### Output Formats

- **FR-014**: System MUST support JSON output format
- **FR-015**: System MUST support YAML output format
- **FR-016**: System MUST allow users to specify the output format explicitly
- **FR-017**: System MUST generate output filenames following a consistent naming pattern (e.g., {path}-{method}.{format})

#### Version Conversion

- **FR-018**: System MUST support converting OpenAPI 3.0.x specifications to 3.1.x during extraction
- **FR-019**: System MUST support converting OpenAPI 3.1.x specifications to 3.0.x during extraction
- **FR-020**: System MUST ensure version conversion is deterministic (repeated conversions produce identical output)
- **FR-021**: System MUST correctly transform standard OpenAPI constructs during version conversion (schemas, security, examples, nullable vs type arrays, etc.)

#### CSV Index Generation

- **FR-022**: System MUST generate a CSV index file during batch extraction operations
- **FR-023**: CSV index MUST include columns: path, HTTP method, OpenAPI version, source file path, output file path, timestamp, validation status
- **FR-024**: System MUST update the CSV index in real-time as each endpoint is processed
- **FR-025**: CSV index MUST be compatible with standard spreadsheet software (proper escaping, RFC 4180 compliance)

#### Validation

- **FR-026**: System MUST validate the input OAS file before processing (7-phase validation)
- **FR-027**: System MUST validate each output file before accepting it as complete
- **FR-028**: System MUST ensure 100% of output files pass OpenAPI specification validation
- **FR-029**: System MUST verify that all $ref entries in output files resolve successfully (no broken references)
- **FR-030**: System MUST reject invalid or malformed input OAS files with clear error messages

#### User Experience (Black Box Requirement)

- **FR-031**: System MUST present a conversational interface using plain language prompts
- **FR-032**: System MUST NOT display code, JSON/YAML structures, or algorithm details to users during normal operation
- **FR-033**: System MUST provide error messages in plain language with actionable guidance
- **FR-034**: System MUST validate user-provided file paths and provide helpful feedback for invalid paths
- **FR-035**: System MUST display progress and completion messages in user-friendly language (no technical jargon)
- **FR-036**: System MUST require explicit file paths from users (no automatic directory discovery or searching)

#### Performance and Reliability

- **FR-037**: System MUST complete single endpoint extraction in under 5 seconds for typical OAS files (up to 1MB)
- **FR-038**: System MUST handle OAS files containing up to 1000 endpoints without failure
- **FR-039**: System MUST provide clear error messages and graceful degradation when encountering unsupported OAS features or extensions

### Key Entities *(include if feature involves data)*

- **OpenAPI Specification (OAS) File**: The source document containing API definitions, including paths, operations, schemas, parameters, responses, and security schemes. Attributes include: file path, OAS version (3.0.x or 3.1.x), format (JSON/YAML), size, number of paths.

- **Resource (Endpoint)**: A unique combination of HTTP path and method representing a single API operation. Attributes include: path template (e.g., "/users/{id}"), HTTP method (GET/POST/PUT/DELETE/PATCH/etc.), operation ID, tags, summary, description.

- **Schema**: A data structure definition referenced by endpoints for request bodies, response bodies, or parameters. Attributes include: schema name, type, properties, required fields, references to other schemas.

- **Parameter**: An input value for an API operation, defined at the path or operation level. Attributes include: parameter name, location (path/query/header/cookie), type, required/optional, schema reference.

- **Security Scheme**: An authentication or authorization mechanism required by an endpoint. Attributes include: scheme name, type (apiKey/http/oauth2/openIdConnect), location (header/query/cookie), flows (for OAuth2).

- **Output File**: A standalone OAS file generated by the slicing operation. Attributes include: file path, format (JSON/YAML), OAS version, source endpoint, timestamp, validation status.

- **CSV Index Entry**: A record in the CSV tracking file representing one sliced endpoint. Attributes include: source path, HTTP method, source file, output file, OAS version, timestamp, validation result.

- **Reference ($ref)**: A pointer to a schema, parameter, response, or other component defined elsewhere in the OAS file. The system must resolve all references and include the referenced objects in the output file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can extract a single endpoint from an OAS file and receive a valid output file in under 5 seconds
- **SC-002**: Batch extraction of 100 endpoints completes in under 3 minutes
- **SC-003**: 100% of generated output files pass OpenAPI specification validation
- **SC-004**: 100% of generated output files have all $ref entries resolved successfully (no broken references)
- **SC-005**: Non-programmer users can complete the entire extraction workflow without seeing code or technical implementation details
- **SC-006**: Version conversion (3.0.x ↔ 3.1.x) produces deterministic output (repeated conversions yield identical files)
- **SC-007**: The system supports OAS files containing up to 1000 endpoints without failure
- **SC-008**: CSV index accurately tracks all sliced resources with correct metadata in 100% of batch operations
- **SC-009**: Error messages are actionable and understandable to non-technical users in 95% of cases (based on user testing)
- **SC-010**: All sliced files are immediately usable by downstream OpenAPI tools (validators, code generators, documentation generators) without modification

## Assumptions

1. **Input File Accessibility**: The user has read access to the source OAS file and the file is stored on a local or network-accessible filesystem (not requiring authentication to cloud storage or APIs).

2. **Output File Location**: The user has write permissions to the output directory. If not specified, outputs are written to a default location (e.g., `./output/` in the current working directory).

3. **OAS Compliance**: The input OAS file generally conforms to OpenAPI 3.0.x or 3.1.x specifications. The system will validate and report errors, but it assumes the majority of input files are well-formed.

4. **External References**: OAS files with external $ref links (HTTP URLs or other local files) are out of scope for the initial version. All references must be internal to the source file.

5. **Standard OpenAPI Features**: The system supports standard OpenAPI constructs (paths, operations, schemas, parameters, responses, security schemes). Vendor-specific extensions (e.g., `x-amazon-*`, `x-google-*`) are preserved but not validated or transformed during version conversion.

6. **Single OAS File Per Extraction**: Each extraction operation works on one source OAS file at a time. Merging or combining multiple source files is out of scope.

7. **File System Storage**: All input and output files are stored on the file system. Integration with version control systems, cloud storage, or databases is out of scope for the initial version.

8. **English Language UX**: User prompts, error messages, and documentation are provided in English.

9. **7-Phase Validation**: The system implements a 7-phase validation checkpoint process to ensure output quality. The specific phases are: (1) input file syntax validation, (2) OAS schema compliance, (3) reference resolution check, (4) output file syntax validation, (5) output OAS schema compliance, (6) output reference resolution verification, (7) functional equivalence check (extracted endpoint matches source).

10. **Filename Collision Handling**: When an output file already exists, the system creates a versioned filename (e.g., `users-get-1.yaml`, `users-get-2.yaml`) rather than overwriting. Users are notified of the new filename.

11. **Disk Space**: Sufficient disk space is available for output files. Batch operations may generate hundreds of files; the system does not include disk space checking or cleanup features.

12. **Circular Reference Handling**: OAS files with circular schema references are supported. The system includes all schemas in the reference chain in the output file, preserving the circular structure.

## Dependencies

1. **OpenAPI Specification Standards**: The feature depends on the OpenAPI Specification versions 3.0.x and 3.1.x standards as defined by the OpenAPI Initiative.

2. **File System Access**: The system requires read access to input files and write access to output directories on the local or network file system.

3. **OpenAPI Validation Library**: An external or internal library/tool capable of validating OpenAPI 3.0.x and 3.1.x specifications is required for the 7-phase validation process.

## Out of Scope

1. **External Reference Resolution**: Resolving $ref links pointing to external HTTP URLs or other external files
2. **Multi-file Merging**: Combining multiple source OAS files into a single output
3. **API Runtime Testing**: Validating that extracted endpoints work against a live API server
4. **Code Generation**: Generating client or server code from extracted specifications
5. **Documentation Rendering**: Converting OAS files to HTML, PDF, or other documentation formats (this is a separate downstream process)
6. **Version Control Integration**: Automatic committing or tagging of extracted files in git or other VCS
7. **Cloud Storage Integration**: Direct upload/download from S3, Azure Blob, Google Cloud Storage, etc.
8. **Authentication for Remote Files**: Supporting authentication to access OAS files stored on remote servers or APIs
9. **Diff and Comparison**: Comparing extracted files across versions or highlighting changes
10. **Custom Validation Rules**: Beyond OpenAPI standard compliance, no custom business rule validation is included
11. **Swagger 2.0 Support**: Only OpenAPI 3.x versions are supported; Swagger 2.0 is out of scope
12. **GraphQL or Other API Specifications**: Only OpenAPI/REST specifications are supported
