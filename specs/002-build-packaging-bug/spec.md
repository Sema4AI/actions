# Feature Specification: Remove Private Package Dependencies from Build

**Feature Branch**: `002-build-packaging-bug`  
**Created**: October 3, 2025  
**Status**: Draft  
**Input**: User description: "Build/Packaging Bug: Private design-system packages block open-source builds #220"  
**GitHub Issue**: #220

## Execution Flow (main)
```
1. Parse user description from Input
   ✓ Feature identified: Remove private package dependencies blocking external builds
2. Extract key concepts from description
   ✓ Actors: External contributors, open-source users, downstream packagers
   ✓ Actions: Clone repo, run build, contribute changes, package software
   ✓ Data: Frontend build artifacts, design system packages
   ✓ Constraints: Cannot access private GitHub Packages registry
3. For each unclear aspect:
   → [NEEDS CLARIFICATION: Which solution approach is preferred - vendoring compiled assets or publishing packages publicly?]
4. Fill User Scenarios & Testing section
   ✓ User flow: external contributor attempts to build frontend
5. Generate Functional Requirements
   ✓ All requirements are testable
6. Identify Key Entities
   ✓ Build artifacts, package dependencies
7. Run Review Checklist
   ⚠ WARN "Spec has uncertainties - preferred solution approach needs clarification"
8. Return: SUCCESS (spec ready for planning with one clarification needed)
```

---

## Clarifications

### Session 2025-10-03

- Q: Which solution approach should be implemented to resolve the private package dependency issue? → A: Option A - Vendor compiled assets
- Q: Who should be responsible for updating the vendored design system assets when upstream changes occur? → A: Option C - Automated CI process
- Q: What is the maximum acceptable increase in build time that vendoring assets can introduce compared to the current (working) build? → A: Option A - No increase (0%)
- Q: How often should the automated CI process check for design system package updates? → A: Option C - Monthly (once per month)
- Q: Should CI explicitly test both authenticated and unauthenticated build paths to ensure neither breaks? → A: Option B - Unauthenticated only

---

## Problem Statement

The Action Server frontend build process currently depends on three private packages hosted on GitHub Packages:
- `@sema4ai/theme`
- `@sema4ai/icons`
- `@sema4ai/components`

These dependencies prevent anyone outside the Sema4.ai organization from:
- Building the project from source
- Testing local changes
- Contributing pull requests
- Packaging the software for self-hosted environments

This contradicts the project's open-source positioning and blocks community participation.

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

As an **external contributor**, I want to clone the Actions repository and build the Action Server frontend so that I can test my changes, create pull requests, and package the software for my environment.

Currently, when I run the build command, I receive authentication errors because I cannot access private package registries restricted to the Sema4.ai organization.

### Acceptance Scenarios

1. **Given** a fresh clone of the Actions repository from GitHub, **When** an external contributor runs the frontend build commands without any authentication credentials, **Then** the build completes successfully without errors

2. **Given** the Actions repository, **When** an external contributor examines the package dependencies, **Then** all required packages are either publicly available or bundled with the repository

3. **Given** a contributor wants to test changes to the Action Server, **When** they modify source files and rebuild, **Then** the build process completes using only publicly accessible resources

4. **Given** a downstream packager wants to create distribution packages, **When** they follow the standard build process in an isolated environment, **Then** no private registry credentials are required

### Edge Cases

- What happens when the build environment has no internet access at all? [MUST work - vendored assets eliminate internet dependency]
- What happens when GitHub Packages is unavailable? [No impact - vendored assets don't require external registry access]
- What happens when automated CI detects an upstream design system update? [CI creates a PR for maintainer review before merging]
- What happens if a Sema4.ai team member with private registry access tries to build? [Build uses vendored assets; private registry access is ignored]
- What happens if the automated update process fails? [Manual intervention required; maintainers notified to investigate and update manually]

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Build process MUST complete successfully without requiring authentication to private package registries

- **FR-002**: Build process MUST be reproducible in any environment with standard build tools installed

- **FR-003**: Repository MUST NOT depend on private packages for successful compilation

- **FR-004**: All design system assets required for building MUST be either publicly accessible or included in the repository

- **FR-005**: Build instructions MUST work for users without Sema4.ai organization access

- **FR-006**: Solution MUST maintain visual consistency and functionality of existing UI components (validated by running the test suite and performing manual visual comparison of rendered components against baseline screenshots or reference implementation)

- **FR-007**: Documentation MUST clearly describe the build process without referencing private resources

### Build & Release Requirements

- **FR-008**: Build command sequence MUST be documented and executable by external contributors

- **FR-009**: Vendored assets MUST include all compiled outputs required for frontend functionality

- **FR-010**: Vendoring process and update procedure MUST be documented for maintainers

- **FR-011**: Automated CI process MUST check for upstream design system updates monthly (once per month)

- **FR-012**: CI automation MUST create pull requests when vendored assets need updating

- **FR-013**: Continuous Integration MUST validate that builds succeed without private credentials in an unauthenticated environment

- **FR-014**: CI MUST NOT require or use private registry authentication during build validation

### Non-Functional Requirements

- **NFR-001**: Build time MUST NOT increase compared to current working build (with authenticated access to private packages)

- **NFR-002**: Repository size increase from vendored assets MUST be documented and justified

- **NFR-003**: Vendored assets MUST maintain the same visual fidelity and functionality as private packages

- **NFR-004**: Automated update checks MUST run monthly to maintain vendored asset freshness while minimizing PR noise (see FR-011 for automated CI implementation)

### Key Entities

- **Private Design Packages**: The three packages (`@sema4ai/theme`, `@sema4ai/icons`, `@sema4ai/components`) currently blocking builds. These contain UI styling, iconography, and internal design system components.

- **Frontend Build Artifacts**: The compiled output that the Action Server uses to serve its web interface. These must be buildable from source by anyone.

- **Build Environment**: The isolated environment where external contributors run build commands. Assumes only standard tools and public package registries.

---

## Solution Approaches

The selected approach is **Option A: Vendor Compiled Assets**.

### Chosen Solution: Vendor Compiled Assets
Bundle the pre-built outputs of the design system packages (`@robocorp/theme`, `@robocorp/icons`, `@sema4ai/ds-internal`) directly in the repository, eliminating the need to download them during build.

**Rationale:**
- Guarantees build reproducibility for all external contributors
- Works in offline/air-gapped environments once cloned
- Avoids legal/compliance review process required for public publishing
- Accommodates proprietary components that cannot be open-sourced

**Tradeoffs Accepted:**
- Repository size will increase (acceptable for ensuring open-source contribution)
- Manual update process required when design system changes
- Less transparent about design system source code

### Alternative Considered: Publish Packages Publicly
This option was considered but rejected due to the presence of paid/proprietary components that cannot be distributed publicly (as mentioned in issue discussion by @fabioz).

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified### Specific Validations
- [x] Build & Release section included (mandatory for packaging changes)
- [x] Reproducibility documented
- [x] External contributor perspective captured

---

## Dependencies & Assumptions

### Dependencies
- Access to compiled design system packages for initial vendoring
- CI/CD pipeline infrastructure for automated update checks
- Maintainer approval workflow for automated update PRs
- Documentation of vendoring and update procedures

### Assumptions
- The visual design and functionality can remain unchanged
- External contributors are expected to build from source
- The project should be buildable without organizational credentials
- Standard build tools are available in contributor environments

---

## Success Metrics

The fix is successful when:
1. A contributor with no Sema4.ai access can clone and build the project
2. CI builds pass without private registry credentials
3. No 401 authentication errors occur during package installation
4. Build time remains identical to or faster than the current working build (0% increase)
5. All UI components maintain identical visual appearance and functionality

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed
- [x] All clarifications resolved (5 questions answered)
