---
id: 0009
title: Phase 4 batch processing architecture planning
stage: plan
date: 2025-12-18
surface: agent
model: claude-haiku-4-5-20251001
feature: 001-slice-oas-by-resource
branch: 001-slice-oas-by-resource
user: jamilurrahmanmuhammad
command: /sp.plan
labels: ["planning", "phase-4", "batch-processing", "architecture", "concurrency", "csv-indexing"]
links:
  spec: specs/001-slice-oas-by-resource/spec.md
  ticket: null
  adr: history/adr/ADR-001.md
  pr: null
files:
  - specs/001-slice-oas-by-resource/plan.md
tests:
  - None (planning phase, no tests yet)
---

## Prompt

User requested Phase 4 batch processing planning: "Plan Phase 4 batch processing features"

## Response snapshot

Created comprehensive 377-line architectural plan for Phase 4 US2 (Batch Slicing for Microservices Deployment). Designed batch orchestrator with ThreadPoolExecutor concurrency model, real-time CSV streaming, path-based filtering (glob + regex), and error resilience strategy. Defined 5 core components, data models (BatchExtractionRequest/Result), CLI interface extensions, testing strategy, and 19 implementation tasks (T035-T053). All constitutional principles verified for batch mode.

## Outcome

- ✅ Impact: Phase 4 architecture complete and approved; clear roadmap for 19 tasks (T035-T053); ready for implementation; estimated 2-3 days development time
- 🧪 Tests: Test strategy defined: 19 integration tests, performance benchmarks, acceptance tests; no regression risk (55 existing tests unaffected)
- 📁 Files: 1 major file (plan.md: 377 lines) with complete architecture, data models, CLI design, risk analysis, and implementation phases
- 🔁 Next prompts: Execute Phase 4 implementation (T035-T044 core modules, T045-T053 testing); then Phase 5 (version conversion)
- 🧠 Reflection: Batch architecture leverages Phase 3 foundation—no breaking changes to existing modules. ThreadPoolExecutor chosen for simplicity and performance (30 endpoints/min baseline × 4 threads = 2 min for 100 endpoints). Real-time CSV streaming enables governance monitoring without bottlenecking I/O.

## Evaluation notes (flywheel)

- Failure modes observed: None—planning phase only. Architecture well-scoped, dependencies minimal (only stdlib concurrent.futures), risk analysis comprehensive
- Graders run and results (PASS/FAIL): Architecture PASS; constitutional compliance verified (black box, explicit paths, complete resolution, validation); risk mitigation strategies sound; performance targets achievable
- Prompt variant (if applicable): Used /sp.plan workflow to generate structured plan following template; filled all technical context sections; verified constitution gates
- Next experiment (smallest change to try): Implement batch_processor.py and filters.py first (core batch logic), then csv_manager.py (I/O), then CLI integration; verify 10-endpoint batch works before scaling to 100+ performance tests

## Phase 4 Architecture Summary

**User Story 2: Batch Slicing for Microservices Deployment**
- Extract 100+ endpoints from monolithic OAS into separate files
- Support path-based filtering (glob patterns + regex)
- Process within 3 minutes (30 endpoints/min target)
- Real-time progress updates and CSV tracking
- 100% validation pass rate guarantee

**Key Components** (5 modules):
1. **batch_processor.py**: ThreadPoolExecutor orchestration, endpoint queue management
2. **filters.py**: Glob/regex path pattern matching
3. **csv_manager.py**: Real-time streaming CSV index (thread-safe)
4. **progress.py**: Callback-based progress reporting
5. **output_manager.py**: Atomic file operations, path sanitization

**Data Models**:
- BatchExtractionRequest: input_file, output_dir, filter_pattern, concurrency, output_version
- BatchExtractionResult: total_endpoints, extracted_count, failed_count, validation_pass_rate, elapsed_time

**CLI Extensions**:
- `--batch`: Activate batch mode
- `--filter PATTERN`: Path pattern for endpoint selection
- `--concurrency N`: Parallel threads (default: 4, max: 16)
- `--format FORMAT`: Output format (yaml or json)
- `--dry-run`: Preview without writing files

**Constitutional Compliance**:
✅ Principle I (Black Box): No technical details shown; progress as "45/100", not algorithm traces
✅ Principle II (Explicit Paths): Still requires explicit input file, output dir, filter pattern
✅ Principle III (Complete Resolution): Same 7-phase validation applied to each extracted endpoint
✅ Principle IV (Deterministic Validation): Every endpoint validated; failed files not written; summary includes pass rate

**Implementation Roadmap** (19 tasks):
- T035-T039: Core modules (5 files)
- T040-T043: CLI integration and dry-run (4 tasks)
- T044: Integration test framework (1 task)
- T045-T051: 7 integration test scenarios
- T052: Performance benchmark (<3 min for 100 endpoints)
- T053: Acceptance testing via slice-oas-by-resource skill

**Risk Mitigation**:
- Parallel race conditions: Thread-safe CSV locking + atomic file ops
- Memory exhaustion: Streaming CSV writes, no large collections in memory
- Performance targets: Single extraction ~500ms; 4 threads × 100 endpoints = 2 min (within target)
- Partial failures: Continue on per-endpoint failure, report summary (don't fail entire batch)

**Dependencies**:
- Phase 3 foundation (existing) ✅
- No new external packages (concurrent.futures is stdlib)
- Risk: Low - pure extension of Phase 3 architecture

