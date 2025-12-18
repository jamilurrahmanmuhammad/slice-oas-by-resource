# Implementation Plan: Batch Processing for Microservices Deployment (Phase 4 US2)

**Branch**: `001-slice-oas-by-resource` | **Date**: 2025-12-18 | **Spec**: [spec.md](./spec.md)

**Input**: User Story 2 (Batch Slicing for Microservices Deployment) - Extract 100+ endpoints with filter patterns, real-time progress, and CSV tracking

---

## Summary

Phase 4 extends the single endpoint extraction (Phase 3) to batch processing capabilities. DevOps engineers need to decompose monolithic OpenAPI specifications (100+ endpoints) into service-specific OAS files. Key requirements: process all matching endpoints within 3 minutes, support path-based filtering, provide real-time progress updates, generate CSV index with metadata, and guarantee 100% validation pass rate.

**Technical Approach**: Build a batch orchestrator that reuses Phase 3 extraction pipeline, adds multi-endpoint processing loop with progress tracking, implements path-based filtering (prefix/regex patterns), creates streamed CSV index with metadata, and validates all outputs before completion.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pydantic, PyYAML, jsonschema, openapi-spec-validator (existing), concurrent.futures (new)
**Storage**: File-based (input OAS → output directory with multiple files + CSV index)
**Testing**: pytest with integration tests (phase-based)
**Target Platform**: Linux/macOS/Windows (CLI tool)
**Project Type**: Single-purpose CLI tool
**Performance Goals**: Process 100 endpoints < 3 minutes (30 endpoints/min average)
**Constraints**: Memory-efficient (avoid loading all outputs simultaneously), disk I/O optimized, progress updates real-time (not batched)
**Scale/Scope**: Support 100-1000+ endpoints per operation, 50-200MB input files, variable output sizes

**Key Design Considerations**:
1. **Parallel Processing**: Use concurrent.futures.ThreadPoolExecutor for I/O-bound extraction tasks
2. **Progress Tracking**: Real-time reporting via callback mechanism (not verbose output)
3. **CSV Streaming**: Write CSV index line-by-line to support large batch operations
4. **Error Resilience**: Continue processing on per-endpoint failures, report summary at end
5. **Filtering Strategy**: Support both glob patterns and regex for endpoint selection
6. **Output Organization**: Option to organize output by service prefix or keep flat structure

---

## Constitution Check

✅ **I. Black Box Abstraction** - Batch mode shows only progress (X/N extracted), file count, summary stats. No algorithm details, no intermediate steps, no technical error traces for failed endpoints (just counts).

✅ **II. Explicit Path Input** - Batch mode still requires explicit: input file path, output directory, filter pattern, target version. No auto-discovery of input files.

✅ **III. Complete Reference Resolution** - Every extracted endpoint must have all transitive refs resolved. Batch processing doesn't change reference resolution quality—same 7-phase validation applies to each file.

✅ **IV. Deterministic Validation** - Every endpoint extracted in batch must pass all 7 validation phases. Failed validations don't produce output files. Summary includes: total processed, successful, failed, validation pass rate.

✅ **Constitutional Requirement**: Real-time CSV index updates ensure governance teams can track progress. Version fidelity maintained across batch (output version applies uniformly to all extracted endpoints).

---

## Architecture Overview

### Data Flow

```
Input OAS File
    ↓
[Batch Filter]  → Path matching (glob/regex)
    ↓
[Endpoint Queue]  → List of (path, method) tuples
    ↓
[Thread Pool]     → Parallel extraction (configurable concurrency)
    ├─ Extract endpoint (slicer.py)
    ├─ Resolve references (resolver.py)
    ├─ Validate 7 phases (validator.py)
    └─ Generate output (generator.py)
    ↓
[CSV Streamer]  → Real-time index update
    ↓
[Output Directory]
    ├─ endpoint1_GET.yaml
    ├─ endpoint2_POST.yaml
    ├─ endpoint3_PUT.yaml
    └─ index.csv  ← Updated in real-time
    ↓
Success Summary
```

### Key Components

1. **Batch Orchestrator** (`batch_processor.py`)
   - Loads OAS, extracts all paths
   - Applies filter pattern (glob or regex)
   - Creates thread pool with configurable concurrency (default: 4 workers)
   - Tracks progress (extracted, failed, total)
   - Handles thread-safe CSV index writing

2. **Endpoint Filter** (`filters.py`)
   - Support path prefix patterns: `/users/*`, `/products/*`
   - Support regex patterns: `^/api/v\d+/.*`
   - Support method-based filtering: GET-only, POST-only, etc.
   - Return filtered (path, method) tuples

3. **CSV Index Manager** (`csv_manager.py`)
   - Real-time streaming writes (append mode, no locking)
   - Headers: path, method, summary, operation_id, tags, filename, file_size_kb, schema_count, parameter_count, response_codes, security_required, deprecated, created_at, output_oas_version, validation_status
   - Thread-safe appending with file locks
   - Metadata auto-populated from extracted endpoint

4. **Progress Reporter** (`progress.py`)
   - Callback-based progress reporting
   - Format: "Extracting endpoint 45/100 (45%)" or "✓ 45 extracted, 2 failed"
   - Real-time updates without verbose output
   - Summary at completion: extracted count, failed count, validation pass rate, total time

5. **Output Manager** (`output_manager.py`)
   - Deterministic filename generation: `{path}_{METHOD}.{format}`
   - Path sanitization: `/users/{id}` → `users-id_GET.yaml`
   - Directory creation and validation
   - File write with atomic operations (write to temp, then rename)

### Error Handling Strategy

- **Per-endpoint failures**: Log to summary (count only), continue processing
- **Missing paths**: Skip endpoint, increment failed counter
- **Validation failures**: Don't write output file, log to validation report
- **I/O errors**: Retry once, then skip with warning
- **Summary report**: List failed endpoints at completion, provide recovery instructions

---

## Interface Design

### CLI Arguments (Extension to existing `--batch` mode)

```bash
slice-oas \
  --input large-api.yaml \
  --output-dir ./microservices \
  --output-version 3.1.x \
  --batch \
  --filter "/users/*" \
  --concurrency 4 \
  --format yaml
```

**New arguments**:
- `--filter PATTERN`: Path pattern (glob or regex) for endpoint selection
- `--concurrency N`: Number of parallel extraction threads (default: 4, max: 16)
- `--format FORMAT`: Output format (yaml or json, applies to all extracted files)
- `--no-csv`: Skip CSV index generation (default: create index.csv)
- `--dry-run`: Show what would be extracted without writing files

**Output structure**:
```
microservices/
├── users-id_GET.yaml
├── users_POST.yaml
├── products-id_GET.yaml
├── products_PUT.yaml
├── products_DELETE.yaml
└── index.csv
```

### CSV Index Format

```csv
path,method,summary,operation_id,tags,filename,file_size_kb,schema_count,parameter_count,response_codes,security_required,deprecated,created_at,output_oas_version,validation_status
"/users/{id}",GET,"Get user by ID",getUserById,"users,public",users-id_GET.yaml,3.2,1,1,"200,404",false,false,2025-12-18T14:30:45Z,3.1.x,PASS
"/users",POST,"Create user",createUser,"users,admin",users_POST.yaml,4.1,1,0,"201,400,409",true,false,2025-12-18T14:30:46Z,3.1.x,PASS
```

---

## Data Models

### BatchExtractionRequest

```python
@dataclass
class BatchExtractionRequest:
    input_file: Path          # OAS file path
    output_dir: Path          # Output directory
    filter_pattern: str | None  # e.g., "/users/*" or "^/api/v\d+"
    filter_type: str = "glob" # "glob" or "regex"
    output_version: str = "auto"  # "auto", "3.0.x", "3.1.x"
    concurrency: int = 4      # Parallel threads
    output_format: str = "yaml"   # "yaml" or "json"
    generate_csv: bool = True
    dry_run: bool = False
```

### BatchExtractionResult

```python
@dataclass
class BatchExtractionResult:
    total_endpoints: int
    extracted_count: int
    failed_count: int
    validation_pass_rate: float  # 0.0 to 1.0
    elapsed_time: float  # seconds
    csv_index_path: Path | None
    failed_endpoints: list[tuple[str, str, str]]  # (path, method, reason)
    output_files: list[Path]
```

### CSVIndexEntry (enhancement)

Extends existing model with batch-specific fields:
- `validation_status`: "PASS", "FAIL", "SKIPPED"
- `failure_reason`: Optional detailed reason for failed validation
- `extraction_time_ms`: Time to extract this single endpoint

---

## Implementation Phases

### Phase 0: Research (if needed)
- ✅ Python concurrency patterns for I/O-bound tasks (use ThreadPoolExecutor)
- ✅ Atomic file operations (write to temp, rename) for safety
- ✅ Real-time progress reporting best practices (callback-based, not queues)
- ✅ Glob vs regex filtering (support both, default glob for simplicity)

### Phase 1: Design & Contracts (THIS PLAN)
- ✅ Define BatchExtractionRequest/Result data models
- ✅ Design batch orchestrator interface
- ✅ Define CSV index format and streaming strategy
- ✅ Error handling and resilience approach

### Phase 2: Implementation (Next step)
**T035-T044**: Implement batch processing core
- T035: Create `batch_processor.py` with ThreadPoolExecutor orchestration
- T036: Create `filters.py` for path pattern matching (glob + regex)
- T037: Create `csv_manager.py` for real-time index streaming
- T038: Create `progress.py` for callback-based progress reporting
- T039: Create `output_manager.py` for atomic file writing and naming
- T040: Implement CLI argument handling for batch mode (--batch, --filter, --concurrency)
- T041: Integrate batch orchestrator into main() CLI flow
- T042: Create batch-specific validation error reporting
- T043: Create dry-run functionality (show what would be extracted)
- T044: Run batch tests and verify all 19 tests pass

**T045-T053**: Testing & refinement
- T045-T051: 7 integration tests for batch scenarios (100 endpoints, filtering, error handling)
- T052: Performance benchmark (verify <3 min for 100 endpoints)
- T053: Acceptance test with slice-oas-by-resource skill (verify all outputs usable)

---

## Success Criteria

### Functional Requirements
✅ Extract all matching endpoints from OAS file based on filter pattern
✅ Process 100 endpoints in < 3 minutes (average 30 endpoints/min)
✅ Generate real-time progress updates (not verbose, just counts)
✅ Create CSV index with accurate metadata for each extracted endpoint
✅ Guarantee 100% validation pass rate for all output files
✅ Support both glob (`/users/*`) and regex (`^/api/v\d+`) patterns
✅ Handle up to 16 parallel threads without resource exhaustion

### Quality Requirements
✅ All 55 existing tests remain passing
✅ 19 new batch integration tests pass (100%)
✅ Performance benchmark passes (<3 min for 100 endpoints)
✅ Error resilience: continue on per-endpoint failures
✅ Dry-run mode works correctly (shows what would be extracted)

### UX Requirements (Black Box)
✅ No technical details shown to user (progress: "45/100", not algorithm traces)
✅ Plain-language error messages (no stack traces)
✅ Conversational prompts for filter pattern and concurrency
✅ Success summary: file count, validation rate, time taken

---

## Dependencies & Risk Analysis

### Internal Dependencies
- Phase 3 US1 (single extraction) ✅ **Already complete**
- Existing resolver, slicer, validator, generator modules ✅ **Already tested**
- CLI infrastructure and Black Box UX patterns ✅ **Already established**

### External Dependencies
- `concurrent.futures` (stdlib, Python 3.11+) ✅
- `pathlib` for path operations (stdlib) ✅
- No new external packages required

### Risk Analysis

| Risk | Probability | Severity | Mitigation |
|------|-------------|----------|-----------|
| Parallel extraction race conditions | Low | High | Use thread-safe CSV locking, atomic file ops |
| Memory exhaustion with 1000+ endpoints | Medium | Medium | Process in batches, streaming CSV writes |
| Performance <3min target for 100 | Low | Medium | Baseline: single extraction ~500ms/endpoint, 4 threads = 2 min for 100 |
| File naming collisions | Low | Medium | Sanitize paths, add method to filename |
| Partial failure (some endpoints fail) | High | Low | Continue processing, report summary, don't fail entire batch |

---

## Testing Strategy

### Test Categories

**Unit Tests** (existing, no changes)
- Parser, slicer, validator, generator ✅

**Integration Tests** (NEW, 19 tests)
- T045: Batch extract 10 endpoints
- T046: Batch extract with glob filter (`/users/*`)
- T047: Batch extract with regex filter (`^/api/v`)
- T048: Handle missing endpoints gracefully
- T049: Handle invalid filter pattern
- T050: Generate CSV index correctly
- T051: Parallel extraction produces same results as sequential
- Additional tests for error scenarios

**Performance Tests**
- T052: Extract 100 endpoints in < 3 minutes
- Verify CSV index doesn't bottleneck (streaming writes)

**Acceptance Tests**
- T053: Run extracted endpoints through slice-oas-by-resource skill (verify all usable)

---

## Timeline & Deliverables

**Phase 4 (US2) Deliverables** (19 tasks):
1. Batch orchestrator (`batch_processor.py`)
2. Path filtering (`filters.py`)
3. CSV streaming (`csv_manager.py`)
4. Progress reporting (`progress.py`)
5. Output management (`output_manager.py`)
6. CLI integration (modify `cli.py`)
7. Integration tests (7 scenarios)
8. Performance validation
9. Acceptance testing

**Estimated effort**: 40-50 implementation tasks (T035-T053)
**Expected completion**: 2-3 days of development

---

## Post-Phase 4 Integration

Phase 4 completion enables:
- **Phase 5** (US3): Version conversion leverages batch infrastructure
- **Phase 6** (US4): CSV governance builds on index format from Phase 4
- **Phase 7** (US5): Black Box UX refinements apply to batch mode

---

## Architecture Decisions

### Decision 1: Thread Pool vs Async
**Choice**: ThreadPoolExecutor (Python threading)
**Rationale**: I/O-bound task (file read/write); threading simpler than async for this scale; GIL not a bottleneck for I/O
**Alternative**: AsyncIO - more complex, not needed for <1000 endpoints

### Decision 2: Streaming CSV vs Batch Write
**Choice**: Real-time streaming (append mode)
**Rationale**: Governance teams need live progress; supports monitoring of large batches; file locks prevent corruption
**Alternative**: Batch write at end - user can't see progress

### Decision 3: Per-endpoint Failure Strategy
**Choice**: Continue processing, report summary
**Rationale**: Batch should maximize output; 1 failed endpoint shouldn't block 99 successes
**Alternative**: Fail entire batch - too rigid for production use

### Decision 4: Output Directory Structure
**Choice**: Flat structure with sanitized filenames
**Rationale**: Simple, portable, works with all tools; no need for service-specific subdirs (user can organize post-extraction)
**Alternative**: Auto-organize by service prefix - too opinionated

---

## Next Steps

1. ✅ **This document**: Plan approved
2. 📋 **Data models & contracts**: Define BatchExtractionRequest/Result
3. 🔧 **Implementation**: Build batch_processor.py, filters.py, csv_manager.py (T035-T043)
4. 🧪 **Integration tests**: 7 batch scenarios + performance benchmark (T044-T052)
5. ✓ **Acceptance**: Verify all outputs via slice-oas-by-resource skill (T053)
