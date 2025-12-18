---
id: 0002
title: Implementation plan for slice-oas-by-resource
stage: plan
date: 2025-12-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-slice-oas-by-resource
branch: 001-slice-oas-by-resource
user: jamil
command: /sp.plan
labels: ["planning", "architecture", "design", "tdd", "openapi", "version-conversion"]
links:
  spec: /specs/001-slice-oas-by-resource/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/plan.md
  - /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/research.md
  - /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/data-model.md
  - /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/contracts/cli-interface.md
  - /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/quickstart.md
  - /home/jamil/repos/slice-oas-by-resource/CLAUDE.md
tests:
  - None (planning phase, no tests yet)
---

## Prompt

Execute /sp.plan command for the slice-oas-by-resource feature with this guidance:

**Planning Prompt:**

Now let's plan the slice-oas-by-resource skill implementation. Using TDD and CLI automation where possible:

1. **Analyze the specification** at `/home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/spec.md`

2. **Create the implementation plan** that includes:
   - Technical architecture (layered approach for parsing, validation, transformation, output)
   - Core components needed (OAS parser, reference resolver, version converter, validator, CSV generator)
   - Data flow from input OAS to sliced output
   - Version handling strategy (3.0.x vs 3.1.x detection and conversion)
   - Validation pipeline (7-phase checkpoint system from constitution)
   - Error handling and user-friendly messages

3. **Define technical context**:
   - Language: Python 3.11+ (standard for OpenAPI tooling)
   - Primary dependencies: OpenAPI spec parser (pydantic, openapi-core or similar), YAML support, JSON handling
   - Storage: File-based (input OAS, output sliced files, CSV index)
   - Testing: pytest with fixtures for OAS specifications
   - Target: CLI tool callable from any environment

4. **Design the reference resolution algorithm**:
   - Phase 1: Extract all $ref entries from operation
   - Phase 2: Recursively resolve schemas, parameters, headers, security schemes
   - Phase 3: Collect transitive dependencies (schemas referenced by schemas)
   - Phase 4: Handle circular references safely
   - Phase 5: Build dependency graph to ensure completeness

5. **Design version conversion**:
   - Auto-detect input OAS version
   - Apply transformation rules for 3.0→3.1 or 3.1→3.0 if requested
   - Validate output matches target version syntax

6. **Design validation checkpoints**:
   - Phase 1: File structure (valid JSON/YAML, root keys)
   - Phase 2: Operation integrity (single path, single method)
   - Phase 3: Response integrity (codes match, headers resolve)
   - Phase 4: Reference resolution (all $ref resolve)
   - Phase 5: Component completeness (no orphaned refs)
   - Phase 6: Payload equivalence (matches parent exactly)
   - Phase 7: Version validation (syntax correct for target version)

7. **Define CSV tracking schema**:
   - Columns: path, method, summary, description, operationId, tags, filename, file_size_kb, schema_count, parameter_count, response_codes, security_required, deprecated, created_at, output_oas_version
   - Real-time append during processing
   - Deduplication logic

8. **Design project structure**:
   - src/slice_oas/ with parser, resolver, converter, validator, slicer, generator modules
   - tests/ with fixtures for 3.0, 3.1, circular refs, edge cases
   - docs/ with user-friendly guides

9. **Ensure constitution compliance**:
   - Black box UX: CLI only outputs simple messages, no code shown
   - Explicit paths: Always request input/output paths
   - Complete resolution: All 7 phases covered
   - Deterministic validation: All phases must pass
   - CSV tracking: Includes version info

10. **Generate the complete plan.md** with all sections filled in, ready for task breakdown.

Use TDD principles: design tests first, then implementation. Create comprehensive test cases for edge cases (circular refs, missing components, version conversion failures).

## Response snapshot

Created comprehensive implementation plan with:

**Phase 0: Research** - Resolved all technical unknowns:
- Selected custom parser with PyYAML + jsonschema + openapi-spec-validator for OAS parsing
- Designed BFS reference resolution algorithm with explicit response header scanning
- Defined fail-fast version conversion strategy for unconvertible structures
- Chose append-only CSV updates with pre-write duplicate checking
- Created error message templates for black-box UX compliance

**Phase 1: Design**:
- Documented 8 core entities in data-model.md: OASDocument, Resource, Reference, ResolvedComponent, ValidationResult, CSVIndexEntry, VersionConverter, TransformationRule
- Defined CLI interface contract with 4 commands: extract, batch, list, version-info
- Specified exact argument validation rules and user-friendly error messages
- Created quickstart guide for non-programmers with step-by-step examples

**Constitutional Compliance**:
- All 5 principles validated (Black Box, Explicit Paths, Complete Resolution, Deterministic Validation, CSV Indexing)
- 7-phase validation pipeline explicitly defined
- Version conversion rules documented for 3.0↔3.1 transformations
- Response header scanning requirement highlighted (common defect prevention)

**Technical Architecture**:
- Layered design: CLI → Parser → Resolver → Converter → Validator → Generator
- Python 3.11+ with pydantic, PyYAML, openapi-spec-validator, jsonschema
- File-based I/O with real-time CSV tracking
- BFS graph traversal for reference resolution with circular reference handling
- Deterministic version conversion with pre-validation for unconvertible structures

**Project Structure**:
- src/slice_oas/ with 9 modules (cli, parser, resolver, converter, validator, slicer, generator, models, exceptions)
- tests/ with unit, integration, and fixtures for diverse OAS scenarios
- docs/ with USAGE.md, VERSION_CONVERSION.md, VALIDATION_PHASES.md

Ready for Phase 2: Task generation via /sp.tasks command.

## Outcome

- ✅ Impact: Complete architectural plan created with all design artifacts (plan.md, research.md, data-model.md, cli-interface.md, quickstart.md)
- 🧪 Tests: Test strategy defined (unit + integration with pytest; fixtures for 3.0.x, 3.1.x, circular refs, malformed files)
- 📁 Files: 6 files created/updated (plan.md, research.md, data-model.md, contracts/cli-interface.md, quickstart.md, CLAUDE.md)
- 🔁 Next prompts: Run /sp.tasks to generate actionable task breakdown; then /sp.implement to execute tasks
- 🧠 Reflection: Strong alignment with constitution requirements; explicit response header scanning addresses common defect; version conversion complexity properly scoped with fail-fast strategy

## Evaluation notes (flywheel)

- Failure modes observed: None during planning; anticipated: response header omission (addressed via explicit scanning requirement), version conversion edge cases (addressed via pre-validation and clear error messages)
- Graders run and results (PASS/FAIL): Constitution Check PASS (all 5 principles + OAS version strategy validated)
- Prompt variant (if applicable): N/A (standard /sp.plan workflow)
- Next experiment (smallest change to try): Generate tasks and validate that reference resolution tests explicitly cover response headers
