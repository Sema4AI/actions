# Sema4.ai Actions Constitution
<!-- Sync Impact Report
Version change: 2.1.1 → 2.2.0
Modified principles:
- V. Observability/Versioning → V. Vendored Builds & Reproducible Releases (refocused)
Added sections:
- Additional Constraints: explicit vendored build policy and license/packaging constraints
Removed sections:
- None
Templates updated: ✅ .specify/templates/plan-template.md
				  ✅ .specify/templates/spec-template.md
				  ✅ .specify/templates/tasks-template.md
				  ✅ .specify/templates/agent-file-template.md
Follow-up TODOs: ⚠ RATIFICATION_DATE left as TODO (see deferred items)
-->

## Core Principles

### I. Library-First Action Design
Every feature or Action MUST be designed as a standalone, well-scoped library. Actions and helper libraries are expected to be:

- self-contained and independently testable (unit + contract tests),
- documented with examples and a quickstart (quickstart.md), and
- discoverable via package metadata (package.yaml) so other teams and agents can reuse them.

Rationale: Designing Actions as libraries promotes reuse, simplifies testing, and reduces coupling between AI-facing logic
and implementation details.

### II. CLI & HTTP-First Interface
All Action Packages MUST expose usable developer interfaces: a command-line surface (CLI) and, when relevant, an HTTP
contract (Action Server endpoints). Interfaces MUST be text-or-JSON friendly: machine-parseable outputs (JSON) and
human-readable fallbacks for interactive use.

Rationale: A predictable CLI + HTTP contract ensures Actions are usable in local development, CI, and by external AI
platforms (e.g., GPTs, LangChain) with minimal glue code.

### III. Test-First (NON-NEGOTIABLE)
Tests MUST be written before implementation. Every new feature or contract change MUST include failing tests that express
the expected behavior (unit, contract, and integration as applicable). Pull requests with implementation changes MUST NOT
merge until the tests are present and green in CI.

Rationale: A test-first discipline ensures design clarity, reduces regressions, and makes the contract between the Action
and its callers explicit and automatable.

### IV. Contract & Integration Testing
Contract tests (schema and behavioral) and end-to-end integration tests MUST cover all externally visible interfaces. When
making contract changes, a migration plan with compatibility guarantees or a breaking-change rationale MUST be provided.

Rationale: AI Agents and downstream systems depend on stable contracts. Contract tests make compatibility explicit and
automatable across releases and tools.

### V. Vendored Builds & Reproducible Releases
When a build artifact (binary or bundled runtime) is vendored into the repository it MUST be justified, reproducible, and
traceable. The following rules apply to vendored build artifacts (for example: pre-built `action-server` binaries, OS
packaged artifacts, or static toolchains):

- Vendoring MUST be approved in the feature plan with a short justification (offline/installability, air-gapped
	environments, or external distribution constraints).
- Every vendored artifact MUST include: origin URL, exact build command, semantic version tag, SHA256 checksum, and
	a link to the producing CI run or release artifact.
- Vendored artifacts MUST be stored under `/build-binary/` or another documented vendor directory and must include a
	machine-readable manifest (vendor-manifest.json) listing checksums and licenses.
- CI MUST validate that any vendored artifact in the repository matches the corresponding artifact produced by the
	canonical build pipeline for that release (binary equality or checksum verification).
- Legal/License review MUST be performed for third-party binaries before vendoring; vendoring of GPL-incompatible
	artifacts is PROHIBITED unless explicitly approved by the legal owner.

Rationale: Vendoring is sometimes necessary for reproducibility or distribution, but it increases maintenance and legal
surface area. These rules make vendoring auditable, automatable, and safer.

## Additional Constraints

- Language & Runtime: Python 3.11.x is the supported runtime for Actions and tooling unless a feature explicitly
	documents a compelling reason for a different runtime. Package environments should be declared in `package.yaml`.
- Licensing: Project is Apache-2.0. Third-party dependencies and vendored artifacts MUST have license declarations and
	pass license scanning before release.
- Build & Release: Releases MUST follow semantic versioning. Vendored build artifacts MUST follow the Vendored Builds
	rules above and be included only when necessary. Release signing and checksums MUST be produced by the canonical CI
	pipeline.
- Observability: Actions MUST emit structured logs and traces. Sensitive information MUST NOT be logged.
- Security: Secrets MUST be stored in CI secrets manager and never committed. Any change that increases privilege or
	external access MUST include a security review and a threat model summary.

## Development Workflow

- Pull Requests: All changes MUST be implemented in feature branches and submitted via PR. PRs MUST include a
	constitution checklist showing how the change satisfies each applicable principle.
- Code Review: At least two maintainer approvals are REQUIRED for non-trivial changes; trivial typos or docs updates may
	be approved by one reviewer if CI is green.
- CI Gates: Every PR MUST pass linting, unit tests, contract tests, and a vendored-artifact verification step when
	relevant. Security, license, and dependency scans MUST run on every PR.
- Release Process: Releases MUST be created from tagged commits. Version bumps MUST follow the Governance rules below.
- Vendor Workflow: For features that vendor builds, the release PR MUST include the vendor manifest, checksum file,
	and a link to the CI run that produced the artifact.

## Governance
<!-- Constitution supersedes ad-hoc practices. Amendments require documentation, approval, and a migration plan. -->

- Constitution Supremacy: This Constitution supersedes informal or ad-hoc practices. Any deviation from the
	Constitution MUST be documented and approved as an explicit exemption in a PR that updates the Constitution.
- Amendment Procedure: Constitutional changes MUST be proposed as a PR against `.specify/memory/constitution.md`.
	Proposals that add or remove principles or materially change governance MUST include a migration plan and rationale,
	and require at least two maintainer approvals. Emergency fixes MAY be fast-tracked but MUST be accompanied by a
	retrospective that is merged into the same PR.
- Versioning Policy: Semantic versioning for the Constitution follows MAJOR.MINOR.PATCH where:
	- MAJOR: Backward-incompatible principle removals or governance redefinitions.
	- MINOR: Addition of a principle/section or material expansion of guidance (e.g., vendored builds rule added).
	- PATCH: Typos, clarifications, or non-semantic wording changes.
- Compliance Review: Each release and feature plan MUST include an explicit Constitution Check section in `plan.md`.
	Automated checks in CI will validate mandatory gates (tests present, vendor manifest when vendoring, license checks,
	and checksum verification for vendored artifacts).

**Version**: 2.2.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown - please insert ISO date
| **Last Amended**: 2025-10-03