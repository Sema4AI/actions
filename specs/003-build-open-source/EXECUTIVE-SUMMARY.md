# Executive Summary: Paid Components Identification

**Date**: 2025-10-04  
**Issue**: [#220 - Private design-system packages block open-source builds](https://github.com/Sema4AI/actions/issues/220)  
**Spec**: 003-build-open-source  
**Maintainer Quote**: "we have some paid components that cannot be distributed as is directly, so, some unbundling/reorganizing is needed" - fabioz, Jun 18

---

## TL;DR

✅ **Spec 003 is correctly scoped** - it addresses ONLY the frontend design system packages  
✅ **No changes to implementation needed** - focus remains on replacing 3 npm packages  
✅ **Documentation enhanced** - clarified enterprise vs. open-source boundaries in spec.md  
📄 **Full analysis** - see `PAID-COMPONENTS-ANALYSIS.md` for comprehensive breakdown

---

## What Are the "Paid Components"?

### 1. Frontend Design System (ADDRESSED BY THIS SPEC)

**Status**: ❌ Proprietary, blocking builds → ✅ Being replaced with open-source

| Package | Current State | Solution |
|---------|---------------|----------|
| `@robocorp/theme` | Private GitHub Package | Build with Emotion (MIT) |
| `@robocorp/icons` | Private GitHub Package | Build with Lucide React (ISC) |
| `@sema4ai/ds-internal` | Private GitHub Package | Build from scratch with Emotion (MIT) |

**Why paid**: Custom proprietary design system, cannot be publicly distributed  
**Impact**: Blocks `npm ci && npm run build` without GitHub Packages credentials  
**Solution**: Clean-room replacement with open-source libraries (Emotion, Lucide React)

### 2. Enterprise Backend Services (OUT OF SCOPE - ENTERPRISE ONLY)

**Status**: Proprietary infrastructure, requires enterprise subscription

| Component | Type | Impact on Open-Source Builds |
|-----------|------|------------------------------|
| Data Server | Backend query engine | ✅ No impact - optional feature |
| Control Room | SaaS platform | ✅ No impact - optional deployment |
| Data Access infrastructure | Cloud services | ✅ No impact - optional feature |

**Why paid**: Enterprise SaaS infrastructure for production deployment and data access  
**Impact**: Does NOT block builds - Action Server works standalone without these  
**Solution**: Not needed - these are optional enterprise features

### 3. Python Libraries (ALREADY OPEN-SOURCE)

**Status**: ✅ Open-source on PyPI (Apache 2.0)

| Package | License | Status |
|---------|---------|--------|
| `sema4ai-actions` | Apache 2.0 | ✅ Open-source |
| `sema4ai-data` | Apache 2.0 | ✅ Open-source (library only) |
| `sema4ai-mcp` | Apache 2.0 | ✅ Open-source |

**Key distinction**: The `sema4ai.data` **library** is open-source, but the **Data Server backend** it connects to is enterprise/paid.

---

## What Blocks Open-Source Builds?

### Currently Blocking ❌

1. **Frontend npm packages** - Private GitHub Packages require authentication
   - Blocks: `npm ci && npm run build` in `action_server/frontend`
   - **Solution**: Spec 003 replaces with open-source components

### NOT Blocking ✅

2. **Data Server** - Optional backend service (not in build path)
   - Action Server builds and runs WITHOUT Data Server
   - Only needed for `@query`/`@predict` features at runtime

3. **Control Room** - Optional SaaS deployment platform
   - Action Server builds and runs WITHOUT Control Room
   - Only needed for enterprise deployment/management

4. **`sema4ai.data` library** - Already on public PyPI
   - Included as regular pip dependency
   - Builds fine (connects to Data Server at runtime if available)

---

## Spec 003 Scope: Correct ✅

### What Spec 003 DOES Address

✅ Replace `@robocorp/theme` with open-source theme (Emotion)  
✅ Replace `@robocorp/icons` with open-source icons (Lucide React + custom)  
✅ Replace `@sema4ai/ds-internal` with open-source components (Emotion-based)  
✅ Enable `npm ci && npm run build` without credentials  
✅ Maintain API compatibility (zero breaking changes)  
✅ Maintain visual/functional parity (validated via manual QA)

### What Spec 003 Does NOT Attempt

❌ Replace Data Server (enterprise backend - out of scope)  
❌ Replace Control Room (SaaS platform - out of scope)  
❌ Remove `sema4ai.data` dependency (already open-source on PyPI)  
❌ Make data-access features work without backend (enterprise-only)  
❌ Change Action Server core functionality (already open-source)

---

## After Spec 003: What Works Open-Source?

### ✅ Works Standalone (No Enterprise Backend Needed)

- Action Server HTTP API server
- Frontend web UI (with open-source design system)
- Standard Python `@action` functions
- OpenAPI spec generation
- OAuth2 authentication
- MCP protocol support
- Local development and testing

### ❌ Requires Enterprise Backend (Optional Features)

- `@query` actions (need Data Server)
- `@predict` actions (need Data Server + ML models)
- Control Room publishing
- Enterprise data source access
- Knowledge base operations
- Production deployment to Control Room

---

## Fabioz's "Unbundling/Reorganizing" Explained

**Original comment** (Jun 18):
> "we have some paid components that cannot be distributed as is directly, so, some unbundling/reorganizing is needed"

**What needed unbundling**:
1. ✅ **Frontend design system** - Proprietary npm packages → Unbundle and replace with open-source
2. ✅ **Core vs. Enterprise features** - Clarify what works standalone vs. requires backend

**What does NOT need unbundling**:
- Backend services remain proprietary/enterprise (correctly scoped as paid features)
- Python libraries already on PyPI (correctly scoped as open-source)
- Action Server core already open-source (correctly scoped)

Spec 003 **perfectly aligns** with this vision: unbundle the proprietary frontend components while keeping enterprise backend infrastructure separate.

---

## Documentation Updates Made

### 1. spec.md - Out of Scope Section

Added clarifications:
- Enterprise backend services remain proprietary
- Data access features require enterprise infrastructure
- `sema4ai.data` library distinction (open-source lib, enterprise backend)

### 2. spec.md - Notes Section

Added "Python Library vs. Backend Services Distinction":
- Lists what works open-source
- Lists what requires enterprise
- Clarifies templates are examples only
- Links to Sema4.ai Enterprise Edition

### 3. New File: PAID-COMPONENTS-ANALYSIS.md

Comprehensive analysis with:
- Evidence from code, issue #220, web searches
- Architecture diagrams showing open-source vs. enterprise
- Verification checklist for post-implementation
- Recommendations for maintainers

---

## Key Takeaways

1. **Spec 003 scope is perfect** - addresses exactly what blocks builds (frontend packages)
2. **No implementation changes needed** - continue with current plan
3. **Documentation enhanced** - clarifies open-source vs. enterprise boundaries
4. **Templates remain** - data-access examples stay as-is (require enterprise backend)
5. **Action Server is open-source** - works standalone for standard actions
6. **Enterprise features are optional** - don't block open-source usage

---

## Next Steps

### For Implementation

1. ✅ Continue with spec 003 as planned
2. ✅ No changes to scope or approach needed
3. ✅ Focus on replacing frontend packages only

### For Future (Post-Implementation)

1. Add README.md to Action Server explaining:
   - Building now works without credentials
   - What works standalone vs. requires enterprise
2. Update data-access template READMEs:
   - Clarify these are examples requiring Data Server
   - Link to enterprise documentation
3. Consider updating VS Code extension descriptions:
   - Clarify Data Access extension requires backend

---

## Questions Answered

**Q: Do we need to open-source the Data Server?**  
A: ❌ No - it's enterprise infrastructure, out of scope for this spec

**Q: Do we need to remove sema4ai.data dependency?**  
A: ❌ No - it's already open-source on PyPI (Apache 2.0)

**Q: Do data-access templates block builds?**  
A: ❌ No - they're Python code, build fine (require Data Server at runtime)

**Q: Does Action Server work without enterprise backend?**  
A: ✅ Yes - standard @action functions work standalone

**Q: Will external contributors be able to build after spec 003?**  
A: ✅ Yes - `npm ci && npm run build` will work without credentials

**Q: Can we test the Action Server without Control Room?**  
A: ✅ Yes - it runs locally for development and testing

---

**Analysis Complete**: 2025-10-04  
**Status**: ✅ Spec 003 correctly scoped, ready to proceed  
**Documentation**: Updated in spec.md, full analysis in PAID-COMPONENTS-ANALYSIS.md
