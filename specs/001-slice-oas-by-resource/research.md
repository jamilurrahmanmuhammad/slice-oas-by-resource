# Research: slice-oas-by-resource

**Feature**: slice-oas-by-resource
**Phase**: Phase 0 (Research & Unknowns Resolution)
**Date**: 2025-12-17

---

## Research Task 1: OpenAPI Parsing Libraries for Python

### Question
Which Python library provides the most reliable parsing and validation for both OAS 3.0.x and 3.1.x with minimal dependencies?

### Options Evaluated

#### Option 1: openapi-spec-validator
- **Pros**:
  - Actively maintained (last update 2024)
  - Supports both OAS 3.0.x and 3.1.x
  - Built on jsonschema for strict validation
  - Minimal dependencies (jsonschema, PyYAML, jsonschema-path)
  - Provides detailed validation error messages
- **Cons**:
  - Does not handle $ref resolution automatically (we need custom resolver anyway)
  - Validation only, no parsing utilities
- **Version Support**: 3.0.0-3.0.4, 3.1.0-3.1.x
- **Assessment**: Strong candidate for validation; we'll need separate parsing logic

#### Option 2: prance
- **Pros**:
  - Full OAS parsing with automatic $ref resolution
  - Supports both 3.0.x and partial 3.1.x
  - Built-in URL resolution for external refs
- **Cons**:
  - 3.1.x support incomplete (missing some JSON Schema 2020-12 features)
  - Automatic $ref resolution conflicts with our need for explicit control
  - Heavy dependency tree
- **Version Support**: 3.0.x fully, 3.1.x partially
- **Assessment**: Not suitable - we need explicit control over reference resolution

#### Option 3: openapi-core
- **Pros**:
  - Request/response validation (useful for testing)
  - Supports OAS 3.0.x
- **Cons**:
  - Limited 3.1.x support
  - Designed for runtime validation, not specification manipulation
  - Heavy dependencies (Werkzeug, parse, more-itertools)
- **Version Support**: 3.0.x primarily
- **Assessment**: Wrong use case - designed for API validation, not spec slicing

#### Option 4: Custom Parser with PyYAML + jsonschema
- **Pros**:
  - Full control over parsing and validation
  - Minimal dependencies (PyYAML, jsonschema)
  - Can implement exact validation rules from constitution
  - No conflicts with reference resolution strategy
- **Cons**:
  - More initial implementation work
  - Need to maintain OAS schema definitions
- **Version Support**: We control the implementation
- **Assessment**: Gives us required control and flexibility

### Decision

**Selected: Custom Parser with PyYAML + jsonschema + openapi-spec-validator**

**Rationale**:
1. Use PyYAML for loading YAML/JSON files into Python dicts
2. Use custom parsing logic to extract paths, operations, components
3. Use openapi-spec-validator for final output validation (7-phase validation requirement)
4. Use jsonschema for schema validation where needed
5. Implement custom reference resolver (constitutional requirement for response header scanning)

**Dependencies**:
- PyYAML (5.4+): YAML/JSON parsing
- jsonschema (4.20+): Schema validation
- openapi-spec-validator (0.7+): Final OAS validation
- pydantic (2.5+): Data model validation and serialization

**Alternatives Rejected**:
- prance: Automatic $ref resolution conflicts with explicit control requirement
- openapi-core: Wrong domain (runtime API validation vs. spec manipulation)

---

## Research Task 2: Reference Resolution Algorithm

### Question
What is the optimal algorithm for transitive reference resolution that handles circular dependencies and avoids infinite loops?

### Patterns Evaluated

#### Pattern 1: Depth-First Search with Visited Set
```
Algorithm: DFS_Resolve(ref, visited)
  if ref in visited: return (already processed, skip)
  add ref to visited
  component = fetch_component(ref)
  for each nested_ref in component:
    DFS_Resolve(nested_ref, visited)
  return component with all dependencies
```
- **Pros**: Simple, handles circular refs naturally, guarantees complete traversal
- **Cons**: May process nodes multiple times if they're referenced from multiple paths
- **Complexity**: O(V + E) where V=components, E=references

#### Pattern 2: Breadth-First Search with Dependency Queue
```
Algorithm: BFS_Resolve(initial_refs)
  queue = initial_refs
  resolved = {}
  while queue not empty:
    ref = queue.pop()
    if ref in resolved: continue
    component = fetch_component(ref)
    resolved[ref] = component
    for nested_ref in component:
      queue.append(nested_ref)
  return resolved
```
- **Pros**: Level-by-level processing, easier to track depth, natural deduplication
- **Cons**: Slightly more memory overhead for queue
- **Complexity**: O(V + E)

#### Pattern 3: Topological Sort with Dependency Graph
```
Algorithm: Topo_Resolve(refs)
  graph = build_dependency_graph(refs)
  detect_cycles(graph)  # warn but continue
  sorted_nodes = topological_sort(graph)
  for node in sorted_nodes:
    resolve(node)
  return resolved_components
```
- **Pros**: Optimal resolution order, explicit cycle detection, dependency visualization
- **Cons**: More complex implementation, requires two passes (graph build + sort)
- **Complexity**: O(V + E) but with higher constant factor

### Critical Implementation Details

**Response Header Scanning** (Constitutional Requirement):
All algorithms must explicitly scan:
- `paths[*][*].responses[*].headers[*].$ref` → components.headers
- This is commonly missed and causes validation failures

**Locations to Scan for $ref**:
1. Operation parameters: `paths[path][method].parameters[*].$ref`
2. Request body schema: `paths[path][method].requestBody.content[*].schema.$ref`
3. Response schemas: `paths[path][method].responses[*].content[*].schema.$ref`
4. Response headers: `paths[path][method].responses[*].headers[*].$ref` ← CRITICAL
5. Security schemes: `paths[path][method].security[*]` → components.securitySchemes
6. Nested schemas: Within any schema, check `properties[*]`, `items`, `allOf`, `oneOf`, `anyOf`, `not`

### Decision

**Selected: Breadth-First Search with Visited Set + Explicit Response Header Scanning**

**Rationale**:
1. BFS provides natural deduplication via visited set
2. Level-by-level processing aligns with validation phase structure
3. Easier to implement max-depth safeguard (constitutional constraint: 100 levels)
4. Explicit scanning checklist prevents missed references
5. Circular refs handled by visited set check before processing

**Pseudocode**:
```python
def resolve_all_references(operation: dict, components: dict) -> dict:
    """Resolve all transitive references for a single operation."""
    refs_to_process = deque()
    visited_refs = set()
    resolved_components = {
        'schemas': {},
        'parameters': {},
        'headers': {},
        'securitySchemes': {}
    }

    # Phase 1: Collect initial refs from operation
    refs_to_process.extend(extract_parameter_refs(operation))
    refs_to_process.extend(extract_request_body_refs(operation))
    refs_to_process.extend(extract_response_refs(operation))
    refs_to_process.extend(extract_response_header_refs(operation))  # CRITICAL
    refs_to_process.extend(extract_security_refs(operation))

    # Phase 2: BFS traversal
    while refs_to_process:
        ref_string = refs_to_process.popleft()

        if ref_string in visited_refs:
            continue  # Already processed (handles circular refs)

        visited_refs.add(ref_string)
        component_type, component_name = parse_ref(ref_string)
        component_content = fetch_from_components(components, component_type, component_name)

        if component_content is None:
            raise UnresolvedReferenceError(ref_string)

        # Store resolved component
        resolved_components[component_type][component_name] = component_content

        # Phase 3: Extract nested refs from this component
        nested_refs = extract_nested_refs(component_content)
        refs_to_process.extend(nested_refs)

    return resolved_components
```

**Complexity**: O(V + E) where V = unique components, E = total $ref entries
**Max Depth Safeguard**: Track level depth, fail if >100 (constitutional constraint)

**Alternatives Rejected**:
- DFS: No advantage over BFS; visited set handles cycles in both
- Topological Sort: Unnecessary complexity; circular refs are valid in OAS

---

## Research Task 3: Version Conversion Strategies

### Question
How should unconvertible structures be handled when converting 3.1→3.0 (e.g., JSON Schema conditionals, multi-type unions)?

### Options Evaluated

#### Option 1: Fail Fast with Clear Error
- **Approach**: Detect unconvertible structures before conversion; return user-friendly error message
- **Example**: "This endpoint uses JSON Schema 'if/then/else' which cannot be converted to OAS 3.0.x. Please use OAS 3.1.x output format."
- **Pros**: Deterministic, no data loss, clear user guidance
- **Cons**: May reject files that could be partially converted
- **Constitutional Alignment**: Meets deterministic requirement (FR-020)

#### Option 2: Partial Conversion with Warnings
- **Approach**: Convert compatible structures, skip or simplify unconvertible parts, log warnings
- **Example**: Convert `type: ["string", "integer"]` → `type: string` (first type only) + warning
- **Pros**: Maximizes conversion success rate
- **Cons**: Data loss, non-deterministic (user may not see warnings), violates FR-020
- **Constitutional Alignment**: Violates deterministic conversion requirement

#### Option 3: Schema Approximation
- **Approach**: Approximate unconvertible structures with closest 3.0.x equivalent
- **Example**: `if/then/else` → `oneOf` with all branches
- **Pros**: Preserves intent in most cases
- **Cons**: Semantic differences, potential validation failures, complex implementation
- **Constitutional Alignment**: Questionable determinism

### Decision

**Selected: Fail Fast with Clear Error + Pre-Conversion Validation**

**Rationale**:
1. Constitutional requirement: deterministic conversion (FR-020)
2. Prevents silent data loss or semantic changes
3. User gets actionable error: "Use OAS 3.1.x output format for this endpoint"
4. Simpler implementation with fewer edge cases
5. Aligns with black-box UX principle: clear, actionable messages

**Conversion Rules Table**:

| Feature | 3.0→3.1 | 3.1→3.0 | Convertible? |
|---------|---------|---------|--------------|
| `nullable: true` | → `type: [original, "null"]` | ← `type: string, nullable: true` | ✓ Yes |
| Multi-type union (non-null) | N/A | `type: ["string", "integer"]` → FAIL | ✗ No |
| `webhooks` section | Add empty `webhooks: {}` | Remove entire section | ✓ Yes |
| `pathItems` in components | Keep as-is | Remove from components | ✓ Yes |
| `mutualTLS` security | Keep as-is | Remove + warn user | ⚠ Partial (loss of security info) |
| JSON Schema `if/then/else` | Keep as-is | FAIL with message | ✗ No |
| JSON Schema `unevaluatedProperties` | Keep as-is | FAIL with message | ✗ No |
| License `identifier` | Keep `url` if present | If only `identifier` → FAIL | ⚠ Partial |
| `examples` array in schema | Use as-is | Convert first to `example` | ✓ Yes |

**Pre-Conversion Validation** (for 3.1→3.0):
```python
def validate_convertible_to_3_0(oas_content: dict) -> bool:
    """Check if OAS 3.1.x can be converted to 3.0.x without data loss."""
    issues = []

    # Check for JSON Schema conditionals
    if has_json_schema_conditionals(oas_content):
        issues.append("Uses JSON Schema 'if/then/else' conditionals")

    # Check for multi-type unions (excluding nullables)
    if has_multi_type_unions(oas_content):
        issues.append("Uses multi-type unions (e.g., type: ['string', 'integer'])")

    # Check for unevaluatedProperties
    if has_unevaluated_properties(oas_content):
        issues.append("Uses 'unevaluatedProperties' keyword")

    # Check for identifier-only license
    if has_identifier_only_license(oas_content):
        issues.append("License uses 'identifier' without 'url'")

    if issues:
        raise UnconvertibleStructureError(
            "Cannot convert to OAS 3.0.x:\n" + "\n".join(f"- {i}" for i in issues) +
            "\n\nPlease use OAS 3.1.x output format for this endpoint."
        )

    return True
```

**User-Facing Error Messages** (Black Box Compliant):
- Technical: "Schema contains if/then/else keywords incompatible with OAS 3.0.x"
- User-Friendly: "This endpoint uses advanced validation rules that require OpenAPI 3.1 format. Please select '3.1' as your output version."

**Alternatives Rejected**:
- Partial conversion with warnings: Violates deterministic requirement, risks silent data loss
- Schema approximation: Too complex, semantic changes unacceptable, hard to validate

---

## Research Task 4: CSV Index Concurrency

### Question
How to ensure CSV file integrity when writing real-time updates during batch processing?

### Options Evaluated

#### Option 1: File Locking (fcntl/msvcrt)
- **Approach**: Acquire exclusive lock before each append, release after write
- **Pros**: Prevents concurrent write corruption
- **Cons**: Platform-specific (Unix vs Windows), not needed (single-threaded CLI)
- **Assessment**: Over-engineering for single-threaded use case

#### Option 2: Append-Only with Post-Processing Deduplication
- **Approach**: Append each entry immediately; deduplicate at end if needed
- **Pros**: Simplest implementation, no locking needed
- **Cons**: Duplicates possible if user interrupts and re-runs
- **Assessment**: Acceptable with pre-append duplicate check

#### Option 3: In-Memory Buffer with Final Write
- **Approach**: Collect all entries in memory, write CSV once at end
- **Pros**: Atomic write, no partial CSV files
- **Cons**: Violates constitutional requirement for real-time updates (Principle V)
- **Assessment**: Not compliant with constitution

### Decision

**Selected: Append-Only with Pre-Write Duplicate Check**

**Rationale**:
1. Constitutional requirement: real-time updates after each successful slice (Principle V)
2. Single-threaded CLI (no concurrent writes)
3. Pre-append check prevents duplicates: before writing, scan CSV for existing path+method
4. Simpler than file locking, platform-independent
5. Handles interruption/resume gracefully

**Implementation**:
```python
def append_to_csv_index(entry: CSVIndexEntry, csv_path: Path) -> None:
    """Append entry to CSV index with duplicate detection."""
    # Phase 1: Check for existing entry
    if csv_path.exists():
        existing_entries = read_csv(csv_path)
        for existing in existing_entries:
            if existing['path'] == entry.path and existing['method'] == entry.method:
                # Update existing entry instead of duplicating
                update_csv_entry(csv_path, entry)
                return

    # Phase 2: Append new entry
    with csv_path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if csv_path.stat().st_size == 0:
            writer.writeheader()  # Write header if file is new
        writer.writerow(entry.to_dict())
```

**CSV Structure**:
```csv
path,method,summary,description,operationId,tags,filename,file_size_kb,schema_count,parameter_count,response_codes,security_required,deprecated,created_at,output_oas_version
/users/{id},GET,Get user by ID,Retrieve a single user,getUserById,"users,accounts",users-id-get.yaml,12.3,5,1,"200,404",true,false,2025-12-17T10:30:00Z,3.1.0
```

**Edge Cases**:
- Empty CSV: Write header row first
- Interrupted processing: Next run checks for duplicates, continues safely
- Manual CSV edits: Preserved (append-only doesn't overwrite)

**Performance**: O(n) duplicate check per append (n = existing entries). For 1000 endpoints, negligible (<100ms total).

**Alternatives Rejected**:
- File locking: Unnecessary complexity for single-threaded tool
- In-memory buffer: Violates real-time update requirement

---

## Research Task 5: Black-Box Error Message Design

### Question
What patterns convert technical validation errors into actionable plain-language guidance?

### Constitutional Constraint
95% of error messages must be actionable and understandable to non-technical users (SC-009)

### Error Categories and Templates

#### Category 1: File Path Errors
| Technical Error | User-Friendly Message | Actionable Guidance |
|----------------|----------------------|---------------------|
| FileNotFoundError | "The file path you provided doesn't exist." | "Please check the path and try again. Make sure you're using the complete file path (e.g., /home/user/api.yaml)." |
| PermissionError (read) | "You don't have permission to read this file." | "Please check the file permissions or try a different file location." |
| PermissionError (write) | "You don't have permission to write to this directory." | "Please choose a different output directory or check folder permissions." |
| IsADirectoryError | "The path you provided is a directory, not a file." | "Please provide the full path to the OpenAPI file, including the filename (e.g., /path/to/api.yaml)." |

#### Category 2: OAS Validation Errors
| Technical Error | User-Friendly Message | Actionable Guidance |
|----------------|----------------------|---------------------|
| Invalid YAML/JSON syntax | "The file has formatting errors and can't be read." | "Please check that the file is valid YAML or JSON. You can use an online validator to find syntax errors." |
| Missing `openapi` field | "This doesn't appear to be an OpenAPI specification file." | "Please make sure the file has an 'openapi' field at the top (e.g., openapi: 3.0.3)." |
| Unsupported version (2.0) | "This tool only supports OpenAPI 3.0 and 3.1 formats." | "The file you provided is in Swagger 2.0 format. Please convert it to OpenAPI 3.x first." |
| Unsupported version (3.2+) | "This OpenAPI version (3.2) is not yet supported." | "This tool supports OpenAPI 3.0.x and 3.1.x. Please use a compatible version." |

#### Category 3: Resource Specification Errors
| Technical Error | User-Friendly Message | Actionable Guidance |
|----------------|----------------------|---------------------|
| Path not found | "The path '/users/{id}' doesn't exist in this OpenAPI file." | "Please check the available paths in your file. You can extract all endpoints with '--batch' to see what's available." |
| Method not found for path | "The path '/users' exists, but it doesn't have a GET operation." | "Available methods for this path: POST, PUT. Please specify one of these instead." |
| Invalid method name | "The method 'FETCH' is not a valid HTTP method." | "Please use a standard HTTP method: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, or TRACE." |

#### Category 4: Reference Resolution Errors
| Technical Error | User-Friendly Message | Actionable Guidance |
|----------------|----------------------|---------------------|
| Unresolved $ref | "The endpoint references a component '#/components/schemas/User' that doesn't exist in the file." | "This usually means the OpenAPI file is incomplete or has broken references. Please check the source file for errors." |
| External $ref detected | "The endpoint references an external file, which is not supported." | "This tool only works with self-contained OpenAPI files. Please combine all external references into a single file first." |
| Circular reference (informational) | "The endpoint has circular schema references (this is OK)." | "Circular references are supported. The output will include all referenced schemas." |

#### Category 5: Version Conversion Errors
| Technical Error | User-Friendly Message | Actionable Guidance |
|----------------|----------------------|---------------------|
| Unconvertible structure (if/then/else) | "This endpoint uses advanced validation rules that require OpenAPI 3.1 format." | "Please select '3.1' as your output version instead of '3.0'." |
| Unconvertible structure (multi-type) | "This endpoint uses multi-type fields that cannot be converted to OpenAPI 3.0 format." | "Please select '3.1' as your output version to preserve all data." |
| mutualTLS in 3.1→3.0 | "Warning: This endpoint uses mutual TLS authentication, which is not supported in OpenAPI 3.0." | "The security scheme will be removed from the output. Consider using OpenAPI 3.1 format to preserve it." |

#### Category 6: Validation Phase Failures
| Technical Error | User-Friendly Message | Actionable Guidance |
|----------------|----------------------|---------------------|
| Phase 1 failure (file structure) | "The output file couldn't be created due to a formatting error." | "This is an internal error. Please report this with your input file." |
| Phase 4 failure (unresolved refs) | "The extracted endpoint has missing components." | "The source file may be incomplete. Please verify all references in the original file resolve correctly." |
| Phase 6 failure (payload mismatch) | "The extracted endpoint doesn't match the original specification." | "This is an internal error. Please report this with your input file." |
| Phase 7 failure (version mismatch) | "The output file doesn't conform to the selected OpenAPI version." | "This may be due to version conversion issues. Try using the same version as the input file." |

### Error Message Structure

```python
class UserFriendlyError(Exception):
    """Base class for all user-facing errors."""
    def __init__(self, message: str, guidance: str, technical_detail: str = None):
        self.message = message  # Plain language description
        self.guidance = guidance  # Actionable next steps
        self.technical_detail = technical_detail  # For debugging (not shown to users)
        super().__init__(self.format_for_user())

    def format_for_user(self) -> str:
        """Format error for black-box UX."""
        output = f"\n{self.message}\n\n{self.guidance}"
        return output

    def format_for_debug(self) -> str:
        """Format error with technical details (only if --debug flag set)."""
        output = self.format_for_user()
        if self.technical_detail:
            output += f"\n\nTechnical details: {self.technical_detail}"
        return output
```

### Decision

**Selected: Layered Error Handling with Template-Based Messages**

**Implementation**:
1. All internal exceptions converted to UserFriendlyError subclasses
2. Error templates stored in exceptions.py
3. CLI layer catches all errors and formats with format_for_user()
4. Optional --debug flag shows technical details for power users
5. Each error has: message (what happened) + guidance (what to do)

**Testing**: Error message unit tests verify:
- No technical jargon (regex check for "$ref", "schema", "component")
- Actionable guidance present (length check, imperative verb check)
- User-facing only (no stack traces, no code references)

**Alternatives Rejected**:
- Generic error messages: Not actionable enough
- Technical errors shown to users: Violates black-box principle

---

## Summary

All research tasks complete. Key decisions:

1. **Parsing**: Custom parser with PyYAML + jsonschema + openapi-spec-validator
2. **Reference Resolution**: BFS with visited set + explicit response header scanning
3. **Version Conversion**: Fail fast on unconvertible structures with clear user guidance
4. **CSV Concurrency**: Append-only with pre-write duplicate check
5. **Error Messages**: Template-based user-friendly messages with actionable guidance

Next phase: Create data-model.md and contracts/cli-interface.md
