# Paid/Enterprise Components Analysis

**Feature**: 003-build-open-source  
**Date**: 2025-10-04  
**Issue Reference**: [#220 - Build/Packaging Bug: Private design-system packages block open-source builds](https://github.com/Sema4AI/actions/issues/220)  
**Maintainer Comment**: [fabioz on Jun 18](https://github.com/Sema4AI/actions/issues/220#issuecomment-) - "we have some paid components that cannot be distributed as is directly, so, some unbundling/reorganizing is needed"

## Executive Summary

This document identifies all paid/enterprise/proprietary components in the Sema4.ai Actions repository and clarifies which components can be open-sourced vs. which require enterprise infrastructure. The analysis distinguishes between:

1. **Proprietary Frontend Packages** (blocking open-source builds) - **ADDRESSED BY THIS SPEC**
2. **Enterprise Backend Services** (data access infrastructure) - **OUT OF SCOPE** (requires enterprise subscription)
3. **Open-Source Python Libraries** (publicly available on PyPI) - **ALREADY OPEN-SOURCE**

---

## 1. Frontend Design System Packages (PROPRIETARY - BLOCKING BUILDS)

### Status: **ADDRESSED BY SPEC 003-build-open-source**

### Components Identified

| Package | Registry | License | Status | Blocks Open-Source Builds |
|---------|----------|---------|--------|---------------------------|
| `@robocorp/theme` | GitHub Packages (private) | Proprietary | Stub only | ✅ YES |
| `@robocorp/icons` | GitHub Packages (private) | Proprietary | Stub only | ✅ YES |
| `@sema4ai/ds-internal` | GitHub Packages (private) | Proprietary | Stub only | ✅ YES |

### Evidence

**From issue #220**:
```
Running `npm ci && npm run build` in `action_server/frontend` fails with 
`401 Unauthorized – GET https://npm.pkg.github.com/@robocorp/theme`.

The repo depends on:
• @robocorp/theme
• @robocorp/icons
• @sema4ai/ds-internal

All three are private GitHub-Package artifacts, so the build cannot complete
outside the Sema4AI org.
```

**From vendored stub LICENSE files**:
```
This is a stub package for testing purposes.
The actual package is proprietary to Sema4.ai.
```

**Location**: `/action_server/frontend/vendored/`

### Why These Are Proprietary

According to fabioz's comment (Jun 18), these are "paid components that cannot be distributed as is directly." The design system appears to be:
- Custom-built for Sema4.ai's commercial products
- Contains proprietary branding, styling, and components
- Not licensed for public distribution

### Solution: Spec 003-build-open-source

**Approach**: Build clean-room open-source replacements
- Replace with components built from MIT/ISC/Apache 2.0 libraries (Emotion, Lucide React)
- Maintain API compatibility with existing frontend code
- Ensure zero breaking changes to application code
- Implement only features/props actually used (not full API)

**Scope**: Frontend packages ONLY. Does not attempt to open-source backend services.

---

## 2. Data Access Infrastructure (ENTERPRISE BACKEND SERVICES)

### Status: **OUT OF SCOPE** (Requires enterprise subscription/deployment)

### Components Identified

| Component | Type | License | Public Availability | Requires Enterprise |
|-----------|------|---------|-------------------|---------------------|
| `sema4ai.data` (Python library) | PyPI package | Apache 2.0 | ✅ Public on PyPI | ❌ Library is free |
| Data Server | Backend service | Proprietary | ❌ Not distributed | ✅ YES |
| Data Access VS Code Extension | Editor extension | Proprietary | ✅ Public on Open VSX | ✅ YES (requires backend) |
| Control Room | SaaS Platform | Proprietary | ❌ SaaS only | ✅ YES |

### Python Library vs. Backend Services

**Important Distinction**:
- The `sema4ai.data` Python package is **openly distributed** on PyPI
- It provides decorators (`@query`, `@predict`) and DataSource types
- **BUT** these decorators require connection to enterprise backend infrastructure:
  - **Data Server** (proprietary backend service for query federation)
  - **Control Room** (enterprise deployment platform)
  - **Enterprise data sources** (PGVector, knowledge bases, ML models)

### Evidence

**From PyPI listing**:
```
sema4ai-data - Python library to develop data packages for Sema4.ai.
Build powerful data-driven actions that can query databases and work 
with various data sources.
```

**From Open VSX (VS Code extension)**:
```
"Sema4.ai Data Access provides enterprise agents a zero-copy data 
access to past, present, and future data. Read more about the 
offering at our product site."
```

**From web search results**:
```
- "We Offer Pay-As-You-Go Pricing for the favourite Python open-source 
   automation stack ... ENTERPRISE."
- "Build powerful enterprise AI agents using natural language, run them 
   securely in your infrastructure"
```

**From code (`action_server/docs/guides/18-data-packages.md`)**:
```python
# Connection info must be provided:
# - In VS Code via Sema4ai Data Extension
# - In Control Room at deployment time
UsersDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="users_database",
        engine="postgres",
        description="Datasource with users information",
    ),
]
```

### Enterprise Features Requiring Backend

1. **Federated Queries** - Query across multiple data sources in single SQL
2. **Knowledge Base** - `sema4_knowledge_base` engine with embedding/reranking models
3. **Native Queries** - Database-specific queries via Data Server
4. **ML Model Predictions** - `prediction:lightwood` engine
5. **PGVector Integration** - Vector database for semantic search
6. **Data Source Credentials** - Centralized credential management in Control Room

### Templates Showcasing Enterprise Features

| Template | Features Used | Requires Enterprise Backend |
|----------|---------------|----------------------------|
| `data-access-query` | Federated queries, @query decorator | ✅ YES |
| `data-access-native` | Native SQL, PostgreSQL data source | ✅ YES |
| `data-access-kb` | Knowledge Base, embeddings, pgvector | ✅ YES |

**Note**: These templates are included in the open-source repo to **showcase capabilities**, but they require enterprise Data Server infrastructure to execute.

### Why This Is Enterprise/Paid

**Architecture**:
```
┌─────────────────┐
│ Python Actions  │ ← sema4ai.data (free PyPI package)
│   with @query   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Server    │ ← Proprietary backend service
│ (Query Engine)  │    - Query federation
└────────┬────────┘    - Credential management
         │             - Model serving
         ▼
┌─────────────────┐
│ Enterprise Data │ ← Customer databases
│    Sources      │    - Postgres, Oracle, etc.
│  & ML Models    │    - PGVector, ML models
└─────────────────┘
```

The **Data Server** is the proprietary component that:
- Federates queries across multiple databases
- Manages secure credential storage (via Control Room)
- Hosts ML models for predictions
- Provides knowledge base infrastructure

Without the Data Server, `@query` and `@predict` decorators cannot execute.

---

## 3. Control Room Integration (ENTERPRISE SAAS PLATFORM)

### Status: **OUT OF SCOPE** (Commercial SaaS platform)

### Components Identified

| Feature | Purpose | Code Location | Requires Subscription |
|---------|---------|---------------|----------------------|
| Package Publishing | Publish actions to Control Room | `action_server/package/` | ✅ YES |
| Cloud Authentication | HMAC-based auth to Control Room API | `action_server/_storage.py` | ✅ YES |
| Organization Management | List/manage Control Room orgs | CLI `cloud` commands | ✅ YES |
| Deployment | Deploy actions to Control Room | Control Room web UI | ✅ YES |

### Evidence

**From CLI (`action_server/_cli_impl.py`)**:
```python
cloud_parser = command_subparser.add_parser(
    "cloud",
    help="Utilities to perform Control Room operations",
)
# Subcommands: login, verify-login, list-organizations
```

**From package publishing API (`action_server/package/_package_publish_api.py`)**:
```python
def create_package(
    organization_id: str, name: str, access_credentials: str, hostname: str
) -> ActionPackageEntityResponse:
    # Publishes action package to Control Room API
    url = CREATE_PACKAGE_URL.substitute(HOSTNAME=hostname, ORG_ID=organization_id)
```

**From CHANGELOG**:
```
## 0.12.0 - 2024-05-29
- Add new command: cloud
  - Subcommand: login (Save Control Room credentials)
  - Subcommand: list-organizations
- Add new package subcommand
  - publish (publish action package to Control Room)
```

### Why This Is Enterprise/Paid

**Control Room** is Sema4.ai's commercial SaaS platform for:
- Deploying actions to production
- Managing access credentials
- Monitoring executions
- Orchestrating workflows
- Team collaboration

The Action Server can run **locally without Control Room**, but production deployment and management features require a Control Room subscription.

---

## 4. Open-Source Components (Already Public)

### Python Libraries on PyPI (Apache 2.0)

| Package | Purpose | License | Status |
|---------|---------|---------|--------|
| `sema4ai-actions` | @action decorator, Request/Response | Apache 2.0 | ✅ Open-source |
| `sema4ai-data` | @query/@predict decorators, DataSource | Apache 2.0 | ✅ Open-source |
| `sema4ai-mcp` | Model Context Protocol bindings | Apache 2.0 | ✅ Open-source |
| `sema4ai-http-helper` | HTTP utilities | Apache 2.0 | ✅ Open-source |
| `sema4ai-common` | Common utilities | Apache 2.0 | ✅ Open-source |

**Note**: These libraries are all included in this repository under `/actions/`, `/mcp/`, `/sema4ai-http-helper/`, etc.

### Action Server (Open-Source)

The Action Server itself (`action_server/` directory) is **open-source** and can:
- Run actions locally without enterprise backend
- Expose OpenAPI spec
- Provide web UI (with open-source frontend after spec 003)
- Support MCP protocol
- Execute Python @action functions

**Without enterprise backend, the Action Server can**:
- ✅ Run standard Python actions
- ✅ Serve HTTP API
- ✅ Provide web UI
- ✅ Support OAuth2
- ✅ Export OpenAPI spec
- ✅ Integrate with MCP clients

**With enterprise backend (paid), the Action Server can additionally**:
- ❌ Execute @query actions (requires Data Server)
- ❌ Execute @predict actions (requires Data Server + ML models)
- ❌ Publish to Control Room
- ❌ Access enterprise data sources

---

## 5. Distinction Summary

### What IS Open-Source (or Will Be After Spec 003)

| Component | Type | Status | Notes |
|-----------|------|--------|-------|
| Action Server | Python app | ✅ Open-source | Local execution, HTTP API, web UI |
| Python libraries | PyPI packages | ✅ Open-source | `sema4ai-actions`, `sema4ai-data`, etc. |
| **Frontend UI** | **React app** | **❌ BLOCKED** → **✅ Will be open-source after spec 003** | Design system packages replaced |
| Templates | Example code | ✅ Open-source | Including data-access templates (showcase only) |
| CLI tools | Python CLI | ✅ Open-source | `action-server` command |

### What Is Enterprise/Paid

| Component | Type | Distribution | Requirement |
|-----------|------|--------------|-------------|
| Data Server | Backend service | ❌ Not distributed | Enterprise subscription |
| Control Room | SaaS platform | ❌ SaaS only | Enterprise subscription |
| Data Access infrastructure | Cloud service | ❌ Not distributed | Enterprise subscription |
| Knowledge Base backend | ML service | ❌ Not distributed | Enterprise subscription |
| VS Code Data Extension (functionality) | Editor extension | ✅ Distributed but requires backend | Enterprise subscription for backend |

---

## 6. Impact on Spec 003-build-open-source

### Scope Confirmation: ✅ CORRECTLY SCOPED

The current spec **ONLY** addresses the frontend design system packages:
- `@robocorp/theme` → Build open-source replacement
- `@robocorp/icons` → Build open-source replacement  
- `@sema4ai/ds-internal` (components) → Build open-source replacement

**The spec explicitly does NOT attempt to**:
- Replace Data Server (enterprise backend)
- Replace Control Room (SaaS platform)
- Remove `sema4ai.data` dependency (it's already on PyPI)
- Make enterprise features work without backend

### Required Spec Updates

**None required for scope**, but **documentation should clarify**:

1. **Add to spec.md "Out of Scope" section**:
   ```
   ### Out of Scope
   - **Enterprise backend services**: This spec does not replace or open-source 
     the Data Server, Control Room, or other enterprise infrastructure
   - **Data access features**: Templates showcasing @query/@predict remain in 
     repository as examples, but require enterprise Data Server to execute
   - **sema4ai.data library**: This Python library is already open-source on PyPI 
     and remains as-is; only its backend infrastructure is enterprise
   ```

2. **Add to NOTES section**:
   ```
   ### Python Library vs. Backend Services
   The `sema4ai.data` Python package (available on PyPI under Apache 2.0) provides 
   decorators like @query and @predict. However, these decorators require connection 
   to Sema4.ai's proprietary Data Server for execution. The Action Server can run 
   fully open-source for standard @action functions, but data-access features 
   require enterprise backend infrastructure.
   ```

3. **Update README or CONTRIBUTING guide**:
   After spec 003 is implemented, document:
   ```
   ## Building the Action Server
   
   The Action Server can now be built entirely from open-source components:
   - ✅ No GitHub Packages authentication required
   - ✅ All frontend dependencies are open-source
   - ✅ Full local development without credentials
   
   ### Enterprise Features
   Some features require Sema4.ai enterprise backend services:
   - Data Access (@query, @predict decorators)
   - Control Room publishing
   - Knowledge Base operations
   
   See [Enterprise Edition](https://sema4.ai/products/enterprise-edition/) 
   for details.
   ```

---

## 7. Verification Checklist

### After Spec 003 Implementation

- [ ] External contributor can `git clone` repository
- [ ] External contributor can `npm ci && npm run build` without credentials
- [ ] CI builds pass without GitHub Packages access
- [ ] Action Server runs locally with open-source frontend
- [ ] Standard @action functions work without enterprise backend
- [ ] Data-access templates are present but documented as requiring enterprise backend
- [ ] Documentation clearly distinguishes open-source vs. enterprise components

### What Should Still Require Enterprise

- [ ] Executing actions with @query decorator
- [ ] Executing actions with @predict decorator
- [ ] Publishing packages to Control Room
- [ ] Accessing enterprise data sources via Data Access extension

---

## 8. Recommendations

### For Maintainers (Sema4.ai)

1. **Documentation**: Create clear docs distinguishing open-source core vs. enterprise features
2. **Templates**: Add README to data-access templates explaining they're examples requiring enterprise backend
3. **VS Code Extension**: Update Data Access extension description to clarify backend requirement
4. **Licensing**: Consider adding LICENSE.md to clarify which components are Apache 2.0 vs. proprietary

### For This Spec

1. ✅ **Scope is correct**: Only addresses frontend packages, not backend services
2. ✅ **No scope creep needed**: Don't attempt to replace Data Server or Control Room
3. ✅ **Documentation enhancement**: Add clarifications about enterprise vs. open-source to spec.md

---

## 9. Conclusion

### Paid/Enterprise Components Identified

1. **Frontend Design System Packages** (proprietary) - **BEING REPLACED BY SPEC 003**
2. **Data Server** (proprietary backend) - **ENTERPRISE ONLY**
3. **Control Room** (SaaS platform) - **ENTERPRISE ONLY**
4. **Data Access Infrastructure** (backend services) - **ENTERPRISE ONLY**

### Open-Source Components

1. **Action Server** (core app) - **ALREADY OPEN-SOURCE**
2. **Python libraries** (sema4ai-*) - **ALREADY OPEN-SOURCE**
3. **Templates** (example code) - **ALREADY OPEN-SOURCE**
4. **Frontend UI** (React app) - **WILL BE OPEN-SOURCE AFTER SPEC 003**

### Spec 003 Status: ✅ CORRECTLY SCOPED

The spec addresses the **exact** components blocking open-source builds (frontend packages) without attempting to open-source the enterprise backend infrastructure. This aligns with fabioz's comment about "unbundling/reorganizing" - we're unbundling the proprietary frontend components, not the entire enterprise platform.

### Action Required

**Minor documentation updates** to clarify the distinction between:
- Open-source Action Server (works standalone)
- Enterprise backend services (required for data-access features)
- Python libraries (open-source but some depend on enterprise backend)

**No changes to implementation scope needed.**

---

**Analysis Complete**: 2025-10-04  
**Reviewed Issue**: #220  
**Recommendation**: Proceed with spec 003 as planned ✅
