# Quick Start Guide: slice-oas-by-resource

**Audience**: Non-programmers, technical writers, API architects, DevOps engineers
**Goal**: Extract individual API endpoints from OpenAPI specifications in 5 minutes

---

## What This Tool Does

The slice-oas-by-resource tool takes a large OpenAPI specification file and breaks it into smaller, individual files—one for each API endpoint. Each output file is a complete, standalone OpenAPI specification that can be used independently.

**Use Cases**:
- Share a single endpoint with external partners without exposing your full API
- Create focused documentation for specific endpoints
- Organize large API specifications into manageable pieces
- Convert endpoints between OpenAPI 3.0 and 3.1 formats

---

## Installation

**Step 1**: Make sure you have Python 3.11 or newer installed.

To check your Python version, open a terminal and run:
```bash
python --version
```

You should see something like `Python 3.11.0` or higher.

**Step 2**: Install the tool using pip:
```bash
pip install slice-oas
```

**Step 3**: Verify the installation:
```bash
python -m slice_oas --help
```

You should see help information about available commands.

---

## Before You Start

### What You Need

1. **Your OpenAPI file**: The complete path to your OpenAPI specification file
   - Example: `/home/user/documents/api.yaml`
   - Format: YAML or JSON
   - Version: OpenAPI 3.0.x or 3.1.x

2. **An output folder**: Where you want the extracted files to go
   - Example: `/home/user/output`
   - The folder should exist or you should have permission to create files in its parent folder

3. **The endpoint you want to extract** (for single extraction)
   - Example: `/users/{id}` with method `GET`

### Finding Your OpenAPI File Path

**On Mac/Linux**:
1. Open your file browser
2. Find the OpenAPI file
3. Right-click and select "Copy Path" or "Get Info"
4. The path should look like: `/Users/yourname/Documents/api.yaml`

**On Windows**:
1. Open File Explorer
2. Find the OpenAPI file
3. Shift + Right-click and select "Copy as path"
4. The path should look like: `C:\Users\yourname\Documents\api.yaml`

---

## Your First Extraction: Single Endpoint

Let's extract one endpoint from your OpenAPI file.

### Example: Extracting GET /users/{id}

**Step 1**: Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux)

**Step 2**: Run this command (replace the paths with your actual paths):

```bash
python -m slice_oas extract \
  --input /home/user/documents/api.yaml \
  --output-dir /home/user/output \
  --resource "/users/{id}:GET"
```

**What this command does**:
- `extract` - tells the tool to extract a single endpoint
- `--input` - path to your OpenAPI file
- `--output-dir` - where to save the extracted file
- `--resource` - which endpoint to extract (path + method)

**Step 3**: Check the results

If successful, you'll see something like:
```
Successfully extracted GET /users/{id}

Output file: /home/user/output/users-id-get.yaml
File size: 12.3 KB
OpenAPI version: 3.0.3
Schemas included: 5
Parameters: 1
Response codes: 200, 404

The endpoint has been saved and added to the tracking index.
```

**Step 4**: Open the output file

Navigate to `/home/user/output` and you'll find:
- `users-id-get.yaml` - Your extracted endpoint
- `sliced-resources-index.csv` - A tracking file (explained below)

---

## Extracting All Endpoints (Batch Mode)

Want to extract every endpoint from your OpenAPI file? Use batch mode.

### Example: Extract Everything

```bash
python -m slice_oas batch \
  --input /home/user/documents/api.yaml \
  --output-dir /home/user/output
```

You'll see real-time progress:
```
Starting batch extraction from /home/user/documents/api.yaml

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
Output directory: /home/user/output
```

### Example: Extract Only Specific Endpoints

Use the `--filter` option to extract only endpoints matching a pattern:

```bash
python -m slice_oas batch \
  --input /home/user/documents/api.yaml \
  --output-dir /home/user/output \
  --filter "/users/*"
```

This extracts only endpoints that start with `/users/`, like:
- `/users` (all methods)
- `/users/{id}` (all methods)
- `/users/{id}/orders` (all methods)

---

## Choosing Output Format and Version

### Output Format (JSON or YAML)

By default, the output format matches your input file. You can change it:

**Convert YAML to JSON**:
```bash
python -m slice_oas extract \
  --input /home/user/documents/api.yaml \
  --output-dir /home/user/output \
  --resource "/users:GET" \
  --format json
```

**Convert JSON to YAML**:
```bash
python -m slice_oas extract \
  --input /home/user/documents/api.json \
  --output-dir /home/user/output \
  --resource "/users:GET" \
  --format yaml
```

### OpenAPI Version Conversion

Your input file might be OpenAPI 3.0.x or 3.1.x. You can convert between versions:

**Convert 3.0 to 3.1**:
```bash
python -m slice_oas extract \
  --input /home/user/documents/api-3.0.yaml \
  --output-dir /home/user/output \
  --resource "/users:GET" \
  --output-version 3.1
```

**Convert 3.1 to 3.0**:
```bash
python -m slice_oas extract \
  --input /home/user/documents/api-3.1.yaml \
  --output-dir /home/user/output \
  --resource "/users:GET" \
  --output-version 3.0
```

**Important**: Some features in OpenAPI 3.1 cannot be converted to 3.0. If conversion isn't possible, you'll see a clear error message explaining why and suggesting to use 3.1 format instead.

---

## Understanding the Tracking Index (CSV File)

Every time you extract endpoints, a file called `sliced-resources-index.csv` is created in your output directory. This file tracks all your extracted endpoints.

### What's in the CSV?

Open the CSV in Excel, Google Sheets, or any spreadsheet program. You'll see:

| Column | What It Means |
|--------|---------------|
| path | The API endpoint path (e.g., `/users/{id}`) |
| method | HTTP method (GET, POST, etc.) |
| summary | Short description of the endpoint |
| operationId | Unique identifier (if defined in your API) |
| tags | Categories this endpoint belongs to |
| filename | Name of the extracted file |
| file_size_kb | Size of the output file |
| schema_count | How many data schemas are included |
| parameter_count | How many parameters the endpoint accepts |
| response_codes | HTTP status codes this endpoint can return |
| security_required | Whether authentication is needed |
| deprecated | Whether this endpoint is marked as deprecated |
| created_at | When the extraction happened |
| output_oas_version | Which OpenAPI version was used |

### Why Is This Useful?

- **Inventory**: See all your extracted endpoints in one place
- **Search**: Filter by tags, methods, or response codes
- **Track Changes**: See when endpoints were last extracted
- **Documentation**: Use as a table of contents for your API docs

---

## Listing Available Endpoints

Not sure what endpoints are in your OpenAPI file? Use the `list` command:

```bash
python -m slice_oas list --input /home/user/documents/api.yaml
```

Output:
```
Endpoints in /home/user/documents/api.yaml (OpenAPI 3.0.3):

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

This helps you:
- See all available endpoints before extracting
- Find the exact path format to use in extraction commands
- Check which methods are available for each path

---

## Checking Version Compatibility

Want to know if your file can be converted between OpenAPI versions? Use the `version-info` command:

```bash
python -m slice_oas version-info --input /home/user/documents/api.yaml
```

Output:
```
OpenAPI Specification: /home/user/documents/api.yaml

Detected version: 3.0.3
Format: YAML
File size: 456.2 KB
Total endpoints: 45

Conversion compatibility:
  ✓ Can convert to OpenAPI 3.1.x
  ✓ Can remain in OpenAPI 3.0.x

No conversion blockers detected.
```

If conversion isn't possible, you'll see why:
```
Conversion compatibility:
  ✗ Cannot convert to OpenAPI 3.0.x

Blockers:
  - Uses JSON Schema 'if/then/else' conditionals (3 endpoints)
  - Uses multi-type unions (5 endpoints)

Recommendation: Keep as OpenAPI 3.1.x format for full compatibility.
```

---

## Common Questions

### Q: What format should I use for the `--resource` argument?

**A**: Use the exact path from your OpenAPI file, followed by a colon, then the HTTP method.

**Examples**:
- `/users/{id}:GET`
- `/api/v1/products:POST`
- `/health:get` (method can be lowercase)

**Wrong**:
- `users/{id}:GET` (missing leading slash)
- `/users/{id}` (missing method)
- `/users/{id} GET` (no colon separator)

### Q: What if my output file already exists?

**A**: The tool creates a new version with a number: `users-get-1.yaml`, `users-get-2.yaml`, etc. Your original file is never overwritten.

### Q: Can I extract endpoints from Swagger 2.0 files?

**A**: No, this tool only supports OpenAPI 3.0.x and 3.1.x. You'll need to convert your Swagger 2.0 file to OpenAPI 3.x first using a different tool.

### Q: What if I get an error message?

**A**: All error messages are designed to be clear and actionable. Read the message carefully—it will tell you what went wrong and what to do next.

**Common errors**:
- File path doesn't exist → Check your path is correct and complete
- Path not found in file → Use `list` command to see available paths
- Permission denied → Make sure you can read the input file and write to the output directory
- Cannot convert version → Use `version-info` to see why, then choose a compatible version

### Q: How do I know if extraction was successful?

**A**: You'll see a success message with file details. Also, check:
1. The output file exists in your output directory
2. The CSV index has a new row for the extracted endpoint
3. The command exits with code 0 (no error)

### Q: What happens to references in my OpenAPI file?

**A**: The tool automatically includes all necessary components (schemas, parameters, security definitions) so the extracted file is completely standalone. You don't need to worry about broken references.

### Q: Can I extract multiple specific endpoints without using batch mode?

**A**: Yes, run the `extract` command multiple times with different `--resource` arguments. Each extraction is independent.

---

## Troubleshooting

### Error: "The file path you provided doesn't exist"

**Cause**: The path to your OpenAPI file is incorrect or the file has been moved.

**Solution**:
1. Double-check the file path
2. Make sure you're using the complete, absolute path
3. On Windows, use forward slashes `/` instead of backslashes `\`, or escape backslashes: `C:\\Users\\...`

### Error: "You don't have permission to read this file"

**Cause**: The file is protected or owned by another user.

**Solution**:
1. Check file permissions
2. Try copying the file to a location you own (like your Documents folder)
3. On Mac/Linux, you might need to change ownership: `sudo chown $USER file.yaml`

### Error: "This doesn't appear to be an OpenAPI specification file"

**Cause**: The file is not a valid OpenAPI file or is corrupted.

**Solution**:
1. Open the file in a text editor and verify it has an `openapi` field at the top
2. Check that the file is valid YAML or JSON (use an online validator)
3. Verify the file isn't empty or corrupted

### Error: "The path '/users' exists, but it doesn't have a GET operation"

**Cause**: You specified a method that doesn't exist for that path.

**Solution**:
1. Use the `list` command to see which methods are available
2. Update your `--resource` argument with the correct method

### Batch extraction is slow

**Expected**: Batch extraction processes each endpoint individually and validates thoroughly. For 100 endpoints, expect 2-3 minutes.

**Tips**:
- Use `--filter` to extract only the endpoints you need
- Make sure you're not running on a slow network drive
- Large files (>1MB) take longer to process

---

## Advanced Usage (Optional)

### Using a Configuration File

Create a file called `.slice-oas-config.yaml` in your home directory:

```yaml
defaults:
  format: yaml
  output_version: auto
  csv_index_name: sliced-resources-index.csv

validation:
  strict: true
  max_depth: 100

output:
  overwrite: false
  include_source_comment: true
```

Then set the environment variable:
```bash
export SLICE_OAS_CONFIG=/home/user/.slice-oas-config.yaml
```

Now all your extractions will use these defaults unless you override them with command-line arguments.

### Debug Mode

If you're comfortable with technical details, add `--debug` to any command to see more information:

```bash
python -m slice_oas extract \
  --input /home/user/documents/api.yaml \
  --output-dir /home/user/output \
  --resource "/users:GET" \
  --debug
```

Debug mode shows:
- Validation phase details
- Technical error messages
- Stack traces if something goes wrong

---

## Next Steps

### Successfully Extracted Endpoints?

Now you can:
1. **Share**: Send individual endpoint files to partners or developers
2. **Document**: Use extracted files to generate focused API documentation
3. **Version Control**: Track changes to specific endpoints over time
4. **Test**: Use extracted files with API testing tools like Postman or Swagger UI
5. **Convert**: Share OpenAPI 3.0 files with teams that need 3.1, or vice versa

### Want to Learn More?

- Read the full CLI reference: See `contracts/cli-interface.md` in the project repository
- Understand version conversion: See `docs/VERSION_CONVERSION.md`
- Learn about validation phases: See `docs/VALIDATION_PHASES.md`

---

## Getting Help

### Command-Line Help

```bash
python -m slice_oas --help               # General help
python -m slice_oas extract --help       # Help for extract command
python -m slice_oas batch --help         # Help for batch command
python -m slice_oas list --help          # Help for list command
```

### Still Stuck?

If you encounter an error you don't understand:
1. Read the error message carefully—it includes guidance on what to do
2. Try the `--debug` flag to see technical details
3. Check that your OpenAPI file is valid using an online validator
4. Make sure you're using Python 3.11 or newer

---

## Summary: Common Commands

**Extract a single endpoint**:
```bash
python -m slice_oas extract --input /path/to/api.yaml --output-dir /output --resource "/users:GET"
```

**Extract all endpoints**:
```bash
python -m slice_oas batch --input /path/to/api.yaml --output-dir /output
```

**Extract endpoints matching a pattern**:
```bash
python -m slice_oas batch --input /path/to/api.yaml --output-dir /output --filter "/users/*"
```

**List available endpoints**:
```bash
python -m slice_oas list --input /path/to/api.yaml
```

**Check version compatibility**:
```bash
python -m slice_oas version-info --input /path/to/api.yaml
```

**Convert format and version**:
```bash
python -m slice_oas extract --input /path/to/api.yaml --output-dir /output --resource "/users:GET" --format json --output-version 3.1
```

---

**You're ready to start slicing OpenAPI specifications!**

Begin with a single endpoint extraction to get familiar with the tool, then move to batch mode when you're comfortable.
