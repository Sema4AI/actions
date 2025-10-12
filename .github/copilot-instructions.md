# actions Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-12

## Active Technologies
- Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation + Vite 6.1.0, React 18.2.0, design system packages to be vendored (002-build-packaging-bug)
- Node.js 20.x LTS / TypeScript 5.3.3 (frontend), Python 3.11.x (backend/build automation) + Vite 6.1.0, React 18.2.0, Radix UI + Tailwind CSS (community), @sema4ai/* design system (enterprise), invoke (build tasks), PyInstaller (backend packaging) (003-open-core-build)
- File-based (vendored packages in `action_server/frontend/vendored/`, build artifacts) (003-open-core-build)
- TypeScript 5.3.3, React 18.2.0 + Vite 6.1.0 (build), Radix UI 1.0.x (headless components), Tailwind CSS 3.4.1 (styling), class-variance-authority 0.7.0 (variants), clsx 2.1.0 + tailwind-merge 2.2.0 (className utility), React Router DOM 6.21.3 (navigation), TanStack Query 5.28.0 (data fetching) (004-community-ui-enhancement)
- N/A (frontend only, no persistence layer) (004-community-ui-enhancement)

## Project Structure
```
src/
tests/
```

## Commands

### Python (Backend)
```bash
# Run tests
cd action_server && pytest
cd actions && pytest
cd common && pytest

# Lint code
ruff check .

# Build tasks (invoke)
inv --list  # Show all available tasks
```

### Frontend Build (Node.js + TypeScript)
```bash
# Community tier (open-source, no credentials required)
cd action_server && inv build-frontend --tier=community
# OR use alias
cd action_server && inv build-frontend-community

# Enterprise tier (requires NPM_TOKEN for private registry)
cd action_server && inv build-frontend --tier=enterprise
# OR use alias
cd action_server && inv build-frontend-enterprise

# Build options
inv build-frontend --tier=community --json  # JSON output for CI
inv build-frontend --tier=community --debug  # Debug build (no minification)
inv build-frontend --tier=community --source=vendored  # Use vendored packages
```

### Artifact Validation
```bash
# Validate built artifacts
cd action_server
python build-binary/artifact_validator.py \
  --artifact=frontend/dist \
  --tier=community \
  --checks=all \
  --json
```

## Code Style
Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation: Follow standard conventions

## Recent Changes
- 004-community-ui-enhancement: Added TypeScript 5.3.3, React 18.2.0 + Vite 6.1.0 (build), Radix UI 1.0.x (headless components), Tailwind CSS 3.4.1 (styling), class-variance-authority 0.7.0 (variants), clsx 2.1.0 + tailwind-merge 2.2.0 (className utility), React Router DOM 6.21.3 (navigation), TanStack Query 5.28.0 (data fetching)
- 003-open-core-build: Added Node.js 20.x LTS / TypeScript 5.3.3 (frontend), Python 3.11.x (backend/build automation) + Vite 6.1.0, React 18.2.0, Radix UI + Tailwind CSS (community), @sema4ai/* design system (enterprise), invoke (build tasks), PyInstaller (backend packaging)
- 002-build-packaging-bug: Added Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation + Vite 6.1.0, React 18.2.0, design system packages to be vendored

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
## Vendored Builds
When present, vendored build artifacts and their manifests will be listed here with the producing CI run link and
short justification. Manual additions about vendored artifacts should be kept between the MANUAL ADDITIONS markers.
