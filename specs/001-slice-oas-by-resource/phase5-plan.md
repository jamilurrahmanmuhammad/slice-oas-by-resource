# Implementation Plan: Phase 5 - Version Conversion for Legacy Migration (US3)

**Branch**: `001-slice-oas-by-resource` | **Date**: 2025-12-18 | **Spec**: [spec.md](./spec.md)

**Input**: User Story 3 (Version Conversion) - Extract endpoints from OpenAPI 3.0.x and convert to 3.1.x (and vice versa)

---

## Summary

Phase 5 extends the batch extraction (Phase 4) to support OpenAPI version conversion. DevOps engineers and integration teams need to extract endpoints from OpenAPI 3.0.x specifications and convert them to 3.1.x format (or vice versa) for compatibility with different toolchains. Key requirements: maintain data integrity, resolve all references, deterministic conversion (repeated runs produce identical results), and correctly handle complex schema structures (oneOf, anyOf, allOf).

**Technical Approach**: Build a version converter module that applies transformation rules to extracted endpoints. Reuse Phase 3-4 extraction pipeline, add version detection, apply rule-based transformations, and validate output against target OAS schema. Support bidirectional conversion (3.0 ↔ 3.1).

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pydantic, PyYAML, jsonschema, openapi-spec-validator (existing)
**Storage**: File-based (input OAS → output converted OAS files)
**Testing**: pytest with integration tests (phase-based, TDD)
**Target Platform**: Linux/macOS/Windows (CLI tool)
**Project Type**: Single-purpose CLI tool (extends Phase 4)
**Performance Goals**: Convert 100 endpoints < 3 minutes (same as extraction)
**Constraints**: Zero data loss during conversion, deterministic output, memory-efficient
**Scale/Scope**: Support 3.0.0-3.0.4 → 3.1.x and 3.1.x → 3.0.x conversions

**Key Design Considerations**:
1. **Version Detection**: Auto-detect source OAS version and validate before conversion
2. **Transformation Rules**: Library of rules for 3.0→3.1 and 3.1→3.0 conversions
3. **Reference Handling**: Convert reference locations (e.g., `$ref` path changes)
4. **Schema Transformations**: Handle nullable → type: [null, type], discriminator changes, etc.
5. **Batch Mode Integration**: Extend batch processor to accept `--convert-version` flag
6. **Validation**: Validate output against target schema; fail conversion if validation fails

---

## Constitution Check

✅ **I. Black Box Abstraction** - Version conversion shown as simple option ("Convert to OpenAPI 3.1.x?"); no transformation details, rules, or technical traces exposed to users.

✅ **II. Explicit Path Input** - Still requires explicit: input file, output directory, target version. No auto-detection of versions for conversion.

✅ **III. Complete Reference Resolution** - Converted output must have all references resolved (already done by Phase 3-4 extraction). Conversion maintains reference integrity.

✅ **IV. Deterministic Validation** - Every converted endpoint validated against target schema. Failed conversions don't produce output. Repeated runs produce identical output.

---

## Architecture Overview

### Data Flow

```
Input OAS File (3.0.x or 3.1.x)
    ↓
[Version Detection] → Detect source version
    ↓
[Batch Extraction] → Extract matching endpoints (Phase 4)
    ↓
[Version Converter] → Apply transformation rules
    ├─ For each endpoint:
    ├─ Transform schema structures (nullable, oneOf/anyOf)
    ├─ Convert references if needed
    ├─ Update version string
    └─ Validate against target schema
    ↓
[Output] → Valid converted OAS files
```

### Key Components

1. **Version Converter** (`converter.py` - ALREADY EXISTS)
   - VersionConverter class with bidirectional conversion
   - Transformation rules for 3.0↔3.1
   - Validate output against target schema

2. **Transformation Rules** (`transformation-rules.json` - NEW)
   - Rule library: 3.0→3.1 conversions
   - Rule library: 3.1→3.0 conversions
   - Handles: nullable, discriminator, examples, webhooks, etc.

3. **CLI Integration** (`cli.py` - EXTEND)
   - Add `--convert-version VERSION` argument
   - Integrate with batch processor for bulk conversion
   - Show conversion progress

4. **Validation** (`validator.py` - EXTEND)
   - Add post-conversion validation
   - Check target schema compliance
   - Report conversion errors

---

## Implementation Details

### Version Conversion Rules

**3.0.x → 3.1.x**:
- `nullable: true` → `type: [existing_type, "null"]` (JSON Schema 2020-12 support)
- Add `webhooks` support (optional, 3.1 feature)
- `discriminator.propertyName` → `discriminator.mapping` updates
- `default` value handling (3.1 allows more types)
- `examples` array → enhanced support
- Keep compatibility: all 3.0 constructs remain valid in 3.1

**3.1.x → 3.0.x**:
- `type: [existing_type, "null"]` → `nullable: true` (reverse conversion)
- Remove `webhooks` (not in 3.0 schema)
- `discriminator.mapping` → `discriminator.propertyName`
- Simplify `examples` if needed
- Warn on 3.1-only features (schema composition, new formats)

### Data Models (extend existing models.py)

```python
@dataclass
class VersionConversionRequest:
    source_version: str  # "3.0.x" or "3.1.x"
    target_version: str  # "3.0.x" or "3.1.x"
    transformation_rules: List[TransformationRule]
    strict_mode: bool = False  # Fail on unconvertible structures
    preserve_examples: bool = True

@dataclass
class ConversionResult:
    success: bool
    source_version: str
    target_version: str
    converted_document: Dict[str, Any]
    warnings: List[str]  # Non-fatal issues
    errors: List[str]  # Fatal issues (conversion failed)
    elapsed_time: float
```

### CLI Extensions

**New Arguments**:
- `--convert-version VERSION`: Target version for conversion (3.0.x or 3.1.x)
- `--strict`: Fail on any unconvertible constructs (default: permissive)
- `--preserve-examples`: Keep all examples in output (default: true)

**Updated Workflow**:
```bash
# Single endpoint conversion
slice-oas --input api-3.0.yaml --output-dir ./output \
  --output-version 3.1.x

# Batch conversion with filtering
slice-oas --input api-3.0.yaml --output-dir ./output \
  --batch --filter "/users/*" --convert-version 3.1.x

# Dry-run preview conversion
slice-oas --input api-3.0.yaml --convert-version 3.1.x --dry-run
```

---

## Implementation Phases

### Phase 0: Research (if needed)
- ✅ OpenAPI 3.0 vs 3.1 differences (ALREADY KNOWN)
- ✅ Transformation rules patterns (RESEARCHED IN PHASE 4 PLANNING)
- ✅ JSON Schema 2020-12 changes for 3.1 (DOCUMENTED)

### Phase 1: Design & Contracts (THIS PLANNING)
- ✅ Define VersionConversionRequest/Result models
- ✅ Design transformation rule library
- ✅ Design CLI interface extensions
- ✅ Define validation strategy for converted output

### Phase 2: Implementation
**T054-T063** (10 tasks):
- **T054**: Create `transformation_rules.json` with 3.0→3.1 and 3.1→3.0 rules
- **T055**: Extend `models.py` with VersionConversionRequest/Result
- **T056**: Implement schema transformation logic in `converter.py`
- **T057**: Extend CLI argument parsing with `--convert-version` flag
- **T058**: Integrate version converter into batch processor
- **T059**: Add conversion progress reporting
- **T060**: Implement post-conversion validation
- **T061**: Add dry-run support for conversions
- **T062**: Create conversion error reporting (plain-language messages)
- **T063**: Integration test framework setup

### Phase 3: Testing & Validation
**T064-T073** (10 tasks):
- **T064-T068**: 5 integration tests for version conversions
  - T064: Convert 3.0→3.1 simple endpoint
  - T065: Convert 3.1→3.0 simple endpoint
  - T066: Handle nullable transformations
  - T067: Batch conversion with filtering
  - T068: Error handling (unconvertible constructs)
- **T069**: Determinism test (repeated runs → identical output)
- **T070**: Performance benchmark (100 endpoints < 3 min)
- **T071**: Acceptance test (converted endpoints work as intended)
- **T072-T073**: Edge cases (complex schemas, circular refs, webhooks)

---

## Success Criteria

### Functional Requirements
✅ Convert 3.0.x extracted endpoint to 3.1.x format
✅ Convert 3.1.x extracted endpoint to 3.0.x format
✅ Maintain 100% data integrity (no data loss)
✅ Support batch conversion with filtering
✅ Deterministic output (repeated runs identical)
✅ Validate converted output against target schema

### Quality Requirements
✅ All 79 existing tests still passing
✅ 10+ new integration tests for version conversion
✅ Performance: 100 endpoints conversion < 3 minutes
✅ Error resilience: invalid conversions don't produce output
✅ Deterministic: repeated runs produce bit-identical output

### UX Requirements (Black Box)
✅ Conversion option shown as simple "Convert to 3.1.x?" prompt
✅ No transformation rules, algorithms, or technical details exposed
✅ Plain-language error messages for unconvertible constructs
✅ Progress updates during batch conversion
✅ Success summary: converted count, validation rate, time

---

## Dependencies & Risk Analysis

### Internal Dependencies
- Phase 3 US1 (single extraction) ✅ **Already complete**
- Phase 4 US2 (batch processing) ✅ **Already complete**
- Existing converter module (`converter.py`) ✅ **Already exists**

### External Dependencies
- `openapi-spec-validator` (stdlib, for validation) ✅
- `jsonschema` (stdlib, for JSON Schema validation) ✅
- No new external packages required

### Risk Analysis

| Risk | Probability | Severity | Mitigation |
|------|-------------|----------|-----------|
| Data loss during conversion | Low | High | Validate input/output, test with real OAS files |
| Unconvertible 3.1 features (webhooks) | Medium | Low | Graceful degradation, warn user, skip webhooks |
| Performance regression | Low | Medium | Reuse Phase 4 batch infrastructure, no new I/O |
| Determinism failures (non-idempotent rules) | Low | High | Rule-based approach ensures determinism, test with hash |

---

## Testing Strategy

### Unit Tests (Phase 2 during implementation)
- Transformation rule application (each rule type)
- Version detection (3.0.x vs 3.1.x)
- Reference transformation
- Schema structure conversions (nullable, oneOf, etc.)

### Integration Tests (Phase 3)
- **T064**: 3.0→3.1 simple endpoint (GET /users/{id})
- **T065**: 3.1→3.0 simple endpoint
- **T066**: Nullable transformation (3.0 nullable: true → 3.1 type: [type, null])
- **T067**: Batch conversion with glob filter (/users/*)
- **T068**: Error handling (unconvertible webhooks in 3.0)
- **T069**: Determinism (convert twice, verify identical hashes)
- **T070**: Performance (<3min for 100 endpoints)
- **T071**: Acceptance (converted endpoints valid OAS + usable)
- **T072-T073**: Edge cases (complex schemas, discriminator, security)

### Acceptance Tests
- Run converted endpoints through slice-oas-by-resource skill (Phase 4 acceptance reuse)
- Verify converted files pass `openapi-spec-validator`
- Compare converted vs. expected for determinism

---

## Timeline & Deliverables

**Phase 5 Deliverables** (20 tasks, T054-T073):
1. Transformation rule library (JSON config file)
2. VersionConversionRequest/Result data models
3. Schema transformation logic (nullable, oneOf, etc.)
4. CLI integration (`--convert-version` flag)
5. Batch processor integration
6. Conversion error reporting
7. Validation strategy for converted output
8. Integration tests (10 scenarios)
9. Performance validation
10. Acceptance testing

**Estimated Effort**: 40-50 implementation + test tasks
**Expected Timeline**: 2-3 days development

---

## Post-Phase 5 Integration

Phase 5 completion enables:
- **Phase 6** (US4): CSV governance can track version conversions
- **Phase 7** (US5): Black Box UX refinements apply to conversion prompts
- **Production Use**: Bulk legacy migration (100+ endpoints, 3.0→3.1)

---

## Architecture Decisions

### Decision 1: Rule-Based Transformation vs. Code-Based
**Choice**: Rule-based transformation (JSON config + engine)
**Rationale**: Easier to maintain, add new rules, ensure determinism
**Alternative**: Custom Python for each conversion (harder to test, non-deterministic)

### Decision 2: Fail vs. Warn on Unconvertible Features
**Choice**: Graceful degradation (warn, skip feature, continue)
**Rationale**: Enables bulk migrations (don't block on rare features)
**Alternative**: Strict failure mode (too rigid for production)

### Decision 3: Reuse Batch Infrastructure vs. New Path
**Choice**: Reuse Phase 4 batch processor + add converter layer
**Rationale**: No code duplication, consistent progress reporting, same performance
**Alternative**: Separate conversion CLI (duplicates batch logic)

### Decision 4: Deterministic Output
**Choice**: Always use same rules, same ordering, validate hash
**Rationale**: Critical for CI/CD (repeated runs must match)
**Alternative**: Heuristic-based (non-deterministic, fails requirement)

---

## Next Steps

1. ✅ **This document**: Phase 5 plan complete
2. 📋 **Research phase**: Finalize transformation rules (if any unknowns)
3. 🔧 **Implementation**: Build converter layer (T054-T063)
4. 🧪 **Testing**: Integration tests + acceptance (T064-T073)
5. ✓ **Validation**: Performance, determinism, acceptance criteria

---

## Appendix: Transformation Rules Preview

### 3.0.x → 3.1.x Rules

**Rule 1: Nullable to Type Array**
- Pattern: `"nullable": true` in property
- Action: Convert to `"type": [original_type, "null"]`
- Scope: Schema properties, parameters

**Rule 2: Discriminator Updates**
- Pattern: `"discriminator": {"propertyName": "type"}`
- Action: Add `"mapping"` from oneOf references
- Scope: Schema definitions

**Rule 3: Webhooks (Optional)**
- Pattern: Detect if webhooks present
- Action: Keep in 3.1, warn in 3.0 conversion
- Scope: Root level `webhooks` key

**Rule 4: Schema Composition**
- Pattern: `oneOf`, `anyOf`, `allOf` with references
- Action: Keep as-is (3.1 enhanced JSON Schema support)
- Scope: Schema definitions

### 3.1.x → 3.0.x Rules (Reverse of above)

**Rule 1: Type Array to Nullable**
- Pattern: `"type": [original_type, "null"]`
- Action: Convert to `"nullable": true, "type": original_type`
- Scope: Schema properties, parameters

**Rule 2: Webhooks Removal**
- Pattern: Detect `webhooks` at root
- Action: Remove for 3.0 (not supported), warn user
- Scope: Root level

**Rule 3: Example Simplification**
- Pattern: `"examples"` array with complex values
- Action: Simplify or keep first example only
- Scope: Schema definitions, operations

---

## Related Documents

- Specification: [spec.md](./spec.md)
- Phase 4 Plan: [Phase 4 Complete](./phase4-plan.md) (reference)
- Phase 3 Plan: [Phase 3 Complete](./phase3-plan.md) (reference)
- Constitution: [constitution.md](../../.specify/memory/constitution.md)
