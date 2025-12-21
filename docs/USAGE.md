# Usage Guide

This guide explains how to use the OAS Slicer tool to extract individual API endpoints from OpenAPI specification files.

## Quick Start

### Extract a Single Endpoint

To extract a single endpoint from your API specification:

```bash
slice-oas /path/to/your/api.yaml --path /users --method GET --output ./output/
```

This creates a standalone file containing just the `/users` GET endpoint with all its dependencies.

### Extract All Endpoints

To extract all endpoints from your specification:

```bash
slice-oas /path/to/your/api.yaml --batch --output ./output/
```

This creates individual files for each endpoint in your API.

### Filter Endpoints

Extract only endpoints matching a pattern:

```bash
# Extract all user-related endpoints
slice-oas /path/to/your/api.yaml --batch --filter "/users*" --output ./output/

# Extract endpoints matching a regex pattern
slice-oas /path/to/your/api.yaml --batch --filter "^/api/v[12]/" --filter-type regex --output ./output/
```

## Common Tasks

### Converting Between OpenAPI Versions

Convert endpoints from OpenAPI 3.0 to 3.1 format:

```bash
slice-oas /path/to/api-30.yaml --batch --convert-version 3.1 --output ./output/
```

Or convert from 3.1 to 3.0:

```bash
slice-oas /path/to/api-31.yaml --batch --convert-version 3.0 --output ./output/
```

### Generating a Resource Index

By default, batch extraction creates a CSV index of all extracted resources:

```bash
slice-oas /path/to/api.yaml --batch --output ./output/
# Creates: ./output/sliced-resources-index.csv
```

To disable the CSV index:

```bash
slice-oas /path/to/api.yaml --batch --no-csv --output ./output/
```

### Preview Before Extraction

See what would be extracted without creating files:

```bash
slice-oas /path/to/api.yaml --batch --dry-run
```

## Output Options

### Output Format

Choose between YAML (default) or JSON output:

```bash
# YAML output (default)
slice-oas /path/to/api.yaml --batch --format yaml --output ./output/

# JSON output
slice-oas /path/to/api.yaml --batch --format json --output ./output/
```

### Output Version

Specify the OpenAPI version for output files:

```bash
# Match input version (default)
slice-oas /path/to/api.yaml --batch --version auto --output ./output/

# Force 3.0 output
slice-oas /path/to/api.yaml --batch --version 3.0 --output ./output/

# Force 3.1 output
slice-oas /path/to/api.yaml --batch --version 3.1 --output ./output/
```

## Understanding the Output

### Individual Endpoint Files

Each extracted file is a complete, valid OpenAPI specification containing:

- The single endpoint (path + method)
- All 8 component types resolved: schemas, parameters, headers, responses, requestBodies, securitySchemes, links, and callbacks
- All transitive dependencies (nested references across component types)
- Security scheme definitions if required
- Server information from the original spec

### CSV Index File

The CSV index contains metadata about each extracted resource:

| Column | Description |
|--------|-------------|
| path | The API path (e.g., `/users/{id}`) |
| method | HTTP method (GET, POST, etc.) |
| summary | Brief description of the endpoint |
| description | Detailed description |
| operation_id | Unique operation identifier |
| tags | Comma-separated list of tags |
| filename | Output file name |
| file_size_kb | File size in kilobytes |
| schema_count | Number of schemas included |
| parameter_count | Number of parameters |
| response_codes | Comma-separated response codes |
| security_required | Whether authentication is required |
| deprecated | Whether the endpoint is deprecated |
| created_at | Extraction timestamp |
| output_oas_version | OpenAPI version of output file |

## Performance Tips

### Large Specifications

For specifications with many endpoints:

1. **Use filtering** to extract only what you need:
   ```bash
   slice-oas large-api.yaml --batch --filter "/api/v2/*" --output ./v2-endpoints/
   ```

2. **Increase concurrency** for faster processing:
   ```bash
   slice-oas large-api.yaml --batch --concurrency 8 --output ./output/
   ```

3. **Use dry-run first** to verify the extraction scope:
   ```bash
   slice-oas large-api.yaml --batch --filter "/users*" --dry-run
   ```

### Expected Performance

- Single endpoint extraction: under 5 seconds
- 100 endpoints: under 3 minutes
- 1000 endpoints: scales linearly with parallelism

## Error Handling

### Common Issues

**File not found:**
Check that the input file path is correct and the file exists.

**Invalid format:**
Ensure your input file is a valid OpenAPI specification file.

**Missing dependencies:**
If an endpoint references components that don't exist, the extraction will fail with a helpful message.

**Version conversion issues:**
Some constructs in OpenAPI 3.1 cannot be converted to 3.0 (e.g., webhooks). Use `--strict` mode to fail fast on unconvertible structures.

### Getting Help

For additional help:

```bash
slice-oas --help
```

## Examples

### Extract User Management Endpoints

```bash
# Create a directory for user endpoints
mkdir -p ./user-endpoints

# Extract all user-related endpoints
slice-oas api.yaml --batch --filter "/users*" --output ./user-endpoints/

# Check the results
ls ./user-endpoints/
cat ./user-endpoints/sliced-resources-index.csv
```

### Prepare Endpoints for Different Environments

```bash
# Extract as 3.0 for legacy systems
slice-oas api.yaml --batch --version 3.0 --output ./legacy/

# Extract as 3.1 for modern systems
slice-oas api.yaml --batch --version 3.1 --output ./modern/
```

### Create Documentation-Ready Files

```bash
# Extract with JSON format for documentation tools
slice-oas api.yaml --batch --format json --output ./docs/api-specs/
```
