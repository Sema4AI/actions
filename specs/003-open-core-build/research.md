# Research: Open-Core Build Separation

**Date**: 2025-10-05  
**Feature**: 003-open-core-build  
**Status**: Complete

## Overview

This document consolidates research findings for implementing a dual-tier build system (Community/Enterprise) for the Action Server project. All technical uncertainties from the specification have been resolved through clarification sessions.

---

## Decision 1: Tier Selection Mechanism

**Chosen**: CLI flag (`--tier=community|enterprise`) as primary mechanism + environment variable (`TIER`) as default + task aliases

**Rationale**:
- CLI flag provides explicit, auditable tier selection in CI logs
- Environment variable offers convenient default for local development
- Task aliases (`build-frontend-community`) provide discoverable shortcuts
- Avoids hidden state issues that config files introduce
- Single source of truth per build invocation

**Alternatives Considered**:
1. **Config file** (`.tierrc` or similar)
   - Rejected: Creates hidden state, easy to commit wrong tier accidentally
   - Rejected: Makes CI logs less transparent (tier not visible in command)

2. **Separate build scripts** (`build-community.sh`, `build-enterprise.sh`)
   - Rejected: Code duplication across scripts
   - Rejected: Harder to maintain consistent build logic

3. **Runtime feature flags**
   - Rejected: Too late in pipeline - want compile-time exclusion
   - Rejected: Risk of leaking paid features if flag misconfigured

**Implementation Details**:
- Python invoke task: `@task def build_frontend(ctx, tier='community', ...)`
- Validation: Fail immediately if `tier not in ['community', 'enterprise']`
- Default behavior: `tier='community'` (safe default, never expose paid features accidentally)

---

## Decision 2: Feature Separation Strategy

**Chosen**: Directory structure (`frontend/src/core/` vs `frontend/src/enterprise/`) + build-time tree-shaking

**Rationale**:
- **Physical separation** makes boundaries obvious, prevents accidental imports
- **Build-time enforcement** guarantees zero enterprise code in community bundles
- **Developer ergonomics**: Clear where to add new features (one directory decision)
- **Lint-friendly**: Static analysis can detect violations pre-commit
- **Review-friendly**: PRs touching `enterprise/` trigger different review flow

**Alternatives Considered**:
1. **Runtime feature flags** (e.g., `if (isEnterprise) { ... }`)
   - Rejected: All code ships to community users (security risk)
   - Rejected: Easy to forget flag check → leak paid features
   - Rejected: Larger bundle sizes unnecessarily

2. **Separate repositories** (`action-server-core` + `action-server-enterprise`)
   - Rejected: Operational overhead (two CI pipelines, two PR flows)
   - Rejected: Slows internal development (must update both repos for changes)
   - Rejected: Overkill for v1 of open-core strategy

3. **Code comments + manual discipline** (`// @enterprise` markers)
   - Rejected: Too fragile, no automated enforcement
   - Rejected: Human error-prone

**Implementation Details**:
- Vite config: `build.rollupOptions.external` to exclude `../enterprise/` for community tier
- ESLint rule: `no-restricted-imports` to block `@/enterprise` in `@/core` files
- CI guard: Post-build AST scan to assert zero `enterprise/` imports in community bundle

---

## Decision 3: Enterprise Feature Boundaries

**Chosen**: Split features into 4 categories (spec FR-017):
- Enterprise frontend: Design system, KB UI, themes, advanced analytics UI, SSO UI
- Enterprise backend: KB hosted, Data Server, org management, registry, managed agents, Reducto, audit logs, SSO backend, enterprise RBAC
- Community frontend: Radix/Tailwind UI, action execution UI, OAuth2 flows, run history, artifacts
- Community backend: Action execution, local server, OpenAPI, MCP tools, agent SDK, BYO LLM, tunnels, API-key auth, OAuth2 backend

**Rationale**:
- **Clear user value distinction**: Community = local development tools, Enterprise = hosted/managed services
- **Licensing alignment**: Community features are OSI-compatible dependencies, Enterprise uses proprietary assets
- **Incremental adoption**: Users start with community, upgrade to enterprise for advanced workflows
- **Maintenance boundary**: Core features have broader contributor base, enterprise features maintained by internal team

**Alternatives Considered**:
1. **Feature-by-feature gating** (every feature has tier flag)
   - Rejected: Too granular, hard to reason about "what's in community?"
   - Rejected: Slippery slope (easy to over-restrict community)

2. **Tier based on deployment target** (local = community, cloud = enterprise)
   - Rejected: Too coarse - want some cloud features in community (e.g., OAuth2)
   - Rejected: Doesn't align with licensing model

**Implementation Details**:
- Backend: `@tier_required('enterprise')` decorator on route handlers
- Frontend: Directory-based enforcement (`enterprise/` imports fail for community tier)
- Documentation: Feature matrix in README showing tier column

---

## Decision 4: Community UI Component Library

**Chosen**: Radix UI (headless primitives) + Tailwind CSS (utility-first styling) following shadcn/ui patterns

**Rationale**:
- **Industry-standard**: Radix is de facto headless UI library for React
- **Accessibility**: ARIA-compliant by default (Button, Dialog, Dropdown, etc.)
- **Flexibility**: Unstyled primitives allow custom branding
- **Lightweight**: Only include components actually used (tree-shakeable)
- **Tailwind integration**: Utility-first styling matches modern React patterns
- **shadcn/ui pattern**: Copy-paste component approach (no npm dependency) gives full control

**Alternatives Considered**:
1. **Material UI (MUI)**
   - Rejected: Heavyweight (~500KB minified), opinionated design
   - Rejected: Harder to customize to match Action Server aesthetic

2. **Chakra UI**
   - Rejected: More dependencies than needed for simple UI
   - Rejected: Runtime theme engine overhead

3. **Headless UI (Tailwind Labs)**
   - Considered: Simpler API than Radix
   - Rejected: Radix has broader component coverage (Accordion, Tabs, Slider, etc.)

4. **Build minimal components from scratch**
   - Rejected: Reinventing accessibility is hard (focus management, keyboard nav, ARIA)
   - Rejected: Not a good use of limited contributor time

**Implementation Details**:
- `frontend/src/core/components/ui/` - shadcn/ui style components
- Install: `@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, etc. (only used components)
- Tailwind config: Extend theme to match existing Action Server color palette
- Migration: Replace `@sema4ai/components` imports in core features with Radix equivalents

---

## Decision 5: CI Workflow Organization

**Chosen**: Single matrix workflow (`.github/workflows/frontend-build.yml`) with `tier: [community, enterprise]` × `os: [ubuntu, macos, windows]` + keep CDN workflow as manual-only

**Rationale**:
- **Reduces drift**: One workflow definition = guaranteed consistent logic across tiers
- **Secrets scoping**: GitHub Actions matrix allows `if: matrix.tier == 'enterprise'` for NPM_TOKEN injection
- **Network hardening**: Community legs run with `env.NO_PROXY=registry.npmjs.org` to block private registries
- **Deterministic logs**: `matrix.tier` visible in job name → easy to debug tier-specific failures
- **Release validation**: Single workflow output = all artifacts validated before release gate

**Alternatives Considered**:
1. **Separate workflows** (`.github/workflows/build-community.yml`, `.github/workflows/build-enterprise.yml`)
   - Rejected: Duplicate logic across two files (higher maintenance burden)
   - Rejected: Harder to ensure both workflows stay in sync

2. **Workflow dispatch input** (`workflow_call` with tier parameter)
   - Rejected: More complex to test (requires triggering workflow manually)
   - Rejected: Less visible in PR checks (matrix shows all tiers explicitly)

3. **Replace CDN workflow entirely**
   - Rejected: Internal developers rely on CDN for quick non-customized builds
   - Decided: Keep as `workflow_dispatch` (manual-only) with clear "internal convenience" label

**Implementation Details**:
- Matrix strategy: `strategy.matrix.tier: [community, enterprise]` + `strategy.matrix.os: [...]`
- Conditional secrets: `env.NPM_TOKEN: ${{ matrix.tier == 'enterprise' && secrets.NPM_TOKEN || '' }}`
- Artifact naming: Upload with `action-server-${{ matrix.tier }}-${{ matrix.os }}-${{ github.sha }}.zip`
- External PRs: `if: github.event.pull_request.head.repo.fork == false || matrix.tier == 'community'` (forks only trigger community builds)

---

## Decision 6: Dependency Management Strategy

**Chosen**: Dual `package.json` files (`package.json.community`, `package.json.enterprise`) + build-time copy

**Rationale**:
- **Explicit dependency lists**: Clear which packages belong to which tier
- **Lock file isolation**: Separate `package-lock.json` for each tier (deterministic builds)
- **Review visibility**: PRs adding enterprise dependencies modify separate file
- **CI simplicity**: Copy `package.json.{tier}` → `package.json` before `npm ci`

**Alternatives Considered**:
1. **Single `package.json` with `optionalDependencies`**
   - Rejected: `npm ci` installs all optional deps by default → no separation
   - Rejected: Can't block community builds from accessing enterprise packages

2. **Programmatic `package.json` modification** (e.g., `jq` to strip `@sema4ai/*`)
   - Rejected: Fragile (breaks if package.json structure changes)
   - Rejected: Harder to review (need to trace modification script)

3. **NPM workspaces** (`packages/community`, `packages/enterprise`)
   - Rejected: Over-engineering for dependency management only
   - Rejected: Complicates build (need to build workspace first)

**Implementation Details**:
- `package.json.community`: Contains only public npm packages (Radix UI, Tailwind, CodeMirror, Tanstack Query)
- `package.json.enterprise`: Adds `@sema4ai/components`, `@sema4ai/icons`, `@sema4ai/theme` (from private registry or vendored)
- Build script: `cp package.json.${tier} package.json && npm ci`
- Git: Track both `.community` and `.enterprise` files, `.gitignore` the generated `package.json`

---

## Decision 7: Vendored Package Strategy

**Chosen**: Retain vendored packages as enterprise fallback (status quo)

**Rationale**:
- **Offline development**: Internal developers can build without network access
- **Registry downtime resilience**: Fallback when private npm registry unavailable
- **Already implemented**: Existing `frontend/vendored/` with manifest.json (checksums, versions)
- **No community impact**: Vendored packages only used for enterprise tier (never in community builds)

**Alternatives Considered**:
1. **Remove vendored packages entirely**
   - Rejected: Breaks offline development workflow (internal team requirement)
   - Rejected: Single point of failure (private registry down = no builds)

2. **Move vendored packages to separate repo**
   - Rejected: Complicates build (need to clone second repo)
   - Rejected: Unnecessary for packages already tracked with checksums

3. **Automated updates via CI** (nightly job to re-vendor latest design system)
   - Considered: Existing manual process is adequate (monthly updates)
   - Future enhancement: Could automate if vendored packages become out-of-date frequently

**Implementation Details**:
- Priority order: Private registry > vendored packages > CDN download
- Manifest: `vendored/manifest.json` contains `{package, version, sha256, license}`
- License compliance: Already reviewed in `specs/002-build-packaging-bug/LICENSE-REVIEW.md`

---

## Decision 8: Build Guardrails

**Chosen**: Multi-layered validation (lint-time + build-time + post-build + CI)

**Rationale**:
- **Defense in depth**: Catch violations at earliest possible stage
- **Fast feedback**: Lint errors show in IDE immediately
- **Deterministic CI**: Same checks run locally and in CI (no surprises)
- **Security-critical**: Accidentally leaking paid features to community is high-risk

**Implementation Details**:

1. **Lint-time** (pre-commit):
   - ESLint rule: `no-restricted-imports` blocks `@/enterprise` imports in `@/core`
   - TypeScript: Path mapping excludes `enterprise/` for community tier builds

2. **Build-time** (during Vite):
   - Vite config: `build.rollupOptions.external` excludes enterprise modules
   - Plugin: Custom Vite plugin to fail if enterprise imports detected in community mode

3. **Post-build** (artifact validation):
   - AST scan: Parse built JS, assert zero matches for `@sema4ai/` imports
   - License scan: Assert all dependencies are OSI-approved for community tier
   - Size check: Warn if bundle size >120% of baseline (prevents accidental inclusion)

4. **CI** (GitHub Actions):
   - Determinism check: Rebuild community artifact, compare SHA256 (must match)
   - SBOM generation: `npm run generate-sbom` produces CycloneDX JSON
   - Provenance: GitHub Actions attestation for artifact integrity

**Alternatives Considered**:
1. **Manual review only**
   - Rejected: Human error-prone, doesn't scale
   - Rejected: Too late (discovered in PR review, not during development)

2. **Runtime checks** (e.g., `if (import.meta.env.TIER === 'community') { throw }`)
   - Rejected: Code still ships to users (security issue)
   - Rejected: Increases bundle size unnecessarily

---

## Decision 9: Backend Tier Handling

**Chosen**: Backend remains tier-agnostic (no build-time changes)

**Rationale**:
- **Simpler architecture**: Frontend tier selection doesn't affect Python code
- **Runtime feature gating**: Backend already has runtime checks for enterprise features (e.g., Knowledge Base enabled only with license key)
- **Single executable**: Community and enterprise both run same `action_server` binary
- **License enforcement**: Existing license validation handles enterprise feature access

**Alternatives Considered**:
1. **Build separate binaries** (`action-server-community`, `action-server-enterprise`)
   - Rejected: Duplicate PyInstaller builds (2x CI time)
   - Rejected: Backend features are license-gated, not build-gated

2. **Tree-shake backend enterprise modules**
   - Rejected: Python tree-shaking is complex (dynamic imports, reflection)
   - Rejected: Not needed - backend features are runtime-disabled without license

**Implementation Details**:
- No changes to `action_server/src/` Python code
- Tier selection only affects frontend bundle embedded in `_static_contents.py`
- License validation at runtime determines which backend features are accessible

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Frontend Language | TypeScript | 5.3.3 | Type safety, IDE support |
| Frontend Framework | React | 18.2.0 | Industry standard, component reuse |
| Build Tool | Vite | 6.1.0 | Fast builds, tree-shaking, single-file output |
| Community UI | Radix UI + Tailwind | Latest stable | Accessible headless primitives |
| Enterprise UI | @sema4ai/* packages | Internal versions | Proprietary design system |
| Backend Language | Python | 3.11.x | Existing codebase |
| Build Automation | invoke | Latest | Existing task runner |
| Backend Packaging | PyInstaller | Latest | Existing executable bundler |
| CI Platform | GitHub Actions | N/A | Repository-native, matrix support |
| Package Manager | npm | 9.x+ (bundled with Node 20) | Standard for Node.js |

---

## Open Questions

**Status**: All questions resolved via clarification session (2025-10-05)

Previously open questions (now resolved):
- ✅ Tier selection mechanism → CLI flag + env var + aliases
- ✅ Feature separation strategy → Directory structure + tree-shaking
- ✅ Community UI library → Radix UI + Tailwind
- ✅ CI workflow organization → Single matrix workflow
- ✅ Vendored package future → Retain as enterprise fallback

---

## Next Steps

1. **Phase 1**: Generate data model, contracts, and quickstart (see `plan.md`)
2. **Phase 2**: Generate ordered task list (see `tasks.md` after `/tasks` command)
3. **Phase 3**: Execute tasks following TDD principles
4. **Phase 4**: Validate quickstart scenarios pass in clean environment

---

**Research Status**: ✅ COMPLETE - All decisions documented, no NEEDS CLARIFICATION remaining
