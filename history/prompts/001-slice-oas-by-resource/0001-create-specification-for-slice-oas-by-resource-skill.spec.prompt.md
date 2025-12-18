---
id: 0001
title: Create specification for slice-oas-by-resource skill
stage: spec
date: 2025-12-17
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-slice-oas-by-resource
branch: 001-slice-oas-by-resource
user: jamil
command: /sp.specify
labels: ["specification", "openapi", "oas-slicing", "api-documentation"]
links:
  spec: /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/spec.md
  - /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/checklists/requirements.md
tests:
  - Specification quality validation passed all checks
---

## Prompt

Execute /sp.specify command with this feature description for slice-oas-by-resource skill:

**Feature Description:**

The slice-oas-by-resource skill is an interactive tool that decomposes large OpenAPI specifications into individual, self-contained OAS files—one for each path and HTTP method combination. The skill enables API teams and technical writers to manage, export, and document individual API endpoints as standalone specifications while maintaining complete fidelity with the parent specification.

**User Scenarios:**

1. **API Architect** needs to extract individual endpoint specifications (e.g., GET /users/{id}) from a 500-endpoint parent OAS file to generate focused endpoint documentation and share with external partners without exposing the full API surface.

2. **Technical Writer** wants to generate PDF documentation for specific API resources by slicing the parent spec and then converting to different formats, without manually reconstructing references and dependencies.

3. **DevOps Engineer** needs to decompose a monolithic API spec into service-specific OAS files for microservices deployment, ensuring each service has only its required endpoints and schemas.

4. **Integration Team** must export 50+ API endpoints to a CSV index for tracking, governance, and bulk operations across multiple OAS versions (both 3.0.x and 3.1.x).

5. **Legacy System Migration** requires slicing a 3.0.x spec and converting sections to 3.1.x while maintaining data integrity and reference resolution.

**Key Requirements:**

- Slice input OAS file by path and HTTP method
- Support both single resource and batch slicing (all resources, multiple resources by filter)
- Output formats: JSON and YAML
- Multi-version support: OAS 3.0.x and 3.1.x (with automatic version conversion if requested)
- Complete reference resolution: all schemas, parameters, headers, security schemes must be included
- CSV index generation with real-time updates during processing
- Black box UX: non-programmer users never see code or technical details
- Explicit path input: no auto-discovery or directory searching
- Strict validation: 7-phase validation checkpoint before accepting any output

**Success Criteria:**

- Users can slice any single endpoint in under 5 seconds
- Batch slicing of 100 endpoints completes in under 3 minutes
- 100% of sliced files pass validation (all $ref entries resolve)
- CSV index accurately tracks all sliced resources with version information
- Version conversion (3.0↔3.1) is deterministic and correct for all standard constructs
- Non-programmers can complete entire workflow without seeing code or algorithms
- All sliced files are valid, standalone OpenAPI specifications usable by downstream tools immediately

Provide the complete spec.md file with all user scenarios, requirements, acceptance criteria, edge cases, and assumptions documented and ready for the planning phase.

## Response snapshot

Successfully created comprehensive feature specification for slice-oas-by-resource skill with:

1. **Branch Created**: 001-slice-oas-by-resource
2. **Specification File**: /home/jamil/repos/slice-oas-by-resource/specs/001-slice-oas-by-resource/spec.md

**Specification Contents**:
- 5 prioritized user stories (P1-P4) with independent test descriptions
- 39 functional requirements organized into 7 categories:
  - Core Slicing Capabilities (FR-001 to FR-009)
  - Batch Processing (FR-010 to FR-013)
  - Output Formats (FR-014 to FR-017)
  - Version Conversion (FR-018 to FR-021)
  - CSV Index Generation (FR-022 to FR-025)
  - Validation (FR-026 to FR-030)
  - User Experience (FR-031 to FR-036)
  - Performance and Reliability (FR-037 to FR-039)
- 8 key entities with attributes
- 10 measurable, technology-agnostic success criteria
- 12 edge cases identified
- 12 assumptions documented
- Clear scope boundaries (Out of Scope section with 12 items)
- 3 dependencies specified

**Quality Validation**: All specification quality checklist items passed, including:
- Zero [NEEDS CLARIFICATION] markers (all requirements are concrete)
- All requirements are testable and unambiguous
- Success criteria are measurable and technology-agnostic
- No implementation details leaked into specification
- Focused on user value and business needs

The specification is complete and ready for the next phase (/sp.plan).

## Outcome

- ✅ Impact: Created comprehensive, production-ready feature specification for OpenAPI slicing tool with 5 user stories, 39 functional requirements, and complete acceptance criteria
- 🧪 Tests: Specification passed all quality validation checks (requirements completeness, technology-agnostic criteria, testability)
- 📁 Files: Created spec.md (279 lines) and requirements.md checklist
- 🔁 Next prompts: /sp.plan (architectural planning), /sp.clarify (if clarifications needed - currently none)
- 🧠 Reflection: Specification successfully balances comprehensiveness with clarity, maintaining strict separation between "what" and "how" while providing concrete, measurable requirements ready for implementation planning

## Evaluation notes (flywheel)

- Failure modes observed: None - specification completed successfully with all validation checks passing
- Graders run and results (PASS/FAIL): Specification Quality Validation - PASS (all 14 checklist items passed)
- Prompt variant (if applicable): Standard /sp.specify workflow with detailed feature description
- Next experiment (smallest change to try): Proceed to /sp.plan to generate architectural decisions and technical design based on this specification
