# Slice OAS by Resource

Decompose large OpenAPI specifications into individual, self-contained OAS files—one for each path and HTTP method combination.

## Overview

This tool enables API teams to extract individual endpoints from large OpenAPI specifications while maintaining complete fidelity with the parent specification. Each extracted file is a valid, standalone OpenAPI document that can be immediately used by downstream tools.

## Features

- **Single Endpoint Extraction**: Extract a single API endpoint with all dependencies resolved
- **Batch Processing**: Process 100+ endpoints efficiently (under 3 minutes)
- **Version Conversion**: Bidirectional conversion between OpenAPI 3.0.x and 3.1.x
- **CSV Indexing**: Generate searchable, traceable CSV index of all sliced resources
- **7-Phase Validation**: Every extracted endpoint passes comprehensive validation
- **Black-Box UX**: Non-technical users can complete the entire workflow without seeing code or technical details

## Installation

Using Poetry (recommended):

```bash
poetry install
```

Or using pip:

```bash
pip install slice-oas
```

## Quick Start

### Extract a Single Endpoint

```bash
slice-oas api.yaml --path /users/{id} --method GET --output ./sliced/
```

### Batch Extract All Endpoints

```bash
slice-oas api.yaml --batch --output ./sliced/
```

### Filter by Pattern

```bash
# Extract only user endpoints
slice-oas api.yaml --batch --filter "/users*" --output ./sliced/

# Extract with regex pattern
slice-oas api.yaml --batch --filter "^/api/v[12]/" --filter-type regex --output ./sliced/
```

### Convert Between Versions

```bash
# Convert 3.0 to 3.1
slice-oas api-30.yaml --batch --convert-version 3.1 --output ./sliced/

# Convert 3.1 to 3.0
slice-oas api-31.yaml --batch --convert-version 3.0 --output ./sliced/
```

## Output

### Individual Endpoint Files

Each extracted file contains:
- The single endpoint (path + method)
- All referenced components (schemas, parameters, headers)
- All transitive dependencies
- Security scheme definitions (if required)

### CSV Index

Batch extraction creates a CSV index (`sliced-resources-index.csv`) with:
- Endpoint path and method
- Summary and description
- Operation ID and tags
- File size and schema count
- Security requirements
- Deprecation status
- Output OpenAPI version

## Performance

| Operation | Target | Typical |
|-----------|--------|---------|
| Single extraction | < 5 seconds | ~1 second |
| 100 endpoints | < 3 minutes | ~45 seconds |
| 1000 endpoints | Scales linearly | ~7 minutes |

## Validation

Every extracted endpoint passes 7 validation phases:

1. **File Structure**: Valid OpenAPI document structure
2. **Operation Integrity**: Complete endpoint definition
3. **Response Integrity**: Valid response definitions
4. **Reference Resolution**: All $ref pointers resolved
5. **Component Completeness**: All dependencies included
6. **Payload Equivalence**: Extraction matches original
7. **Version Validation**: Conforms to target version

## Documentation

- [Usage Guide](docs/USAGE.md) - Detailed usage instructions
- [Version Conversion](docs/VERSION_CONVERSION.md) - 3.0/3.1 conversion details
- [Validation Phases](docs/VALIDATION_PHASES.md) - Validation process explained

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output directory | Required |
| `--path` | Endpoint path (single mode) | - |
| `--method` | HTTP method (single mode) | - |
| `--batch` | Extract all endpoints | `false` |
| `--filter` | Filter pattern (glob or regex) | - |
| `--filter-type` | Filter type: `glob` or `regex` | `glob` |
| `--format` | Output format: `yaml` or `json` | `yaml` |
| `--version` | Output version: `auto`, `3.0`, `3.1` | `auto` |
| `--convert-version` | Convert to version: `3.0`, `3.1` | - |
| `--concurrency` | Parallel workers | `4` |
| `--no-csv` | Disable CSV generation | `false` |
| `--dry-run` | Preview without writing | `false` |
| `--strict` | Fail on conversion issues | `false` |

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/jamil/slice-oas-by-resource.git
cd slice-oas-by-resource

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=slice_oas --cov-report=html

# Run specific test file
poetry run pytest tests/integration/test_e2e_workflow.py

# Run slow tests (large file handling)
poetry run pytest -m slow
```

### Project Structure

```
slice-oas-by-resource/
├── src/slice_oas/          # Main package
│   ├── cli.py              # Command-line interface
│   ├── parser.py           # OAS file parsing
│   ├── slicer.py           # Endpoint extraction
│   ├── resolver.py         # Reference resolution
│   ├── validator.py        # 7-phase validation
│   ├── converter.py        # Version conversion
│   ├── generator.py        # Output generation
│   ├── batch_processor.py  # Batch processing
│   ├── csv_manager.py      # CSV index management
│   └── models.py           # Data models
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test fixtures
├── docs/                   # Documentation
└── pyproject.toml          # Project configuration
```

## Requirements

- Python 3.11+
- Dependencies:
  - pydantic-core
  - PyYAML
  - openapi-spec-validator
  - jsonschema

## License

MIT

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## Status

Production-ready with 150+ comprehensive tests covering:
- Single endpoint extraction
- Batch processing with filtering
- Version conversion (3.0 ↔ 3.1)
- CSV index generation
- Black-box UX validation
- Edge cases and error handling
