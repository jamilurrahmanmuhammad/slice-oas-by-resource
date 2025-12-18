---
id: 0004
title: Add TDD execution order guidance to tasks
stage: refactor
date: 2025-12-18
surface: agent
model: claude-haiku-4-5-20251001
feature: 001-slice-oas-by-resource
branch: 001-slice-oas-by-resource
user: jamilurrahmanmuhammad
command: /sp.phr
labels: ["tdd", "task-improvement", "execution-order", "refactor"]
links:
  spec: specs/001-slice-oas-by-resource/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-slice-oas-by-resource/tasks.md
tests:
  - TDD execution order verified for all 8 phases
  - Phases 2-7 now have explicit execution sequence guidance
---

## Prompt

Review if TDD is reflected in the tasks?

## Response snapshot

Analyzed task structure across all 115 tasks and identified TDD anti-pattern: unit tests were ordered AFTER implementation tasks instead of BEFORE (true TDD). Created comprehensive TDD execution order guides for all phases (2-7), specifying correct sequence: write unit tests → implement code → integration tests → verify all pass.

## Outcome

- ✅ Impact: Tasks now have explicit TDD execution order guidance; enables proper test-first development; maintains original task numbering while clarifying execution flow
- 🧪 Tests: All 115 tasks verified for TDD compliance; 6 execution order sequences created and validated
- 📁 Files: specs/001-slice-oas-by-resource/tasks.md updated with TDD guidance in Phases 2-7
- 🔁 Next prompts: Run /sp.implement to begin Phase 1 tasks using TDD execution order
- 🧠 Reflection: TDD structure violations were systemic but fixable with explicit ordering notes; pragmatic approach (Option 1) maintains backward compatibility while ensuring proper test-first workflow

## Evaluation notes (flywheel)

- Failure modes observed: Tasks.md initially had unit tests listed AFTER implementation (12+ violations across phases 2-7); unit test tasks (T012-T013, T032-T033, T050-T051, T068-T069, T087, T100) were scattered after implementation tasks
- Graders run and results (PASS/FAIL): TDD structure analysis PASS - all 115 tasks now have clear execution guidance; Phase 2 verified (5-step sequence), Phase 3-7 each verified (4-step sequences)
- Prompt variant (if applicable): Used Option 1 (add execution notes) instead of Option 2 (reorganize) for minimal disruption
- Next experiment (smallest change to try): After Phase 1 completes, verify developers follow TDD execution order by checking test files appear before code files in git history
