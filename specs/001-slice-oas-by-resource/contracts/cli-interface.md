# CLI Interface Contract: slice-oas-by-resource

**Feature**: slice-oas-by-resource
**Phase**: Phase 1 (Design & Contracts)
**Date**: 2025-12-17

---

## Overview

The slice-oas-by-resource tool is invoked as a Python module from the command line. It provides a conversational, black-box interface where technical details are hidden from non-programmer users.

**Invocation Format**:
```bash
python -m slice_oas [COMMAND] [OPTIONS]
```

---

## Commands

### 1. Single Resource Extraction

**Purpose**: Extract a single endpoint from an OAS file into a standalone specification.

**Syntax**:
```bash
python -m slice_oas extract \
  --input <file_path> \
  --output-dir <directory_path> \
  --resource <path:method> \
  [--format json|yaml] \
  [--output-version 3.0|3.1]
```

**Required Arguments**:
| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--input` | Path | Absolute path to input OAS file | `/home/user/api.yaml` |
| `--output-dir` | Path | Absolute path to output directory | `/home/user/sliced` |
| `--resource` | String | Resource identifier (path:method) | `/users/{id}:GET` |

**Optional Arguments**:
| Argument | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `--format` | Enum | Same as input | Output format (json or yaml) | `yaml` |
| `--output-version` | String | Same as input | Output OAS version (3.0 or 3.1) | `3.1` |

**Resource Identifier Format**:
- Pattern: `<path>:<method>`
- Path: Exact path template from OAS (case-sensitive)
- Method: HTTP method (case-insensitive)
- Separator: Single colon `:`
- Examples:
  - `/users/{id}:GET`
  - `/api/v1/products:POST`
  - `/health:get` (lowercase method is ok)

**Examples**:
```bash
# Extract GET /users/{id} as YAML in OAS 3.1 format
python -m slice_oas extract \
  --input /data/petstore.yaml \
  --output-dir /output \
  --resource "/users/{id}:GET" \
  --format yaml \
  --output-version 3.1

# Extract POST /products with same format as input
python -m slice_oas extract \
  --input /data/api.json \
  --output-dir /output \
  --resource "/products:POST"
```

**Success Output** (Black Box - Plain Language):
```
Successfully extracted GET /users/{id}

Output file: /output/users-id-get.yaml
File size: 12.3 KB
OpenAPI version: 3.1.0
Schemas included: 5
Parameters: 1
Response codes: 200, 404

The endpoint has been saved and added to the tracking index.
```

**Error Output Examples**:
```
Error: The file path you provided doesn't exist.

Please check the path and try again. Make sure you're using the complete file path (e.g., /home/user/api.yaml).
```

```
Error: The path '/users/{id}' doesn't exist in this OpenAPI file.

Please check the available paths in your file. You can extract all endpoints with the 'batch' command to see what's available.
```

---

### 2. Batch Extraction

**Purpose**: Extract all or filtered endpoints from an OAS file.

**Syntax**:
```bash
python -m slice_oas batch \
  --input <file_path> \
  --output-dir <directory_path> \
  [--filter <pattern>] \
  [--format json|yaml] \
  [--output-version 3.0|3.1]
```

**Required Arguments**:
| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--input` | Path | Absolute path to input OAS file | `/home/user/api.yaml` |
| `--output-dir` | Path | Absolute path to output directory | `/home/user/sliced` |

**Optional Arguments**:
| Argument | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `--filter` | String | None (all) | Path prefix pattern | `/users/*` |
| `--format` | Enum | Same as input | Output format | `yaml` |
| `--output-version` | String | Same as input | Output OAS version | `3.1` |

**Filter Patterns**:
- Glob-style wildcards supported
- Examples:
  - `/users/*` - All paths starting with /users/
  - `/api/v1/*` - All paths in /api/v1/
  - `*` - All paths (default if omitted)

**Examples**:
```bash
# Extract all endpoints
python -m slice_oas batch \
  --input /data/petstore.yaml \
  --output-dir /output

# Extract only user-related endpoints
python -m slice_oas batch \
  --input /data/api.yaml \
  --output-dir /output \
  --filter "/users/*" \
  --format yaml \
  --output-version 3.1
```

**Success Output** (Real-Time Progress):
```
Starting batch extraction from /data/api.yaml

Processing endpoints:
[1/45] Extracting GET /users... ✓
[2/45] Extracting POST /users... ✓
[3/45] Extracting GET /users/{id}... ✓
...
[45/45] Extracting DELETE /orders/{id}... ✓

Batch extraction complete!

Endpoints processed: 45
Successful: 45
Failed: 0
Output directory: /output
Tracking index: /output/sliced-resources-index.csv

All endpoints have been extracted and validated.
```

**Progress Indicators**:
- Real-time progress: `[current/total] Extracting METHOD /path... ✓`
- Success: Green checkmark (✓) in terminal
- Failure: Red X (✗) with error summary at end
- No technical details shown during processing (black-box requirement)

---

### 3. List Endpoints

**Purpose**: Show all available endpoints in an OAS file without extracting.

**Syntax**:
```bash
python -m slice_oas list \
  --input <file_path> \
  [--filter <pattern>]
```

**Required Arguments**:
| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--input` | Path | Absolute path to input OAS file | `/home/user/api.yaml` |

**Optional Arguments**:
| Argument | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `--filter` | String | None (all) | Path prefix pattern | `/users/*` |

**Example**:
```bash
python -m slice_oas list --input /data/api.yaml
```

**Output** (Plain Language Table):
```
Endpoints in /data/api.yaml (OpenAPI 3.0.3):

Path                    Method    Summary                  Tags
------------------------------------------------------------------------------
/users                  GET       List all users           users
/users                  POST      Create a new user        users
/users/{id}             GET       Get user by ID           users
/users/{id}             PUT       Update user              users
/users/{id}             DELETE    Delete user              users
/products               GET       List products            products
/products/{id}          GET       Get product by ID        products

Total endpoints: 7
```

---

### 4. Version Info

**Purpose**: Show detected OAS version and conversion compatibility.

**Syntax**:
```bash
python -m slice_oas version-info \
  --input <file_path>
```

**Example**:
```bash
python -m slice_oas version-info --input /data/api.yaml
```

**Output**:
```
OpenAPI Specification: /data/api.yaml

Detected version: 3.0.3
Format: YAML
File size: 456.2 KB
Total endpoints: 45

Conversion compatibility:
  ✓ Can convert to OpenAPI 3.1.x
  ✓ Can remain in OpenAPI 3.0.x

No conversion blockers detected.
```

**Output with Conversion Blockers**:
```
OpenAPI Specification: /data/api.yaml

Detected version: 3.1.0
Format: JSON
File size: 234.5 KB
Total endpoints: 12

Conversion compatibility:
  ✗ Cannot convert to OpenAPI 3.0.x

Blockers:
  - Uses JSON Schema 'if/then/else' conditionals (3 endpoints)
  - Uses multi-type unions (5 endpoints)

Recommendation: Keep as OpenAPI 3.1.x format for full compatibility.
```

---

## Common Options (All Commands)

### `--debug`
**Purpose**: Enable technical error messages for debugging (optional).

**Effect**:
- Normal mode (default): User-friendly error messages only
- Debug mode: Includes technical details, stack traces, and validation phase information

**Example**:
```bash
python -m slice_oas extract \
  --input /data/api.yaml \
  --output-dir /output \
  --resource "/users:GET" \
  --debug
```

**Debug Output Example**:
```
Error: The endpoint references a component that doesn't exist in the file.

Please check the source file for errors.

Technical details:
  Unresolved reference: #/components/schemas/User
  Location: responses.200.content.application/json.schema
  Validation phase: 4 (Reference Resolution)
  Stack trace: [...]
```

### `--help`
**Purpose**: Show help information for a command.

**Example**:
```bash
python -m slice_oas --help
python -m slice_oas extract --help
python -m slice_oas batch --help
```

---

## Output File Naming Convention

**Pattern**: `{sanitized_path}-{method}.{format}`

**Sanitization Rules**:
1. Remove leading slash
2. Replace all slashes with hyphens
3. Remove curly braces from path parameters
4. Convert to lowercase
5. Append HTTP method (lowercase)
6. Add file extension

**Examples**:
| Path | Method | Format | Output Filename |
|------|--------|--------|-----------------|
| `/users` | GET | yaml | `users-get.yaml` |
| `/users/{id}` | GET | json | `users-id-get.json` |
| `/api/v1/products` | POST | yaml | `api-v1-products-post.yaml` |
| `/users/{userId}/orders/{orderId}` | DELETE | json | `users-userid-orders-orderid-delete.json` |

**Collision Handling**:
If a file already exists, append a counter: `users-get-1.yaml`, `users-get-2.yaml`, etc.

---

## Exit Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 0 | Success | All operations completed successfully |
| 1 | File not found | Input file doesn't exist or isn't readable |
| 2 | Invalid OAS file | File is not a valid OpenAPI specification |
| 3 | Resource not found | Specified endpoint doesn't exist in OAS |
| 4 | Validation failure | Output failed one or more validation phases |
| 5 | Permission error | Cannot read input or write to output directory |
| 6 | Conversion error | Cannot convert between requested OAS versions |
| 7 | Unresolved reference | $ref entries cannot be resolved |
| 99 | Internal error | Unexpected error (should be reported as bug) |

**Usage in Scripts**:
```bash
python -m slice_oas extract --input api.yaml --output-dir ./output --resource "/users:GET"
if [ $? -eq 0 ]; then
  echo "Extraction successful"
else
  echo "Extraction failed with exit code $?"
fi
```

---

## Environment Variables

### `SLICE_OAS_CONFIG`
**Purpose**: Path to configuration file (optional, for advanced users).

**Format**: YAML file with default settings.

**Example Config**:
```yaml
# .slice-oas-config.yaml
defaults:
  format: yaml
  output_version: auto  # Use same version as input
  csv_index_name: sliced-resources-index.csv

validation:
  strict: true  # Fail on any validation phase failure
  max_depth: 100  # Max transitive reference depth

output:
  overwrite: false  # If true, overwrite existing files; if false, create versioned names
  include_source_comment: true  # Add comment with source file info at top of output
```

**Usage**:
```bash
export SLICE_OAS_CONFIG=/home/user/.slice-oas-config.yaml
python -m slice_oas extract --input api.yaml --output-dir ./output --resource "/users:GET"
```

---

## CSV Index Schema

**File Location**: `{output_dir}/sliced-resources-index.csv`

**Column Order** (Constitutional Requirement):
```
path | method | summary | description | operationId | tags | filename | file_size_kb | schema_count | parameter_count | response_codes | security_required | deprecated | created_at | output_oas_version
```

**Format**: RFC 4180 compliant CSV
- Header row always present
- Comma-separated values
- Quoted strings if containing commas or quotes
- UTF-8 encoding
- Unix line endings (LF)

**Example**:
```csv
path,method,summary,description,operationId,tags,filename,file_size_kb,schema_count,parameter_count,response_codes,security_required,deprecated,created_at,output_oas_version
/users/{id},GET,Get user by ID,Retrieve a single user by their ID,getUserById,"users,accounts",users-id-get.yaml,12.3,5,1,"200,404",true,false,2025-12-17T10:30:00Z,3.1.0
/users,POST,Create user,Create a new user account,createUser,users,users-post.yaml,8.7,3,0,"201,400,409",true,false,2025-12-17T10:30:05Z,3.1.0
```

**Deduplication**: If the same path+method is extracted again, the existing row is updated with new timestamp.

---

## Argument Validation Rules

### `--input`
1. Must be an absolute path (not relative)
2. File must exist
3. Must be readable by current user
4. Must be a file (not a directory)
5. Must have .yaml, .yml, or .json extension

**Error Messages**:
- Relative path: "Please provide the complete file path starting from the root (e.g., /home/user/api.yaml)."
- File doesn't exist: "The file path you provided doesn't exist. Please check the path and try again."
- Permission denied: "You don't have permission to read this file. Please check the file permissions."
- Is directory: "The path you provided is a directory, not a file. Please provide the full path including the filename."

### `--output-dir`
1. Must be an absolute path (not relative)
2. Directory must exist OR parent directory must exist and be writable
3. Must be writable by current user

**Error Messages**:
- Relative path: "Please provide the complete directory path starting from the root (e.g., /home/user/output)."
- Parent doesn't exist: "The output directory's parent folder doesn't exist. Please create it first or choose a different location."
- Permission denied: "You don't have permission to write to this directory. Please choose a different output directory."

### `--resource`
1. Must follow pattern `<path>:<method>`
2. Path must exist in input OAS file
3. Method must be valid HTTP verb
4. Format: exact path from OAS (case-sensitive) + colon + method (case-insensitive)

**Error Messages**:
- Invalid format: "Please use the format '/path:METHOD' (e.g., '/users/{id}:GET')."
- Path not found: "The path '/users/{id}' doesn't exist in this OpenAPI file. Available paths: [list]."
- Method not found: "The path '/users' exists, but it doesn't have a GET operation. Available methods: POST, PUT."

### `--format`
1. Must be either `json` or `yaml`
2. Case-insensitive

**Error Messages**:
- Invalid format: "Please choose either 'json' or 'yaml' as the output format."

### `--output-version`
1. Must be either `3.0` or `3.1`
2. If converting 3.1→3.0, pre-validation runs to check for blockers
3. If conversion not possible, error with guidance

**Error Messages**:
- Invalid version: "Please choose either '3.0' or '3.1' as the output version."
- Conversion blocked: "This endpoint uses advanced validation rules that require OpenAPI 3.1 format. Please select '3.1' as your output version."

### `--filter`
1. Glob-style pattern
2. Must start with `/` or `*`
3. Asterisk `*` matches any characters within a path segment

**Error Messages**:
- Invalid pattern: "Filter patterns should start with '/' or '*' (e.g., '/users/*')."

---

## Interaction Flow (Black Box UX)

### Single Extraction Flow
```
User runs command
  ↓
CLI validates arguments
  ↓ (if error)
Show plain-language error + guidance → Exit
  ↓ (if valid)
Load and validate OAS file
  ↓ (if error)
Show plain-language error + guidance → Exit
  ↓ (if valid)
Extract endpoint and resolve references
  ↓ (if error)
Show plain-language error + guidance → Exit
  ↓ (if valid)
Apply version conversion (if requested)
  ↓ (if error)
Show plain-language error + guidance → Exit
  ↓ (if valid)
Run 7-phase validation
  ↓ (if any phase fails)
Show which phase failed + plain-language error → Exit
  ↓ (all phases pass)
Write output file
Update CSV index
Show success message with file details → Exit code 0
```

### No Code/JSON/YAML Shown
Constitutional requirement: Black-box abstraction (Principle I).

**What users see**:
- Plain language prompts
- Progress indicators ("Processing...", "Validating...", "Complete!")
- Success messages with file locations and sizes
- Error messages with actionable guidance

**What users NEVER see** (unless --debug flag):
- JSON or YAML content
- Python stack traces
- Schema definitions
- $ref resolution details
- Validation algorithms
- Internal data structures

---

## Testing Contract Compliance

### Acceptance Tests for CLI Interface

1. **Argument Validation**: All invalid argument combinations return appropriate exit codes and user-friendly errors
2. **Black Box UX**: No technical details in normal mode; only plain language
3. **Progress Reporting**: Batch operations show real-time progress
4. **File Output**: Output files follow naming convention and are valid OAS
5. **CSV Integrity**: CSV index matches exact column order, RFC 4180 compliant
6. **Exit Codes**: Correct exit codes for all error scenarios
7. **Version Conversion**: Unconvertible structures fail fast with guidance
8. **Help Messages**: --help shows comprehensive usage information

---

## Summary

This CLI interface provides:
- **Black-box UX**: No code or technical details exposed to users
- **Explicit paths**: No automatic file discovery; users provide exact paths
- **Clear errors**: All errors have plain-language descriptions and actionable guidance
- **Real-time feedback**: Progress indicators during batch operations
- **Deterministic behavior**: Same inputs always produce same outputs
- **Version awareness**: Auto-detects input version, allows explicit output version selection
- **CSV tracking**: Real-time index of all sliced resources

Next step: Create `quickstart.md` for non-programmer users.
