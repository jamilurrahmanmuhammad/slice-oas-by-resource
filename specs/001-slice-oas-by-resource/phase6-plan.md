# Implementation Plan: Phase 6 - CSV Index Generation for API Governance (US4)

**Branch**: `001-slice-oas-by-resource` | **Date**: 2025-12-18 | **Spec**: [spec.md](./spec.md)

**Input**: User Story 4 (CSV Index Generation) - Generate searchable, traceable CSV index of all sliced resources with governance metadata

---

## Summary

Phase 6 completes the API Governance story by fully integrating the existing `CSVIndexManager` into the batch extraction pipeline. Technical writers and governance teams need a comprehensive CSV index tracking all API endpoints for documentation, tracking, and bulk operations. The CSV manager implementation exists (`csv_manager.py`) but is not connected to the extraction pipeline.

**Technical Approach**: Wire `CSVIndexManager` into `BatchProcessor`, add real-time entry creation after each successful extraction, implement duplicate detection, and ensure RFC 4180 compliance for spreadsheet compatibility. Add comprehensive tests for CSV functionality.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pydantic, PyYAML, csv module (stdlib), threading (stdlib)
**Storage**: File-based (`{output_directory}/sliced-resources-index.csv`)
**Testing**: pytest with integration tests (TDD approach)
**Target Platform**: Linux/macOS/Windows (CLI tool)
**Project Type**: Single-purpose CLI tool (extends Phase 4-5)
**Performance Goals**: Real-time CSV updates, <10ms per entry append
**Constraints**: Thread-safe writes, RFC 4180 compliance, no data loss
**Scale/Scope**: Support 1000+ entries per CSV, append mode for sessions

**Existing Implementation Status**:
- `CSVIndexManager` class in `csv_manager.py` - COMPLETE (thread-safe, headers match constitution)
- `CSVIndexEntry` model in `models.py` - COMPLETE (15 columns, `to_csv_row()` method)
- `create_csv_index_entry()` factory - COMPLETE
- Integration with BatchProcessor - **NOT DONE** (Phase 6 focus)
- Duplicate detection - **NOT DONE** (Phase 6 focus)
- Append mode for existing files - **NOT DONE** (Phase 6 focus)
- Comprehensive tests - **PARTIAL** (basic test exists, needs expansion)

---

## Constitution Check

✅ **I. Black Box Abstraction** - CSV is created silently; users see only "CSV index created at {path}" message. No internal CSV formatting, column details, or file structure exposed.

✅ **II. Explicit Path Input** - CSV location is `{output_directory}/sliced-resources-index.csv` - derived from user-specified output directory. No auto-discovery.

✅ **III. Complete Reference Resolution** - CSV entries include `schema_count`, `parameter_count` - metrics derived from resolved references. No impact on reference resolution itself.

✅ **IV. Deterministic Validation** - Only successfully validated endpoints are added to CSV. Failed extractions are NOT added. CSV entries are deterministic (same input → same output).

✅ **V. CSV Indexing** - **PRIMARY FOCUS** - All requirements from Principle V must be fully implemented:
- Location: `{output_directory}/sliced-resources-index.csv`
- Exact column order: path | method | summary | description | operationId | tags | filename | file_size_kb | schema_count | parameter_count | response_codes | security_required | deprecated | created_at | output_oas_version
- Created on first resource sliced
- Updated in real-time after each successful slice
- Append mode (preserve previous rows)
- No duplicates (path+method combination)
- Failed resources NOT added

---

## Architecture Overview

### Data Flow

```
Batch Extraction Pipeline (Phase 4-5)
    ↓
[After Each Successful Extraction]
    ↓
[Create CSVIndexEntry] → Factory function
    ├─ Extract metadata from operation
    ├─ Calculate file_size_kb from output
    ├─ Count schemas, parameters
    ├─ Parse response codes
    └─ Check security/deprecation status
    ↓
[CSVIndexManager.append_entry()] → Thread-safe append
    ├─ Duplicate check (path+method)
    ├─ RFC 4180 escaping
    └─ Atomic file append
    ↓
[CSV Updated] → Real-time tracking
```

### Key Components

1. **CSVIndexManager** (`csv_manager.py` - EXISTS, needs enhancement)
   - Thread-safe append operations (EXISTS)
   - Duplicate detection (NEW)
   - Append mode for existing files (NEW)
   - Entry count tracking (NEW)

2. **CSVIndexEntry** (`models.py` - COMPLETE)
   - 15-column Pydantic model
   - `to_csv_row()` method with RFC 4180 escaping

3. **BatchProcessor Integration** (`batch_processor.py` - NEW INTEGRATION)
   - Create CSVIndexManager on batch start
   - Call `append_entry()` after each successful extraction
   - Track CSV path in BatchExtractionResult
   - Report CSV summary in completion message

4. **CLI Integration** (`cli.py` - EXTEND)
   - Add `--no-csv` flag to disable CSV generation
   - Report CSV path in batch summary
   - Show entry count in summary

---

## Implementation Details

### CSV Column Specification (Constitution Compliance)

| Column | Source | Format | Example |
|--------|--------|--------|---------|
| path | operation.path | string | /users/{id} |
| method | operation.method | uppercase | GET |
| summary | operation.summary | string or empty | Get user by ID |
| description | operation.description | string or empty | Retrieves user... |
| operationId | operation.operationId | string or empty | getUserById |
| tags | operation.tags | comma-separated | users,admin |
| filename | generated | sanitized | users-id_GET.yaml |
| file_size_kb | calculated | float 2dp | 4.23 |
| schema_count | calculated | integer | 5 |
| parameter_count | calculated | integer | 3 |
| response_codes | parsed | comma-separated | 200,400,404 |
| security_required | boolean | yes/no | yes |
| deprecated | boolean | yes/no | no |
| created_at | timestamp | ISO 8601 | 2025-12-18T10:30:00Z |
| output_oas_version | version | family | 3.1.x |

### Duplicate Detection Strategy

```python
def has_duplicate(self, path: str, method: str) -> bool:
    """Check if path+method already exists in CSV.

    Performance: O(n) scan, acceptable for <10k entries.
    For larger scale: consider in-memory set or SQLite index.
    """
    if not self.csv_path.exists():
        return False

    with open(self.csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['path'] == path and row['method'] == method:
                return True
    return False
```

### Append Mode Strategy

```python
def initialize(self, append_mode: bool = False) -> None:
    """Create CSV file with headers.

    Args:
        append_mode: If True, don't overwrite existing file with headers
    """
    with self.lock:
        if self._initialized:
            return

        # Append mode: check if file exists and has headers
        if append_mode and self.csv_path.exists():
            # Validate existing headers match
            with open(self.csv_path, 'r', newline='') as f:
                reader = csv.reader(f)
                existing_headers = next(reader, None)
                if existing_headers == self.HEADERS:
                    self._initialized = True
                    return

        # Create new file with headers
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)

        self._initialized = True
```

### RFC 4180 Compliance

The existing `CSVIndexEntry.to_csv_row()` handles escaping:
- Escape quotes: `"` → `""`
- Wrap values containing commas, quotes, or newlines in double quotes
- Python's `csv.writer` with default dialect provides RFC 4180 compliance

### Metadata Extraction Functions

```python
def extract_csv_metadata(
    doc: Dict[str, Any],
    path: str,
    method: str,
    output_path: Path,
    output_version: str
) -> Dict[str, Any]:
    """Extract all metadata needed for CSV entry.

    Returns dict with all 15 columns populated.
    """
    operation = doc.get('paths', {}).get(path, {}).get(method.lower(), {})

    return {
        'path': path,
        'method': method.upper(),
        'summary': operation.get('summary', ''),
        'description': operation.get('description', ''),
        'operation_id': operation.get('operationId', ''),
        'tags': ','.join(operation.get('tags', [])),
        'filename': output_path.name,
        'file_size_kb': round(output_path.stat().st_size / 1024, 2),
        'schema_count': count_schemas(doc),
        'parameter_count': count_parameters(doc, path, method),
        'response_codes': ','.join(sorted(operation.get('responses', {}).keys())),
        'security_required': has_security_requirement(operation, doc),
        'deprecated': operation.get('deprecated', False),
        'output_oas_version': output_version,
    }
```

---

## Project Structure

### Files to Modify

```text
src/slice_oas/
├── csv_manager.py        # ENHANCE: Add duplicate detection, append mode
├── batch_processor.py    # INTEGRATE: Connect CSVIndexManager
├── cli.py                # EXTEND: Add --no-csv flag, CSV summary
└── models.py             # NO CHANGE: CSVIndexEntry already complete

tests/integration/
├── test_batch_extraction.py  # ENHANCE: TestBatchCSVIndex tests
└── test_csv_generation.py    # NEW: Dedicated CSV tests
```

### New Test File

```text
tests/integration/test_csv_generation.py
├── TestCSVCreation          # T074-T076
├── TestCSVRealTimeUpdates   # T077-T078
├── TestCSVDeduplication     # T079-T080
├── TestCSVRFC4180           # T081-T082
├── TestCSVAppendMode        # T083-T084
└── TestCSVEdgeCases         # T085-T088
```

---

## Acceptance Criteria (from Spec & Constitution)

### FR-022: CSV Generation During Batch Operations
- [x] CSVIndexManager class exists
- [ ] Integration with BatchProcessor
- [ ] CSV created when `generate_csv=True`

### FR-023: CSV Column Specification
- [x] All 15 columns defined in HEADERS
- [x] Column order matches constitution
- [ ] All columns populated correctly from metadata

### FR-024: Real-Time Updates
- [x] Thread-safe append operation
- [ ] Entry added immediately after each successful extraction
- [ ] No batching/buffering of entries

### FR-025: RFC 4180 Compliance
- [x] to_csv_row() handles escaping
- [ ] Test with Excel, Google Sheets
- [ ] Test with special characters (quotes, commas, newlines)

### Constitution Principle V Requirements
- [x] Filename: `sliced-resources-index.csv`
- [x] Column order matches constitution
- [ ] Created on first resource sliced
- [ ] Real-time updates
- [ ] Append mode (preserve previous rows)
- [ ] No duplicates (path+method check)
- [ ] Failed resources NOT added

---

## Task Breakdown (T074-T088)

### Core Implementation (T074-T078)

**T074** [US4] Enhance CSVIndexManager with duplicate detection in `csv_manager.py`
- Add `has_duplicate(path, method)` method
- O(n) scan implementation (acceptable for <10k entries)
- Return True if path+method exists, False otherwise

**T075** [US4] Enhance CSVIndexManager with append mode in `csv_manager.py`
- Modify `initialize()` to support append_mode parameter
- Validate existing headers if file exists
- Preserve existing entries when appending

**T076** [US4] Integrate CSVIndexManager into BatchProcessor in `batch_processor.py`
- Create CSVIndexManager in `process()` when `generate_csv=True`
- Call `append_entry()` after each successful extraction
- Implement `extract_csv_metadata()` helper function
- Set `csv_index_path` in BatchExtractionResult

**T077** [US4] Add metadata extraction utilities in `csv_manager.py`
- Implement `count_schemas(doc)` function
- Implement `count_parameters(doc, path, method)` function
- Implement `has_security_requirement(operation, doc)` function
- Implement `extract_csv_metadata()` factory function

**T078** [US4] Extend CLI with CSV options in `cli.py`
- Add `--no-csv` flag to disable CSV generation
- Add CSV path to batch summary output
- Add entry count to completion message

### Integration Tests (T079-T088)

**T079** [US4] Test CSV creation and basic functionality
- Verify CSV created at correct path
- Verify all 15 columns present in header
- Verify entries added for successful extractions

**T080** [US4] Test real-time CSV updates
- Extract 10 endpoints, verify CSV has 10 entries
- Verify entries appear as processing continues
- Verify order matches extraction order

**T081** [US4] Test duplicate detection
- Run batch twice, verify no duplicate entries
- Test path+method uniqueness
- Verify second run appends new entries only

**T082** [US4] Test RFC 4180 compliance
- Test entries with commas in summary
- Test entries with quotes in description
- Test entries with newlines in description
- Verify CSV opens correctly in Excel/Sheets

**T083** [US4] Test append mode
- Run extraction, verify CSV created
- Run again with new filter, verify entries appended
- Verify original entries preserved

**T084** [US4] Test failed extractions NOT added to CSV
- Trigger extraction failure (invalid path)
- Verify failed endpoint not in CSV
- Verify other endpoints still added

**T085** [US4] Test CSV with large batches
- Extract 100 endpoints, verify all in CSV
- Verify performance (< 1 second for CSV operations)
- Verify file size reasonable

**T086** [US4] Test CSV metadata accuracy
- Verify schema_count correct
- Verify parameter_count correct
- Verify response_codes correct
- Verify security_required correct

**T087** [US4] Test CSV with version conversion
- Extract with version conversion (Phase 5)
- Verify output_oas_version reflects converted version
- Verify all other metadata correct

**T088** [US4] Test --no-csv flag
- Run with --no-csv flag
- Verify no CSV file created
- Verify extraction still works

---

## Dependencies

### Internal Dependencies
- **Phase 4** (Batch Processing): BatchProcessor must be working
- **Phase 5** (Version Conversion): output_oas_version must track converted version

### External Dependencies
- Python `csv` module (stdlib)
- Python `threading` module (stdlib)
- No new dependencies required

---

## Risk Analysis

### Risk 1: Performance with Large CSVs
**Impact**: Slow extraction if CSV grows to 10k+ entries
**Mitigation**: Duplicate detection is O(n); consider in-memory hash set for >1000 entries

### Risk 2: Concurrent Write Corruption
**Impact**: CSV corruption if multiple threads write simultaneously
**Mitigation**: Existing thread lock in CSVIndexManager; test concurrent access

### Risk 3: RFC 4180 Edge Cases
**Impact**: CSV doesn't open correctly in spreadsheet software
**Mitigation**: Comprehensive testing with special characters; use csv.writer defaults

---

## Estimated Effort

- **Core Implementation** (T074-T078): 5 tasks × 30 min = 2.5 hours
- **Integration Tests** (T079-T088): 10 tasks × 20 min = 3.5 hours
- **Total**: ~6 hours with parallel opportunities

---

## Success Metrics

- [ ] CSV created during batch extraction with all 15 columns
- [ ] Real-time updates (entry added after each extraction)
- [ ] No duplicates in CSV (path+method uniqueness)
- [ ] RFC 4180 compliance (opens in Excel, Google Sheets)
- [ ] Append mode preserves existing entries
- [ ] Failed extractions NOT added to CSV
- [ ] All 15 tests passing (T074-T088)
- [ ] Integration with Phase 5 version conversion working
