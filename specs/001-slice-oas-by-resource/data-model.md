# Data Model: slice-oas-by-resource

**Feature**: slice-oas-by-resource
**Phase**: Phase 1 (Design & Contracts)
**Date**: 2025-12-17

---

## Entity Relationship Overview

```
OASDocument
  ├── has many → Resource (Endpoint)
  │     ├── has many → Reference
  │     │     └── resolves to → ResolvedComponent
  │     │           └── has many → Reference (transitive)
  │     └── produces → CSVIndexEntry
  │
  ├── processed by → VersionConverter
  │     └── uses many → TransformationRule
  │
  └── validated by → ValidationResult (7 phases)
```

---

## Core Entities

### 1. OASDocument

**Purpose**: Represents a parsed OpenAPI specification file.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| file_path | Path | Yes | Absolute path to source OAS file | Must exist, must be readable |
| version | str | Yes | OAS version (e.g., "3.0.3", "3.1.0") | Must match regex `^3\.(0\|1)\.\d+$` |
| format | Enum[JSON, YAML] | Yes | File format | Detected from extension or content |
| content | dict | Yes | Parsed OAS content | Must have `openapi`, `info`, `paths` keys |
| endpoints | List[Resource] | Yes | All endpoints extracted from paths | Generated on parse |

**State Transitions**:
```
Created → Loaded → Validated → Ready for Slicing
```

**Methods**:
- `parse_file(file_path: Path) -> OASDocument`: Load and parse OAS file
- `detect_version() -> str`: Extract version from `openapi` field
- `extract_endpoints() -> List[Resource]`: Build Resource list from paths
- `validate_structure() -> bool`: Check required root keys present

**Validation Rules**:
1. File must exist and be readable
2. Content must be valid JSON or YAML
3. `openapi` field must be present and match `3.(0|1).x`
4. `info` section must be present with at least `title` and `version`
5. `paths` section must be present (may be empty)

**Example**:
```python
doc = OASDocument(
    file_path=Path("/data/petstore.yaml"),
    version="3.0.3",
    format=Format.YAML,
    content={"openapi": "3.0.3", "info": {...}, "paths": {...}},
    endpoints=[...]
)
```

---

### 2. Resource (Endpoint)

**Purpose**: Represents a single API endpoint (path + method combination).

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| path | str | Yes | Path template (e.g., "/users/{id}") | Must exist in source OAS paths |
| method | str | Yes | HTTP method (lowercase) | Must be in [get, post, put, delete, patch, head, options, trace] |
| operation | dict | Yes | Full operation object from OAS | Must be dict with at least `responses` key |
| operation_id | str | No | Unique operation identifier | If present, must be unique in source OAS |
| summary | str | No | Short description | Extracted from operation.summary |
| description | str | No | Full description | Extracted from operation.description |
| tags | List[str] | No | Categorization tags | Extracted from operation.tags |
| security | List[dict] | No | Security requirements | Extracted from operation.security or root security |
| deprecated | bool | No | Deprecation status | Extracted from operation.deprecated, defaults to false |

**Relationships**:
- Has many `Reference` objects (extracted from operation)
- Produces one `CSVIndexEntry` when sliced

**Methods**:
- `extract_references() -> List[Reference]`: Scan operation for all $ref entries
- `to_standalone_oas(resolved_components: dict, output_version: str) -> dict`: Build complete OAS file
- `generate_filename(format: Format) -> str`: Create output filename (path sanitized + method + format)

**Validation Rules**:
1. Path must exist in source OAS
2. Method must be valid HTTP verb (lowercase)
3. Operation must have `responses` section
4. If operation_id present, must be unique

**Example**:
```python
resource = Resource(
    path="/users/{id}",
    method="get",
    operation={"summary": "Get user", "responses": {"200": {...}}},
    operation_id="getUserById",
    summary="Get user by ID",
    tags=["users"],
    security=[{"apiKey": []}],
    deprecated=False
)
```

---

### 3. Reference

**Purpose**: Represents a single $ref pointer in the OpenAPI specification.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| ref_string | str | Yes | Full $ref value (e.g., "#/components/schemas/User") | Must start with "#/" for internal refs |
| ref_type | Enum | Yes | Type of reference | One of: schema, parameter, header, security, response, example, requestBody |
| source_location | str | Yes | Where this ref was found | For debugging/error messages |
| target | ResolvedComponent | No | Resolved component (set after resolution) | Populated by resolver |

**Enums**:
```python
class RefType(Enum):
    SCHEMA = "schemas"
    PARAMETER = "parameters"
    HEADER = "headers"
    SECURITY = "securitySchemes"
    RESPONSE = "responses"
    EXAMPLE = "examples"
    REQUEST_BODY = "requestBodies"
```

**Methods**:
- `parse_ref() -> Tuple[RefType, str]`: Extract type and name from ref_string
- `is_external() -> bool`: Check if ref points outside file (returns True if starts with "http" or "../")
- `resolve(components: dict) -> ResolvedComponent`: Fetch target from components section

**Validation Rules**:
1. Internal refs must start with `#/`
2. Must follow format `#/components/{type}/{name}`
3. External refs (http://, ../) are not supported (raise error)

**Example**:
```python
ref = Reference(
    ref_string="#/components/schemas/User",
    ref_type=RefType.SCHEMA,
    source_location="paths./users/{id}.get.responses.200.content.application/json.schema",
    target=None  # Populated by resolver
)
```

---

### 4. ResolvedComponent

**Purpose**: Represents a component fetched from the components section with all its transitive dependencies.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| component_type | RefType | Yes | Type of component | Must match ref_type from Reference |
| component_name | str | Yes | Component name | Must exist in components section |
| content | dict | Yes | Full component definition | Must be valid schema/parameter/etc. |
| transitive_refs | List[Reference] | Yes | All refs within this component | Extracted during resolution |

**Methods**:
- `collect_dependencies(components: dict, visited: Set[str]) -> dict`: Recursively resolve all nested refs
- `extract_nested_refs() -> List[Reference]`: Scan content for $ref entries

**Validation Rules**:
1. Content must conform to OAS schema for component type
2. All transitive_refs must be resolvable

**Example**:
```python
resolved = ResolvedComponent(
    component_type=RefType.SCHEMA,
    component_name="User",
    content={
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "address": {"$ref": "#/components/schemas/Address"}
        }
    },
    transitive_refs=[
        Reference(ref_string="#/components/schemas/Address", ...)
    ]
)
```

---

### 5. ValidationResult

**Purpose**: Captures the result of a single validation phase.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| phase | int | Yes | Phase number (1-7) | Must be 1-7 |
| phase_name | str | Yes | Human-readable phase name | From predefined list |
| passed | bool | Yes | Whether phase passed | - |
| error_message | str | Conditional | Technical error description | Required if passed=False |
| user_message | str | Conditional | Plain-language error | Required if passed=False |
| details | dict | No | Additional context | For debugging |

**Validation Phases** (Constitutional Requirement):
1. **File Structure**: Valid JSON/YAML, root keys present
2. **Operation Integrity**: Single path, single method, correct definition
3. **Response Integrity**: Codes match, headers resolve, schemas present
4. **Reference Resolution**: ALL $ref entries resolve to existing components
5. **Component Completeness**: No orphaned refs, required components non-empty
6. **Payload Equivalence**: Operation matches parent spec exactly
7. **Version Validation**: OAS version matches requested, schema syntax correct

**Methods**:
- `to_user_message() -> str`: Convert technical details to plain language (uses error message templates from research.md)
- `to_dict() -> dict`: Serialize for logging

**Validation Rules**:
1. If passed=False, both error_message and user_message must be present
2. Phase must be in range 1-7
3. phase_name must match standard phase names

**Example**:
```python
result = ValidationResult(
    phase=4,
    phase_name="Reference Resolution",
    passed=False,
    error_message="Unresolved reference: #/components/schemas/User",
    user_message="The endpoint references a component that doesn't exist in the file. Please check the source file for errors.",
    details={"ref": "#/components/schemas/User", "location": "responses.200.content"}
)
```

---

### 6. CSVIndexEntry

**Purpose**: Represents a single row in the CSV tracking file.

**Fields** (Constitutional Requirement - Exact Order):
| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| path | str | Yes | API path template | "/users/{id}" |
| method | str | Yes | HTTP method (uppercase) | "GET" |
| summary | str | No | Short description | "Get user by ID" |
| description | str | No | Full description | "Retrieve a single user..." |
| operation_id | str | No | Operation identifier | "getUserById" |
| tags | str | No | Comma-separated tags | "users,accounts" |
| filename | str | Yes | Output file name | "users-id-get.yaml" |
| file_size_kb | float | Yes | Output file size in KB | 12.3 |
| schema_count | int | Yes | Number of schemas included | 5 |
| parameter_count | int | Yes | Number of parameters | 1 |
| response_codes | str | Yes | Comma-separated codes | "200,404" |
| security_required | bool | Yes | Whether security is required | true |
| deprecated | bool | Yes | Deprecation status | false |
| created_at | str | Yes | ISO 8601 timestamp | "2025-12-17T10:30:00Z" |
| output_oas_version | str | Yes | Output OAS version | "3.1.0" |

**Methods**:
- `to_csv_row() -> dict`: Format as RFC 4180 compliant CSV row
- `from_resource(resource: Resource, output_file: Path, version: str) -> CSVIndexEntry`: Factory method

**Validation Rules**:
1. path and method are required
2. created_at must be ISO 8601 format
3. output_oas_version must match `^3\.(0\|1)\.\d+$`
4. Tags must be comma-separated without quotes
5. All string fields must escape quotes and commas per RFC 4180

**CSV Format Example**:
```csv
path,method,summary,description,operationId,tags,filename,file_size_kb,schema_count,parameter_count,response_codes,security_required,deprecated,created_at,output_oas_version
/users/{id},GET,Get user by ID,Retrieve a single user,getUserById,"users,accounts",users-id-get.yaml,12.3,5,1,"200,404",true,false,2025-12-17T10:30:00Z,3.1.0
```

---

## Version Conversion Entities

### 7. VersionConverter

**Purpose**: Handles conversion between OAS 3.0.x and 3.1.x.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| source_version | str | Yes | Input OAS version | Must be 3.0.x or 3.1.x |
| target_version | str | Yes | Desired output version | Must be 3.0.x or 3.1.x |
| transformation_rules | List[TransformationRule] | Yes | Rules to apply | Selected based on direction |

**Methods**:
- `validate_convertible(content: dict) -> bool`: Check for unconvertible structures (raises error if found)
- `convert(content: dict) -> dict`: Apply all transformation rules
- `get_rules_for_direction() -> List[TransformationRule]`: Select rules based on source→target

**Validation Rules**:
1. Source and target must be different families (3.0.x vs 3.1.x)
2. If converting 3.1→3.0, must pass validate_convertible() check
3. Conversion must be deterministic (same input → same output)

**Example**:
```python
converter = VersionConverter(
    source_version="3.0.3",
    target_version="3.1.0",
    transformation_rules=[
        NullableToTypeArrayRule(),
        AddWebhooksRule(),
        ...
    ]
)
```

---

### 8. TransformationRule

**Purpose**: Defines a single transformation for version conversion.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| name | str | Yes | Rule identifier | Unique within ruleset |
| applies_to | Enum | Yes | Conversion direction | 3.0→3.1 or 3.1→3.0 |
| pattern | Callable | Yes | Matching function | Returns True if rule applies |
| action | Callable | Yes | Transformation function | Modifies content in-place or returns new |

**Enums**:
```python
class ConversionDirection(Enum):
    TO_3_1 = "3.0→3.1"
    TO_3_0 = "3.1→3.0"
```

**Built-in Transformation Rules**:

#### For 3.0 → 3.1:
1. **NullableToTypeArrayRule**: `nullable: true` → `type: [original, "null"]`
2. **AddWebhooksRule**: Add empty `webhooks: {}` section if not present
3. **PreserveAllRule**: Keep all other structures as-is (3.1 is superset)

#### For 3.1 → 3.0:
1. **TypeArrayToNullableRule**: `type: [type, "null"]` → `type: type, nullable: true`
2. **RemoveWebhooksRule**: Delete `webhooks` section entirely
3. **RemovePathItemsRule**: Delete `pathItems` from components
4. **RemoveMutualTLSRule**: Remove `mutualTLS` security schemes + warn user
5. **DetectConditionalsRule**: Detect `if/then/else` → FAIL (unconvertible)
6. **DetectMultiTypeUnionsRule**: Detect non-nullable multi-type → FAIL
7. **ConvertLicenseRule**: If only `identifier` → FAIL; if both, keep only `url`

**Methods**:
- `matches(content: dict, location: str) -> bool`: Check if rule applies to this content
- `transform(content: dict, location: str) -> dict`: Apply transformation

**Example**:
```python
class NullableToTypeArrayRule(TransformationRule):
    name = "nullable_to_type_array"
    applies_to = ConversionDirection.TO_3_1

    def matches(self, content: dict, location: str) -> bool:
        return "nullable" in content and content["nullable"] is True

    def transform(self, content: dict, location: str) -> dict:
        original_type = content.get("type", "string")
        content["type"] = [original_type, "null"]
        del content["nullable"]
        return content
```

---

## Data Flow Diagram

```
1. User provides input file path
   ↓
2. OASDocument.parse_file(path)
   ↓
3. OASDocument.extract_endpoints() → List[Resource]
   ↓
4. User selects Resource to slice
   ↓
5. Resource.extract_references() → List[Reference]
   ↓
6. For each Reference:
   6a. Reference.resolve(components) → ResolvedComponent
   6b. ResolvedComponent.collect_dependencies() → more References
   6c. Repeat until visited set complete (handles circular refs)
   ↓
7. If version conversion requested:
   7a. VersionConverter.validate_convertible()
   7b. VersionConverter.convert(content) → transformed content
   ↓
8. Resource.to_standalone_oas(resolved_components, output_version) → OAS dict
   ↓
9. For each ValidationPhase (1-7):
   9a. Run validation → ValidationResult
   9b. If failed: return error, abort
   ↓
10. Write output file
    ↓
11. CSVIndexEntry.from_resource() → append to CSV
    ↓
12. Return success message to user
```

---

## State Diagrams

### Resource Slicing State Machine

```
[User Input] → [File Loaded] → [Endpoints Extracted] → [Resource Selected]
                                                              ↓
                                                    [References Extracted]
                                                              ↓
                                                    [References Resolved] ← (circular refs handled)
                                                              ↓
                                          [Version Conversion] (if needed)
                                                              ↓
                                                [Standalone OAS Created]
                                                              ↓
                                                [Validation Phase 1-7]
                                                   ↓              ↓
                                              [Failed]      [Passed]
                                                   ↓              ↓
                                            [Error to User] [File Written]
                                                              ↓
                                                       [CSV Updated]
                                                              ↓
                                                    [Success Message]
```

### Validation Phase Dependencies

```
Phase 1: File Structure
    ↓ (must pass)
Phase 2: Operation Integrity
    ↓ (must pass)
Phase 3: Response Integrity
    ↓ (must pass)
Phase 4: Reference Resolution
    ↓ (must pass)
Phase 5: Component Completeness
    ↓ (must pass)
Phase 6: Payload Equivalence
    ↓ (must pass)
Phase 7: Version Validation
    ↓ (must pass)
[File Accepted]
```

Any phase failure → Entire validation fails → File rejected

---

## Validation Rules Summary

### Constitutional Requirements
1. All fields must be validated according to OAS 3.0.x or 3.1.x schema
2. Reference resolution must include response headers (commonly missed)
3. Circular references are valid and must be preserved
4. Version conversion must be deterministic
5. Validation must follow 7-phase pipeline (no shortcuts)

### Data Integrity
1. All $ref entries must resolve within the sliced file (no external refs)
2. CSV index must match exact column order specified in constitution
3. Timestamps must be ISO 8601 format
4. File paths must be absolute
5. Version strings must match semantic versioning pattern for 3.0.x or 3.1.x

---

## Next Steps

This data model will be implemented using:
- **Pydantic v2** for data validation and serialization
- **Enums** for type safety (RefType, ConversionDirection, etc.)
- **Type hints** throughout for IDE support and runtime checking
- **dataclasses** for lightweight entities (ValidationResult, CSVIndexEntry)

Next phase: Define CLI interface contract in `contracts/cli-interface.md`
