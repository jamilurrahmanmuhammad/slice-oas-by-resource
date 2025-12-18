<!--
SYNC IMPACT REPORT
Version: 1.0.0 → 1.1.0 (MINOR: Added OAS version awareness + multi-version output)
Modified Principles: I (clarified UX), III (expanded with version details), IV (version validation added)
Added Sections: OAS Version Strategy (1), OAS Family Differences (1)
Removed Sections: None
Templates Updated: ⚠ Pending - spec/plan/tasks need version selection guidance
Follow-up TODOs: Add version selection to spec template; document version-specific validation rules in plan template
-->

# Slice OpenAPI Specification by Resource Constitution

## Core Principles

### I. Black Box Abstraction (User Experience FIRST)
Non-programmer users MUST never see code, algorithms, pseudocode, or technical implementation details. The skill operates as a complete black box: user provides input → skill executes silently → user receives results. Only business-relevant information is exposed (files created, location, size, format, version).

**Non-Negotiable Rules:**
- Zero code or technical explanations shown to non-programmer users
- No intermediate steps, validation procedures, or processing pipelines visible
- No implementation details, dependencies, or tool mentions
- Results reported in simple, everyday language only
- Version information communicated as "compatibility format" not technical detail

**Rationale:** Users care about what was created, not how it was created. Technical exposure adds no value and reduces accessibility for non-technical teams.

### II. Explicit Path Input (No Auto-Discovery)
This skill NEVER searches for files, explores directories, or uses glob/find/ls commands. Users MUST provide complete, explicit file paths. If paths are invalid, the skill reports the error and requests correction—never attempts automatic path recovery or discovery.

**Non-Negotiable Rules:**
- Always request input file path explicitly from user
- Always request output folder path explicitly from user
- Always request output version (OAS 3.0.x or 3.1.x) explicitly from user
- Validate paths silently (no directory exploration)
- Report exact error for invalid paths; ask user for correction
- Never use find, glob, or directory listing to locate files
- Never attempt to guess alternative file locations
- Never browse filesystem without explicit user request

**Rationale:** Explicit paths and version selection eliminate ambiguity and ensure users control exactly where files come from, go to, and what format they take.

### III. Complete Reference Resolution with Version Fidelity
Every sliced OpenAPI file MUST include all transitively referenced components while preserving the semantics of the requested OAS version. Response headers, schemas, parameters, security schemes, and all nested references must be recursively resolved. Circular references are detected and handled without infinite loops. Version-specific transformations (3.0↔3.1) MUST be correct and explicit.

**Non-Negotiable Rules:**
- MUST scan and include all response header references (common defect)
- MUST recursively resolve schema references (transitive closure)
- MUST include all security schemes referenced by operation
- MUST handle circular references using visited set (prevent loops)
- MUST validate all references resolve within sliced file
- MUST fail validation if ANY $ref remains unresolved
- MUST preserve OAS version of input file OR apply correct version transformation if output version differs
- MUST understand version-specific syntax and convert correctly (see OAS Family Differences section)

**Critical Implementation Detail:** Response headers in responses[*].headers[*].$ref are frequently missed. These MUST be explicitly scanned and included in components.headers or the sliced file will have unresolved references.

**Version-Specific Rules:**
- When slicing from OAS 3.0.x: preserve `nullable` keyword, omit `webhooks` and `pathItems`, omit `mutualTLS` scheme
- When slicing from OAS 3.1.x: use JSON Schema 2020-12 features, include `webhooks`, may include `pathItems`, support `mutualTLS`
- When converting 3.0→3.1: replace `nullable: true` with `type: [originalType, "null"]`, add `webhooks` if empty object
- When converting 3.1→3.0: convert array types to `nullable`, remove `webhooks` section, remove `pathItems` from components, remove `mutualTLS` schemes

**Rationale:** Incomplete reference resolution produces invalid, unusable OpenAPI files. Users need standalone, self-contained specifications that can be used immediately without external resolution. Multi-version support requires understanding the subtle differences between OAS families.

### IV. Deterministic Validation (Strict Output Quality Assurance)
Every sliced file MUST pass a six-phase validation checkpoint plus version-specific validation before being reported as successfully created. No exceptions. If validation fails, processing stops and user receives diagnostic error information.

**Non-Negotiable Rules:**
- Phase 1: File structure (valid JSON/YAML, root keys present)
- Phase 2: Operation integrity (single path, single method, correct definition)
- Phase 3: Response integrity (codes match, headers resolve, schemas present)
- Phase 4: Reference resolution (ALL $ref entries resolve to existing components)
- Phase 5: Component completeness (no orphaned refs, required components non-empty)
- Phase 6: Payload equivalence (operation matches parent spec exactly)
- Phase 7 (NEW): Version validation (OAS version matches requested output version, schema syntax correct for version)
- Validation MUST be deterministic and reproducible
- Every checkpoint MUST be passed; failing at any checkpoint rejects the entire file

**Version-Specific Validation:**
- Detect input OAS version from `openapi` field (3.0.x or 3.1.x)
- If version conversion requested, validate all conversions applied correctly
- For OAS 3.0.x output: no `type: [...]` arrays in schemas (must use `nullable`)
- For OAS 3.1.x output: all schema constructs comply with JSON Schema 2020-12
- Validate security schemes: mutualTLS only in 3.1.x
- Validate info section: license with `identifier` only in 3.1.x

**Rationale:** Validation gates prevent release of broken OpenAPI specifications. Version validation ensures output matches the requested format and is usable by downstream tools.

### V. CSV Indexing (Real-Time Resource Tracking)
A CSV index file MUST be maintained at `{output_directory}/sliced-resources-index.csv`. One row per successfully sliced resource with: path, method, summary, operationId, tags, filename, size, schema count, parameter count, response codes, security requirement, deprecation status, and timestamp.

**Non-Negotiable Rules:**
- CSV created on first resource sliced
- Updated in real-time after each successful slice (not batched)
- Append mode (preserve previous rows when re-running)
- No duplicates (check for existing path+method combinations)
- Failed resources NOT added to CSV
- CSV remains readable and updateable during processing
- Exact column order: path | method | summary | description | operationId | tags | filename | file_size_kb | schema_count | parameter_count | response_codes | security_required | deprecated | created_at | output_oas_version
- CSV MUST include output_oas_version column to track which version each sliced file targets

**Rationale:** CSV provides searchable, machine-readable tracking of all sliced resources. Users can build catalogs, measure coverage, or validate completeness without parsing individual OpenAPI files.

## OAS Version Strategy

### Version Support

This skill supports slicing and version conversion for:
- **OAS 3.0.x family**: 3.0.0, 3.0.1, 3.0.2, 3.0.3, 3.0.4
- **OAS 3.1.x family**: 3.1.0, 3.1.1, and future 3.1.x patch versions
- **Version Detection**: Automatically detected from input `openapi` field (semantic versioning format)
- **Version Conversion**: Supports conversion between families (3.0.x ↔ 3.1.x) with explicit transformation rules

**Generalization Strategy:** Treat as family versions (3.0.x vs 3.1.x) because:
- Patch versions (e.g., 3.0.3 vs 3.0.4) represent clarifications, not feature changes
- Tooling compatible with 3.0.0 is compatible with 3.0.4
- Tooling compatible with 3.1.0 is compatible with 3.1.1
- Family-level strategy reduces complexity while maintaining correctness

### Version Selection Workflow

User must explicitly choose output version:
1. Input file version is detected automatically
2. User prompted: "Use input version [detected] or convert to different version? (3.0.x / 3.1.x)"
3. If conversion selected, user confirms transformation rules will be applied
4. Processing continues with chosen output version
5. Result files are in requested version format; CSV tracks version for each resource

## OAS Family Differences

### Key 3.0.x Characteristics (Design-Critical)

- **Schema Model**: Constrained JSON Schema (not full JSON Schema)
- **Nullable Handling**: `nullable: true` boolean flag for optional nulls
- **Composition**: `allOf`, `oneOf`, `anyOf`, `not` supported but no JSON Schema conditionals
- **Root Structure**: No `webhooks` section, no `pathItems` in components
- **Security Schemes**: apiKey, http, oauth2, openIdConnect (no mutualTLS)
- **License**: Only `url` field (no `identifier`)
- **Arrays in Schema**: Must use explicit `type: array` with `items`; no type unions like `type: ["string", "null"]`

### Key 3.1.x Differences (Design-Critical)

- **Schema Model**: Full JSON Schema 2020-12 compliance
- **Nullable Handling**: Use `type: ["originalType", "null"]` array (no `nullable` keyword)
- **Composition**: All JSON Schema features including `if/then/else` conditionals
- **Root Structure**: Adds `webhooks` section, adds `pathItems` in components
- **Security Schemes**: Adds `mutualTLS` scheme type (new)
- **License**: Both `url` and `identifier` supported (mutually exclusive per spec)
- **Arrays in Schema**: Can use `type: ["string", "integer", null]` syntax for union types
- **Examples**: `examples` array introduced for richer example support

### Transformation Rules for 3.0 → 3.1 Conversion

When converting 3.0.x input to 3.1.x output:

1. **Remove all `nullable` keywords**: Replace `nullable: true` with `type: [originalType, "null"]`
   - Example: `type: string, nullable: true` → `type: ["string", "null"]`
   - Example: `type: integer, nullable: true` → `type: ["integer", "null"]`
   - Keep schemas with `nullable: false` as-is (remove the keyword)

2. **Add empty `webhooks` section** if not present

3. **Keep existing components as-is**: 3.1 is a superset and supports all 3.0 structures

4. **Convert security schemes**: No changes needed (all 3.0 schemes valid in 3.1)

5. **Convert license section**: If only `url` present, keep as-is (both formats valid in 3.1)

6. **Preserve all other structures**: All 3.0 constructs are valid in 3.1 without modification

### Transformation Rules for 3.1 → 3.0 Conversion

When converting 3.1.x input to 3.0.x output:

1. **Convert all type unions to `nullable`**: Replace `type: [originalType, "null"]` with separate fields
   - Example: `type: ["string", "null"]` → `type: string, nullable: true`
   - Example: `type: ["integer", "null"]` → `type: integer, nullable: true`
   - If union has multiple non-null types (e.g., `["string", "integer"]`) → **FAIL** (not convertible)

2. **Remove `webhooks` section**: Omit entirely from 3.0 output

3. **Remove `pathItems` from components**: Delete if present

4. **Remove `mutualTLS` security schemes**: Delete and warn user

5. **Keep `examples` as-is**: OAS 3.0 doesn't have examples array but individual examples are compatible; if needed, convert array to single example or omit

6. **Convert license**: If `identifier` present without `url`, **FAIL** (not convertible); if both present, use `url` only

7. **Flatten JSON Schema conditionals**: If `if/then/else` present, **FAIL** with user message: "This OAS 3.1 spec uses JSON Schema conditionals which cannot be automatically converted to 3.0"

### Validation Rules for Each Version

**For OAS 3.0.x output:**
- ✓ No `type: [array]` syntax (must use `type` + `items`)
- ✓ `nullable` field may be present
- ✓ No `webhooks` root field
- ✓ No `pathItems` in components
- ✓ No `mutualTLS` in securitySchemes
- ✓ No `if/then/else` in schemas
- ✓ License has only `url` (no `identifier`)

**For OAS 3.1.x output:**
- ✓ May use `type: [type1, type2, ...]` syntax
- ✓ No `nullable` field (use type arrays instead)
- ✓ May have `webhooks` section
- ✓ May have `pathItems` in components
- ✓ May include `mutualTLS` security scheme
- ✓ May include `if/then/else` conditionals
- ✓ License may use `identifier` field (mutually exclusive with `url`)

## Quality Assurance

### Output Validation Requirements

**Mandatory Checks (Non-Negotiable):**
- ✓ All sliced files MUST be valid OpenAPI specifications for the requested version
- ✓ All $ref entries MUST resolve to existing components within the sliced file
- ✓ Response headers with $ref MUST have corresponding entries in components.headers
- ✓ All transitive schema dependencies MUST be included (recursive closure)
- ✓ File naming MUST follow pattern: `{path-sanitized}-{method}.{format}`
- ✓ Operations MUST match parent specification exactly (bit-for-bit for resolveability)
- ✓ No unresolved external references (all refs must be resolvable within sliced file)
- ✓ OAS version in output MUST match requested output version
- ✓ All version-specific schema syntax MUST be correct for requested version

**Failure Criteria:**
- Any validation checkpoint fails → file is rejected
- Any unresolved $ref → validation fails
- Any missing component → validation fails
- Any format error → validation fails
- Version mismatch between declared and actual syntax → validation fails
- Version conversion error (unconvertible structures) → user notified, file rejected

## Governance

**Amendment Procedure:**
Constitution supersedes all other guidance. Amendments require (1) documented rationale addressing current constraint, (2) impact analysis on dependent templates and tasks, and (3) version bump with semantic versioning (MAJOR for backward-incompatible changes, MINOR for new principles or version support, PATCH for clarifications).

**Compliance Review:**
All pull requests affecting skill behavior MUST verify compliance with principles I-V. Code reviews MUST confirm validation checkpoints are executed; CSV index is maintained; black box abstraction preserved; no auto-discovery code exists; and version transformations are correct.

**Versioning Policy:**
- MAJOR: Principle removal/redefinition, validation bypass, or black box violation
- MINOR: New principle, new OAS version support, CSV column addition, or validation checkpoint addition
- PATCH: Wording, clarification, non-semantic refinement

**Version**: 1.1.0 | **Ratified**: 2025-12-17 | **Last Amended**: 2025-12-17
