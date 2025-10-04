# Recommendations: Open-Source vs. Enterprise Boundaries

**Date**: 2025-10-04  
**Spec**: 003-build-open-source  
**Purpose**: Actionable recommendations for maintaining clear boundaries between open-source and enterprise components

---

## For Maintainers (Sema4.ai Team)

### Immediate Actions (Post Spec 003 Implementation)

#### 1. Update Main README.md

Add a section clarifying what's open-source:

```markdown
## Building the Action Server

The Action Server can now be built entirely from open-source components without any authentication or credentials:

```bash
git clone https://github.com/Sema4AI/actions.git
cd actions/action_server/frontend
npm ci && npm run build  # No credentials needed! ✅
```

### What Works Open-Source

- ✅ Action Server HTTP API
- ✅ Web UI with complete design system
- ✅ Standard Python `@action` functions
- ✅ OpenAPI spec generation
- ✅ OAuth2 authentication
- ✅ MCP protocol support
- ✅ Local development and testing

### Enterprise Features

Some features require Sema4.ai's enterprise backend infrastructure:

- **Data Access** (`@query`, `@predict` decorators) - Requires Data Server
- **Control Room Publishing** - Requires Control Room subscription
- **Enterprise Data Sources** - PostgreSQL, Oracle, ML models via Data Server
- **Knowledge Bases** - Embedding/reranking models via Data Server

See [Sema4.ai Enterprise Edition](https://sema4.ai/products/enterprise-edition/) for enterprise features.

### Contributing

External contributors can now:
- Build and test the Action Server locally
- Contribute to core functionality
- Submit PRs without needing credentials
- Run CI builds successfully

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
```

#### 2. Add Template READMEs

Create `action_server/templates/data-access-*/ENTERPRISE-NOTICE.md`:

```markdown
# Enterprise Backend Required

This template showcases **Sema4.ai Data Access** features which require enterprise infrastructure to execute.

## What This Template Demonstrates

- Using `@query` decorators to query databases
- DataSource configuration patterns
- SQL query examples with parameters
- Integration with Sema4.ai Data Server

## Running This Template

### Development (Requires Enterprise)

To run this template, you need:

1. **Sema4.ai Enterprise subscription** with Data Access enabled
2. **Data Server** configured and running
3. **VS Code Sema4.ai Data Extension** installed
4. **Data source credentials** configured in the extension

Contact [Sema4.ai Sales](https://sema4.ai/contact/) for enterprise access.

### Learning Mode (No Backend Required)

You can:
- ✅ Review the code to understand data-access patterns
- ✅ Use as a starting point for your own implementation
- ✅ See how `@query` decorators are structured
- ❌ Cannot execute queries without Data Server

## Open-Source Alternative

For open-source database access without enterprise backend, consider:
- Direct database connections with `psycopg2`, `pymongo`, etc.
- SQLAlchemy for ORM-based queries
- Standard Python data access libraries

The Action Server itself is fully open-source and can execute standard `@action` functions that use these libraries.
```

#### 3. Update VS Code Extension Descriptions

**Data Access Extension** (`open-vsx.org` and VS Code Marketplace):

```
Sema4.ai Data Access provides enterprise agents with zero-copy access to databases, 
knowledge bases, and ML models.

**Note**: This extension connects to Sema4.ai's enterprise Data Server infrastructure. 
A Sema4.ai Enterprise subscription is required for query execution.

The extension provides:
- Data source configuration UI
- Query builder and testing
- Integration with Action Server
- Credential management

For open-source Action Server usage without Data Access features, see the 
core sema4ai-actions extension.
```

#### 4. Create ARCHITECTURE.md

Document the system architecture:

```markdown
# Action Server Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Open-Source Components                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐      ┌──────────────┐     ┌─────────────┐ │
│  │   Web UI    │◄────►│    Action    │◄───►│   Python    │ │
│  │   (React)   │      │    Server    │     │   Actions   │ │
│  └─────────────┘      │   (FastAPI)  │     │   (@action) │ │
│                        └──────────────┘     └─────────────┘ │
│                               │                              │
└───────────────────────────────┼──────────────────────────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │   HTTP Clients     │
                     │   (AI Agents)      │
                     └────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Enterprise Components                      │
│                    (Optional - Paid)                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │  Data Server │◄────►│   Control    │◄───►│   ML       │ │
│  │  (Queries)   │      │     Room     │     │  Models    │ │
│  └──────────────┘      │  (SaaS)      │     └────────────┘ │
│         │              └──────────────┘                     │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │  Enterprise  │                                           │
│  │ Data Sources │                                           │
│  └──────────────┘                                           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Open-Source Layer

**Action Server** (`action_server/`):
- HTTP API server (FastAPI)
- Action execution runtime
- OpenAPI spec generation
- OAuth2 authentication
- MCP protocol support
- License: Apache 2.0

**Web UI** (`action_server/frontend/`):
- React-based user interface
- Action testing and execution
- OpenAPI explorer
- Design system (open-source after spec 003)
- License: Apache 2.0

**Python Actions** (`actions/`):
- `@action` decorator
- Request/Response models
- Standard Python code execution
- License: Apache 2.0

### Enterprise Layer (Optional)

**Data Server**:
- Query federation across multiple databases
- DataSource credential management
- ML model serving
- Knowledge base infrastructure
- License: Proprietary

**Control Room**:
- SaaS deployment platform
- Team collaboration
- Production monitoring
- Package management
- License: Proprietary

## Open-Source Usage

The Action Server can run **completely standalone** for:
- REST API actions
- Standard Python functions
- Local development
- HTTP/MCP integration

**No enterprise components required** for basic usage.

## Enterprise Usage

Add Data Server and Control Room for:
- Multi-database queries (`@query`)
- ML predictions (`@predict`)
- Enterprise data sources
- Production deployment
- Team management

**Requires enterprise subscription** for these features.
```

---

## For External Contributors

### Quick Start Guide

Create `CONTRIBUTING.md` section:

```markdown
## Getting Started

### Prerequisites

- Node.js 20.x LTS
- Python 3.11+
- Git

### Building Locally (No Credentials Required!)

```bash
# Clone repository
git clone https://github.com/Sema4AI/actions.git
cd actions

# Install Python dependencies
cd action_server
pip install poetry
poetry install

# Build frontend
cd frontend
npm ci        # No authentication needed after spec 003! ✅
npm run build

# Run Action Server
cd ..
poetry run action-server start --actions=../templates/basic
```

### What You Can Contribute To

✅ **Action Server core** - HTTP API, execution runtime, CLI  
✅ **Web UI** - React components, user experience  
✅ **Python libraries** - Actions, decorators, utilities  
✅ **Documentation** - Guides, examples, API docs  
✅ **Templates** - Example action packages  
✅ **Tests** - Unit tests, integration tests  

### What Requires Enterprise Access

Some features connect to proprietary backend infrastructure:

❌ **Data Server integration** - Requires enterprise subscription  
❌ **Control Room features** - Requires enterprise subscription  
❌ **Data-access templates execution** - Examples only, need backend  

You can still:
- Review and improve data-access template code
- Contribute to the Action Server runtime that executes them
- Test with mock data sources

### Testing Your Changes

```bash
# Run Action Server tests
poetry run pytest

# Run frontend tests
cd frontend
npm test

# Run integration tests
poetry run pytest tests/integration/
```

All tests run without enterprise backend!
```

---

## For Users/Developers

### Decision Matrix: When Do I Need Enterprise?

Create a decision flowchart document:

```markdown
# Do I Need Sema4.ai Enterprise?

## Quick Decision Tree

```
START: What are you building?
│
├─ [HTTP API actions with Python]
│  └─> ✅ FREE - Use open-source Action Server
│      No enterprise needed
│
├─ [Query multiple databases in one action]
│  └─> ❌ ENTERPRISE - Requires Data Server
│      Contact Sema4.ai for subscription
│
├─ [ML model predictions in actions]
│  └─> ❌ ENTERPRISE - Requires Data Server
│      Contact Sema4.ai for subscription
│
├─ [Deploy to production with team]
│  ├─ [Self-hosted]
│  │  └─> ✅ FREE - Deploy Action Server yourself
│  └─ [Managed platform]
│     └─> ❌ ENTERPRISE - Use Control Room
│         Contact Sema4.ai for subscription
│
└─ [Local development and testing]
   └─> ✅ FREE - Everything works open-source
```

## Feature Comparison

| Feature | Open-Source | Enterprise |
|---------|-------------|------------|
| **Action Server HTTP API** | ✅ Included | ✅ Included |
| **Web UI** | ✅ Included | ✅ Included |
| **Standard Python actions** | ✅ Included | ✅ Included |
| **OpenAPI spec** | ✅ Included | ✅ Included |
| **MCP protocol** | ✅ Included | ✅ Included |
| **OAuth2 auth** | ✅ Included | ✅ Included |
| **Local testing** | ✅ Included | ✅ Included |
| | | |
| **Multi-database queries** | ❌ Not available | ✅ Data Server |
| **ML model predictions** | ❌ Not available | ✅ Data Server |
| **Knowledge bases** | ❌ Not available | ✅ Data Server |
| **Vector search** | ❌ Not available | ✅ Data Server |
| **Enterprise data sources** | ❌ Not available | ✅ Data Server |
| **Control Room deployment** | ❌ Not available | ✅ Control Room |
| **Team collaboration** | ❌ Not available | ✅ Control Room |
| **Production monitoring** | ❌ Not available | ✅ Control Room |

## Example Use Cases

### ✅ Open-Source is Perfect For:

1. **Simple REST API actions**
   ```python
   @action
   def calculate_tax(income: float, rate: float) -> float:
       return income * rate
   ```

2. **Single database queries** (using standard libraries)
   ```python
   import psycopg2
   
   @action
   def get_user(user_id: int) -> dict:
       conn = psycopg2.connect(DATABASE_URL)
       # Query single database
   ```

3. **AI agent tools**
   - HTTP API for LangChain, AutoGPT, etc.
   - MCP server for Claude Desktop
   - OpenAPI for agent frameworks

4. **Local development**
   - Test actions before deployment
   - Rapid prototyping
   - Learning and experimentation

### ❌ Enterprise Needed For:

1. **Cross-database queries**
   ```python
   @query  # Requires Data Server
   def sales_report(datasource: DataSource):
       # Join data from PostgreSQL + MongoDB + Snowflake
       sql = """
       SELECT s.amount, c.name, p.title
       FROM sales.orders AS s
       JOIN customers.users AS c
       JOIN products.catalog AS p
       """
   ```

2. **ML predictions**
   ```python
   @predict  # Requires Data Server
   def predict_churn(datasource: DataSource):
       # Use hosted ML model
   ```

3. **Production deployment**
   - Managed infrastructure
   - Team access control
   - Monitoring and logging
   - Package versioning

## Getting Enterprise Access

Contact Sema4.ai:
- Website: https://sema4.ai/contact/
- Email: sales@sema4.ai
- Request: Data Access or Control Room demo
```

---

## For Documentation Team

### Doc Structure Recommendations

```
/docs
├── README.md                          # Overview with enterprise distinction
├── getting-started/
│   ├── quickstart.md                 # Open-source quickstart
│   ├── quickstart-enterprise.md      # Enterprise features quickstart
│   └── installation.md               # No credentials needed!
├── guides/
│   ├── actions/                      # Open-source guides
│   ├── data-access/                  # Enterprise guides (clearly marked)
│   └── deployment/
│       ├── self-hosted.md           # Open-source deployment
│       └── control-room.md          # Enterprise deployment
├── architecture/
│   ├── overview.md                  # System architecture diagram
│   ├── open-source-components.md    # What's included
│   └── enterprise-components.md     # What's enterprise
└── contributing/
    ├── development.md               # No credentials needed
    └── testing.md                   # All tests run open-source
```

### Documentation Markers

Use consistent markers throughout docs:

```markdown
<!-- Open-Source Feature -->
✅ **Open-Source**: This feature works without enterprise backend.

<!-- Enterprise Feature -->
🔒 **Enterprise**: This feature requires Sema4.ai Data Server / Control Room.
Contact [sales@sema4.ai](mailto:sales@sema4.ai) for access.

<!-- Example Only -->
📖 **Example**: This template demonstrates enterprise features.
Code can be reviewed, but execution requires enterprise backend.
```

---

## For CI/CD

### GitHub Actions Updates

#### 1. Add Open-Source Build Verification

`.github/workflows/verify-open-source-build.yml`:

```yaml
name: Verify Open-Source Build

on:
  pull_request:
  push:
    branches: [master]

jobs:
  build-without-credentials:
    name: Build without any enterprise credentials
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Verify no credentials in environment
        run: |
          # Ensure truly open-source
          if [ -n "$NPM_TOKEN" ] || [ -n "$GH_TOKEN" ] || [ -n "$NODE_AUTH_TOKEN" ]; then
            echo "ERROR: Credentials found - build must work without"
            exit 1
          fi
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Build frontend (without credentials)
        run: |
          cd action_server/frontend
          npm ci    # Must succeed without authentication
          npm run build
      
      - name: Verify build artifacts
        run: |
          cd action_server/frontend
          test -f dist/index.html || exit 1
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Build Action Server
        run: |
          cd action_server
          pip install poetry
          poetry install
          poetry run action-server --help
```

#### 2. Add Template Tests

Verify templates build (even if execution requires enterprise):

```yaml
name: Template Validation

on: [pull_request, push]

jobs:
  validate-templates:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        template:
          - basic
          - data-access-query      # Build only, no execution
          - data-access-native     # Build only, no execution
          - data-access-kb         # Build only, no execution
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Validate ${{ matrix.template }} syntax
        run: |
          cd templates/${{ matrix.template }}
          python -m py_compile *.py
      
      - name: Check dependencies installable
        run: |
          cd templates/${{ matrix.template }}
          if [ -f package.yaml ]; then
            # Verify package.yaml is valid
            python -c "import yaml; yaml.safe_load(open('package.yaml'))"
          fi
```

---

## Implementation Checklist

### Immediate (With Spec 003)

- [ ] Update `spec.md` with enterprise clarifications (✅ DONE)
- [ ] Create `PAID-COMPONENTS-ANALYSIS.md` (✅ DONE)
- [ ] Create `EXECUTIVE-SUMMARY.md` (✅ DONE)
- [ ] Complete spec 003 implementation (replace frontend packages)

### Post-Implementation

- [ ] Update main `README.md` with "Building the Action Server" section
- [ ] Add template `ENTERPRISE-NOTICE.md` files to data-access templates
- [ ] Update `CONTRIBUTING.md` with "No credentials needed" messaging
- [ ] Create `ARCHITECTURE.md` with system diagram
- [ ] Update VS Code extension descriptions (marketplace + open-vsx)

### Documentation

- [ ] Restructure docs with enterprise distinction
- [ ] Add `🔒 Enterprise` markers to relevant guides
- [ ] Create "Do I Need Enterprise?" decision guide
- [ ] Add architecture diagrams

### CI/CD

- [ ] Add "Verify Open-Source Build" workflow
- [ ] Add template syntax validation
- [ ] Update existing workflows to not require credentials
- [ ] Add build verification to PR checks

---

## Success Metrics

After implementation, verify:

1. **External contributor experience**:
   - ✅ Clone repo, build frontend, run Action Server without ANY credentials
   - ✅ All CI builds pass without secrets
   - ✅ Clear documentation on what works open-source

2. **Enterprise customer clarity**:
   - ✅ Clear understanding of which features require subscription
   - ✅ Easy path from open-source trial to enterprise purchase
   - ✅ Contact information prominently displayed

3. **Maintainer burden**:
   - ✅ Fewer "can't build" issues
   - ✅ Easier external PR validation
   - ✅ Clear scope boundaries for contributions

---

**Created**: 2025-10-04  
**Status**: Ready for implementation  
**Dependencies**: Spec 003 completion
