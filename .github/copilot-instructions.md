# actions Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-03

## Active Technologies
- Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation + Vite 6.1.0, React 18.2.0, design system packages to be vendored (002-build-packaging-bug)
- TypeScript 5.3.3, Node.js 20.x (LTS), React 18.2.0 + Vite 6.1.0 (build tool), React 18.2.0, React Router 6.21.3, TanStack Query 5.28.0 (003-build-open-source)
- N/A (frontend-only, no persistent storage) (003-build-open-source)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation: Follow standard conventions

## Recent Changes
- 003-build-open-source: Added TypeScript 5.3.3, Node.js 20.x (LTS), React 18.2.0 + Vite 6.1.0 (build tool), React 18.2.0, React Router 6.21.3, TanStack Query 5.28.0
- 003-build-open-source: Added TypeScript 5.3.3, Node.js 20.x (LTS), React 18.2.0 + Vite 6.1.0 (build tool), React 18.2.0, React Router 6.21.3, TanStack Query 5.28.0
- 002-build-packaging-bug: Added Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation + Vite 6.1.0, React 18.2.0, design system packages to be vendored

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
## Vendored Builds
When present, vendored build artifacts and their manifests will be listed here with the producing CI run link and
short justification. Manual additions about vendored artifacts should be kept between the MANUAL ADDITIONS markers.
