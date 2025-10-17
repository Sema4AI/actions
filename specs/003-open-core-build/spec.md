# Feature Specification: Open-Core Build Separation and Dual-Path Frontend for Action Server

**Feature Branch**: `003-open-core-build`  
**Created**: October 5, 2025  
**Status**: Draft  
**Input**: User description: "Open-Core Build Separation and Dual-Path Frontend for Action Server - Establish a maintainable, open-core setup where the Action Server can be built and customized by external contributors without private credentials, while internal Sema4.ai developers retain a seamless path to the proprietary design system and CDN flow."

## Execution Flow (main)
```
1. Parse user description from Input
   → ✓ Feature description provided
2. Extract key concepts from description
   → Identified: OSS contributors, internal developers, build tiers, design system separation
3. For each unclear aspect:
   → Multiple clarifications needed (marked in Requirements)
4. Fill User Scenarios & Testing section
   → ✓ Three primary user journeys defined
5. Generate Functional Requirements
   → ✓ Requirements generated with testability criteria
6. Identify Key Entities (if data involved)
   → Build artifacts, configuration entities identified
7. Run Review Checklist
   → ⚠ WARN "Spec has uncertainties - 6 clarifications needed"
8. Return: SUCCESS (spec ready for clarify phase)
```

---

## ⚡ Quick Guidelines
This specification establishes a dual-tier build system for the Action Server project to enable:
- External contributors to build and customize without proprietary credentials
- Internal developers to maintain access to proprietary design system
- Clear separation between Community tier (open-source core) and Enterprise tier (proprietary features)

---

## Clarifications

### Session 2025-10-05 (5 Questions Resolved)
- Q: How should users and CI switch between Community and Enterprise build tiers? → A: CLI flag (`--tier=community/enterprise`) as authoritative switch with environment variable (`TIER=community`) as convenient default, plus thin task aliases (`build-frontend-community`). Avoid config file to prevent hidden state issues. **[Applied to FR-002]**
- Q: How should the codebase distinguish between community (open) and enterprise (paid) features? → A: Directory structure (`frontend/src/core/` vs `frontend/src/enterprise/`) combined with build-time tree-shaking. Physical separation prevents accidental leakage; build-time stripping enforces it. Avoid runtime flags as primary mechanism (too easy to leak) and separate repos (unnecessary operational overhead for v1). **[Applied to FR-015]**
- Q: Which specific features are enterprise-only, and where do they live? → A: **Enterprise:** Proprietary design system (frontend), branding/themes (frontend), Knowledge Base (backend+frontend), Data Server (backend), org/workspace mgmt (backend), package registry (backend), managed agents (backend), Reducto integration (backend), advanced analytics (backend+frontend, TBD), audit logs (backend, TBD), SSO/SAML/SCIM (backend+frontend, TBD), enterprise RBAC (backend, TBD). **Community:** Action execution (backend+frontend), local action server (backend), full OpenAPI spec (backend), MCP tools (backend), agent SDK (backend), BYO LLM providers (backend), expose tunnels (backend), API-key auth (backend), OAuth2 basic (backend+frontend), run history/logs (backend+frontend), artifacts view (backend+frontend), open UI/Radix (frontend). **[Applied to FR-017; NOTE: Backend implementation out of scope for this feature plan]**
- Q: Which open-source UI component library should the Community tier use? → A: Radix UI + Tailwind CSS (shadcn/ui pattern). Industry-standard headless primitives with utility-first styling - flexible, accessible, and widely adopted. **[Applied to FR-010]**
- Q: How should the existing CI workflows be organized for community and enterprise builds? → A: Single matrix workflow (`.github/workflows/frontend-build.yml`) with `tier: [community, enterprise]` strategy. Community legs run with network hardening (blocked private registries, no secrets); enterprise legs get scoped credentials. Keep CDN workflow (`.github/workflows/frontend-build-cdn.yml`) as manual-only internal convenience (workflow_dispatch), clearly marked non-release. Replace old unauthenticated workflow with matrix approach. Benefits: one pipeline reduces drift, deterministic logs via `matrix.tier`, security-sane secrets scoping, separate release gate validates all matrix legs before artifact promotion. **[Applied to FR-020]**

### Additional Design Decisions (Documented in /plan phase)
- Package.json strategy: Dual files (package.json.community and package.json.enterprise) with build-time copy to root **[Applied to FR-014]**
- Vendored packages: Retained as enterprise fallback with monthly manual updates **[Applied to FR-031]**

---

## User Scenarios & Testing

### Primary User Story 1: External Contributor (Community Tier)

An open-source contributor wants to add a new feature to the Action Server and test it with a customized frontend. They clone the repository on their local machine without any Sema4.ai credentials.

**Acceptance Scenarios:**
1. **Given** a fresh clone of the repository with no npm credentials configured, **When** contributor runs the community build command, **Then** the frontend builds successfully using only open-source components and produces a functional UI
2. **Given** a completed community frontend build, **When** contributor runs the backend build, **Then** the Action Server executable is created with the community-tier UI embedded
3. **Given** the built Action Server executable, **When** contributor launches it and opens the UI, **Then** all core functionality works (even if styling is less polished)
4. **Given** a pull request from an external contributor, **When** CI runs the community build workflow, **Then** no authentication errors occur and no proprietary code is included in artifacts

**Edge Cases:**
- What happens when contributor attempts to build without internet access? (Should succeed - no network dependencies)
- How does system handle if contributor accidentally has GitHub Packages credentials in their npm config? (Should ignore them, still use open-source components)
- What if community build attempts to import proprietary components? (Build should fail with clear error message)

### Primary User Story 2: Internal Developer (Enterprise Tier)

A Sema4.ai employee needs to customize both the frontend and backend for a client demo. They have access to the private npm registry with the proprietary design system packages.

**Acceptance Scenarios:**
1. **Given** valid npm credentials for the private registry, **When** developer runs the enterprise build command, **Then** the frontend builds with the proprietary design system from the private registry
2. **Given** an enterprise build environment, **When** developer is offline but has vendored packages available, **Then** the build falls back to vendored packages successfully
3. **Given** a need for a quick non-customized build, **When** developer runs the CDN build command, **Then** the prebuilt frontend is downloaded rapidly without compilation
4. **Given** an enterprise build configuration, **When** developer switches to community tier, **Then** no source files are modified and switching back is seamless

**Edge Cases:**
- What happens when private registry is down during build? (Registry unavailability detected via 5-second connection timeout; system automatically falls back to vendored packages if manifest.json exists; user notified via warning: "Private registry unavailable, using vendored packages v{version}")
- How does system handle expired npm tokens? (npm authentication failure triggers clear error message: "NPM_TOKEN expired or invalid. Refresh credentials: npm login --registry=https://npm.pkg.github.com"; build exits with code 4 (dependency error))
- What if developer wants to test community tier locally? (Run `inv build-frontend --tier=community` or `TIER=community inv build-frontend`; tier switch takes <5s for config changes, no source modifications required)

### Primary User Story 3: Release Manager (Build/Release Management)

A project maintainer needs to create official release artifacts for both the open-source distribution and internal enterprise version.

**Acceptance Scenarios:**
1. **Given** a release tag on the repository, **When** CI runs the build matrix, **Then** both community and enterprise artifacts are produced with clearly distinguishable names
2. **Given** completed build artifacts, **When** maintainer inspects the community artifact, **Then** no proprietary design system code or paid features are present
3. **Given** completed build artifacts, **When** maintainer reviews build logs, **Then** each log clearly states which tier was built
4. **Given** the same commit hash and build tier, **When** the build runs twice, **Then** the artifacts are byte-for-byte identical (deterministic builds)

**Edge Cases:**
- What happens when enterprise build is accidentally published to public release channels? (CI workflow includes explicit release gate: artifacts containing "enterprise" in filename MUST NOT trigger on public release branches; manual approval required for enterprise artifact promotion; artifact naming convention enforces tier visibility)
- How does system handle partial failures (e.g., community succeeds, enterprise fails)? (Each tier builds independently in separate matrix jobs; one failure doesn't block the other; final workflow status aggregates all jobs; release requires all matrix legs to pass)
- What if a PR modifies paid features but targets community tier? (CI import guard (lint + build-time) detects `frontend/src/enterprise/` modifications; if detected, validation fails with exit code 2 and message: "Enterprise features modified; ensure PR does not include these changes in community builds")

---

## Requirements

### Functional Requirements

**Build System:**
- **FR-001**: System MUST support two distinct build tiers: "Community" (open-source core) and "Enterprise" (proprietary features)
- **FR-002**: System MUST support tier selection via CLI flag (`--tier=community|enterprise`) as primary mechanism with highest precedence, environment variable (`TIER`) as secondary fallback, and hardcoded default as final fallback. Precedence order: CLI flag > environment variable > default (community). System MUST provide convenience task aliases (`build-frontend-community`, `build-frontend-enterprise`)
- **FR-003**: System MUST default to Community tier when no explicit tier selection is made
- **FR-004**: Community tier builds MUST succeed without any authentication to private registries or CDN services. Build system MUST NOT require network access after initial `npm ci` completes (all dependencies resolved from node_modules). CI enforces this via network hardening (blocked private registry hosts)
- **FR-005**: Community tier builds MUST NOT fetch, bundle, or reference any proprietary design system packages
- **FR-006**: Enterprise tier builds MUST support two package sources in priority order: private registry > vendored packages. CDN workflow (`.github/workflows/frontend-build-cdn.yml`) is retained as separate internal convenience workflow (manual-only, workflow_dispatch) but is NOT a build-time dependency source
- **FR-007**: System MUST produce deterministic builds where identical inputs (commit hash + tier + platform) yield byte-identical outputs. Build determinism enforced via: locked dependencies (package-lock.json), Vite output configuration (consistent chunk naming), and SOURCE_DATE_EPOCH environment variable for reproducible timestamps
- **FR-008**: System MUST generate build artifacts with tier-distinguishing names (e.g., `action-server-community-linux` vs `action-server-enterprise-linux`)
- **FR-009**: Build logs MUST explicitly display the selected tier at the start of the build process

**Frontend Components:**
- **FR-010**: Community tier frontend MUST use Radix UI (headless primitives) + Tailwind CSS (utility-first styling) following shadcn/ui patterns instead of proprietary design system
- **FR-011**: Community tier UI MUST be fully functional for all core features (viewing actions, executing requests, viewing results)
- **FR-012**: Community tier UI MUST be visually acceptable with measurable criteria: (1) all interactive elements (buttons, inputs, dropdowns) are clickable and visible, (2) text is readable with sufficient contrast (WCAG AA minimum), (3) layouts do not overflow or cause horizontal scrolling on standard viewports (1280px+), (4) core user flows (execute action, view results, check logs) complete without UI errors, (5) no visual regressions from baseline as measured by visual regression testing
- **FR-013**: Enterprise tier frontend MUST use proprietary design system packages from the selected source
- **FR-014**: System MUST use dual package.json files (package.json.community and package.json.enterprise) with build-time copy operation to root package.json, to manage tier-specific npm dependencies

**Feature Separation:**
- **FR-015**: System MUST use directory structure (`frontend/src/core/` for community, `frontend/src/enterprise/` for enterprise) combined with build-time tree-shaking to enforce tier boundaries during compilation
- **FR-016**: Enterprise features MUST NOT be accessible or included in community tier builds. Enforcement mechanism: Community tier builds MUST exclude `frontend/src/enterprise/` directory via Vite build configuration (`build.rollupOptions.external` pattern matching or custom Vite plugin to fail on enterprise imports during build). Build MUST fail with exit code 2 if enterprise imports are detected in community bundles
- **FR-017**: System MUST enforce the following feature boundaries:
  
  **SCOPE NOTE**: This feature plan (003-open-core-build) addresses **frontend build separation and directory structure only**. Backend enterprise feature implementation (APIs, data access, authentication flows) is Phase 2 and will be addressed in feature plan 004-backend-enterprise-features.
  
  **Feature Classification**:
  - **Enterprise-only frontend**: @sema4ai/* design system packages, branding/themes pack, Knowledge Base UI (frontend scaffolding only)
  - **Enterprise-only frontend (DEFERRED to Phase 2)**: Advanced analytics UI, SSO/SAML configuration UI, Audit logs viewer, Enterprise RBAC management UI
  - **Enterprise-only backend (OUT OF SCOPE - Phase 2)**: Knowledge Base (hosted), Data Server, org/workspace management, package registry/publishing, managed agents, Reducto integration, audit logs backend, SSO/SAML/SCIM backend, enterprise RBAC backend
  - **Community (open) frontend**: Open UI (Radix/shadcn), action execution UI, OAuth2 basic flows, run history/logs, artifacts view/download
  - **Community (open) backend (UNCHANGED)**: Action execution, local action server, full OpenAPI spec, MCP tools/resources/prompts, agent client SDK, BYO LLM providers, expose tunnels, API-key auth, OAuth2 basic backend
  
  **Implementation Note**: Tasks T034 creates frontend page components for enterprise features as **scaffolding only** (no backend API integration). Full functionality requires Phase 2 backend implementation.

**CI/CD:**
- **FR-018**: CI workflows MUST validate both community and enterprise tiers independently
- **FR-019**: CI MUST fail community tier builds if proprietary code imports are detected
- **FR-020**: CI MUST use single matrix workflow (`.github/workflows/frontend-build.yml`) with `tier: [community, enterprise]` and `os: [ubuntu-latest, macos-latest, windows-latest]` strategy. Community tier CI legs MUST run with network hardening (blocked access to private npm registries) and no secret credentials. Enterprise tier CI legs MUST receive scoped credentials (NPM_TOKEN) via secrets, available only to enterprise matrix jobs. CI MUST include guardrail checks for community builds: no enterprise imports, OSI-only licenses, bundle size budget validation. CI MUST generate SBOM (Software Bill of Materials) and provenance metadata for all artifacts. CDN workflow (`.github/workflows/frontend-build-cdn.yml`) MUST be retained as manual-only (`workflow_dispatch`) internal convenience, clearly documented as non-release path. **Implementation details**: See `plan.md` CI Workflow Contract for complete specification (secrets scoping, fork handling, artifact naming)
- **FR-021**: Pull requests from external contributors MUST trigger only community tier builds (not enterprise)
- **FR-022**: Internal branches/PRs MUST trigger both tier builds for validation

**Developer Experience:**
- **FR-023**: Local development setup MUST work for community tier without any credential configuration
- **FR-024**: Internal developers switching between tiers MUST NOT require source file modifications
- **FR-025**: System MUST preserve existing internal developer workflows (CDN quick builds, offline vendored builds)
- **FR-026**: Build failures MUST provide clear, actionable error messages indicating which tier failed and why

**Documentation & Policy:**
- **FR-027**: Documentation MUST clearly explain which features are community vs enterprise. **Canonical feature list**: See FR-017 for authoritative classification. Documentation locations: main README.md (overview) and action_server/frontend/README.md (developer guide)
- **FR-028**: Documentation MUST provide step-by-step instructions for building each tier (build commands, tier selection, troubleshooting in action_server/frontend/README.md)
- **FR-029**: Contribution guidelines MUST direct external contributors to community-tier code paths (contributing section in main README.md specifies: external PRs limited to `frontend/src/core/` and shared utilities)
- **FR-030**: Architecture documentation MUST diagram the separation between Community tier core and Enterprise tier features using Mermaid diagrams in `specs/003-open-core-build/architecture.md`. MUST include 4 required diagrams: (1) directory structure (core/ vs enterprise/ separation), (2) build flow (tier selection → dependency resolution → tree-shaking → artifact generation), (3) CI matrix strategy (tier × os matrix, secrets scoping, fork PR handling), (4) feature boundaries (which features in community vs enterprise - **reference FR-017 for canonical feature classification**)

**Vendored Packages:**
- **FR-031**: System MUST retain vendored packages as enterprise fallback when private registry is unavailable (offline development, network issues). Vendored package updates MUST be applied monthly by platform team via manual process documented in `action_server/frontend/vendored/README.md` (process includes: `npm pack` from private registry, checksum generation, manifest.json update, license validation). **NOTE**: This manual process is intentional (not automated) to ensure review and validation; automation deferred to operational runbook (not in feature scope)
- **FR-032**: Vendored packages MUST maintain integrity checksums via existing `manifest.json` mechanism and MUST pass license validation (reference: `specs/002-build-packaging-bug/LICENSE-REVIEW.md`). This feature validates existing checksums; creation of new vendored packages out of scope

### Non-Functional Requirements

**Performance:**
- **NFR-001**: Community tier builds MUST complete in ≤5 minutes (target based on baseline performance assessment; baseline MUST be measured during T001-PRE by timing current build and documented in this section before implementation; if baseline exceeds target, optimization tasks include: dependency caching, incremental builds, parallel compilation)
- **NFR-002**: Enterprise tier builds MUST complete in ≤7 minutes (target based on baseline performance assessment; baseline MUST be measured during T001-PRE by timing current build and documented in this section before implementation; if baseline exceeds target, optimization tasks include: vendored package preloading, build caching, CDN prefetch)
- **NFR-003**: Switching between tiers (configuration change only, no rebuild) MUST take less than 5 seconds; incremental rebuild after tier switch SHOULD complete in less than 2 minutes

**Security:**
- **NFR-004**: Community tier builds MUST be air-gapped (no network access to private registries)
- **NFR-005**: Proprietary credentials MUST NOT be exposed in community tier build logs or artifacts
- **NFR-006**: Enterprise tier credentials MUST be securely managed via environment variables and secrets management, scoped only to enterprise matrix jobs (never available to community legs)

**Maintainability:**
- **NFR-007**: Build system configuration MUST be namespaced and consolidated: tier selection logic in `build-binary/tier_selector.py`, package resolution in `build-binary/package_resolver.py`, tree-shaking rules in `vite.config.js`, feature boundaries in `feature-boundaries.json`, ESLint rules in `.eslintrc.js`. Adding or modifying tier logic MUST require changes to ≤3 configuration files
- **NFR-008**: Adding new community features MUST NOT require changes to enterprise-tier code paths (enforced by directory separation: changes to `frontend/src/core/` do not affect `frontend/src/enterprise/`)
- **NFR-009**: Adding new enterprise features MUST NOT affect community tier builds (enforced by build-time tree-shaking: enterprise imports excluded from community bundles)

**Reliability:**
- **NFR-010**: Community tier builds MUST have 100% success rate in CI (no flaky network dependencies)
- **NFR-011**: Build system MUST provide clear failure attribution (which tier, which step, why)
- **NFR-012**: CI matrix failure handling MUST aggregate results from all tier × os jobs. One failed job blocks release artifact promotion but does not cancel other running jobs (fail-fast: false). Job summary MUST display pass/fail status for all matrix combinations with drill-down links to failed job logs. Release gate requires all matrix legs to pass before artifacts are promoted to release channels

### Key Entities

**Build Tier Configuration:**
- Represents: The selected build mode (Community or Enterprise)
- Attributes: tier name, default status, validation rules
- Relationships: Determines which dependency sources, UI components, and features are included

**Build Artifact:**
- Represents: The compiled output of a frontend or backend build
- Attributes: tier indicator (in filename), platform (OS/arch), commit hash, build timestamp, checksum
- Relationships: Maps to specific Build Tier Configuration, produced by CI workflow

**Frontend Dependency Source:**
- Represents: Origin of npm packages (private registry, vendored files, or CDN)
- Attributes: source type, priority order, availability check, fallback rules
- Relationships: Selected based on Build Tier Configuration and availability

**Feature Flag:**
- Represents: A marker indicating if a feature is community (open) or enterprise (paid)
- Attributes: feature name, tier restriction, enforcement mechanism
- Relationships: Controls which code paths are included in each Build Artifact

**CI Workflow:**
- Represents: Automated build and validation pipelines
- Attributes: tier scope (community-only, enterprise-only, or both), trigger conditions, artifact outputs
- Relationships: Produces Build Artifacts, validates Build Tier Configuration compliance

---

## Build & Release

### Build Commands
**Community Tier:**
```bash
# Local development build (from action_server/frontend/)
inv build-frontend --tier=community

# CI build (produces: action-server-community-{linux|windows|macos})
.github/workflows/frontend-build-community.yml
```

**Enterprise Tier:**
```bash
# Local development build with private registry
inv build-frontend --tier=enterprise

# Local development build with vendored fallback
inv build-frontend --tier=enterprise --source=vendored

# Quick non-customized build from CDN
inv build-frontend-cdn

# CI build (produces: action-server-enterprise-{linux|windows|macos})
.github/workflows/frontend-build-enterprise.yml
```

### Target Artifacts
- **Community Executables**: `action-server-community-{platform}` - Includes open-source UI, no proprietary features
- **Enterprise Executables**: `action-server-enterprise-{platform}` - Includes proprietary design system and paid features
- **Frontend Bundles**: `frontend-dist-{tier}.tar.gz` - Standalone frontend build outputs

### Packaging Format
- Executables: PyInstaller single-file bundle with embedded frontend HTML/JS/CSS
- Frontend bundles: Tarball containing `index.html` and static assets

### Reproducibility
- Same commit hash + same tier + same platform = byte-identical artifact
- Locked dependencies: `package-lock.json` (community) and enterprise package sources pinned to versions
- Build environment: CI uses consistent Node.js (20.x LTS) and Python (3.11.x) versions
- CI run links: Artifacts include build metadata with CI run URL

### Vendoring Decision
**Community Tier:** No vendored packages - uses only public npm registry packages (e.g., Radix UI, Tailwind)

**Enterprise Tier:** Vendored packages retained as fallback when:
- Private registry is unavailable (offline development, network issues)
- Automated updates applied monthly via existing process (see `action_server/frontend/vendored/`)
- Justification: Enables reliable builds for internal developers without constant network dependency

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details beyond necessary build commands (languages, frameworks minimized to essential references)
- [x] Focused on user value (OSS contribution enablement, internal developer productivity)
- [x] Written for stakeholders (maintainers, contributors, internal developers)
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain - **All 7 clarifications resolved: 5 via /clarify session (2025-10-05) + 2 design decisions in /plan phase**
- [x] Requirements are testable (each FR has verifiable acceptance criteria)
- [x] Success criteria are measurable (deterministic builds, CI success rate, artifact naming validation)
- [x] Scope is clearly bounded (frontend build system, feature separation, CI workflows; backend enterprise features explicitly out of scope)
- [x] Dependencies and assumptions identified (existing vendored packages, PyInstaller backend, current CI structure)

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted (open-core architecture, build tiers, feature separation)
- [x] All ambiguities resolved (7 clarifications: 5 via /clarify session + 2 design decisions)
- [x] User scenarios defined (3 primary user journeys with detailed edge cases)
- [x] Requirements generated (31 functional, 11 non-functional requirements)
- [x] Entities identified (5 key entities with relationships)
- [x] Review checklist passed (all criteria met, no warnings)
- [x] Specification analysis complete (all CRITICAL/HIGH/MEDIUM/LOW issues resolved via /analyze)

---
