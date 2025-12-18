## specifyplus workflow

When setting project rules or adding or changing features, follow this sequence:

1. **Constitution**

   - Use `/sp.constitution` to setup, updating, generaing or refining the project principles

2. **Specify (WHAT)**
   - Use `/sp.specify` to capture user journeys, acceptance criteria, and constraints.

3. **Clarify (WHAT EXACTLY)**
   - Use `/sp.clarify` clarify the specification for removing any ambiguity.


4. **Plan (HOW)**
   - Use `/sp.plan` to specify to plan the feature. provide the following prompt: Now let's plan
        Also:
        – use TDD
        - Use Context7 MCP server for documentation lookups.
        - Prefer CLI automation where possible.


5. **Tasks (BREAKDOWN)**
   - Use `/sp.tasks` to plan the tasks. Providing the following prompt: Now let's  the tasks
        Also:
        – use TDD
        - Use Context7 MCP server for documentation lookups.
        - Prefer CLI automation where possible.

6. **ADR (Architecture)**
   - Use `/sp.adr` to review planning artifacts for architecturally significant decisions and create ADRs. (project)

7. **Analyze (Review)**
   - Use `/sp.analyze` to review the planning and tasks.

8. **Implement (CODE)**
   - Implement tasks *one by one* using `/sp.implement`  Providing the following prompt: Now let's  execute the tasks using the files in the current feature.
        Also:
        – use TDD
        - Use Context7 MCP server for documentation lookups.
        - Prefer CLI automation where possible.



## Agent behavior rules

- Do NOT start large refactors without first updating the spec via specifyplus.
- For ambiguous requirements, call `/sp.clarify` or ask for clarification
  before coding.
- For quality checks, prefer:
  - `/sp.analyze` for spec-driven audits
  - `/sp.checklist` for review checklists

## Files agents should read first

1. `AGENTS.md` (this file)
2. `constitution` (principles/constraints)
3. `spec.md`
4. `checklist.md`
5. `plan.md`
6. `tasks.md`
