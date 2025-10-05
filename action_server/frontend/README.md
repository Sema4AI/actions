# sema4ai-server-frontend

## Dual-Tier Build System

This frontend supports two build tiers:
- **Community**: Open-source build using Radix UI + Tailwind CSS (no proprietary dependencies)
- **Enterprise**: Internal build using @sema4ai design system packages

### Package Manifest Precedence

The build system uses tier-specific package manifests:
- `package.json.community` - Community tier dependencies (Radix UI, Tailwind, OSI-licensed packages only)
- `package.json.enterprise` - Enterprise tier dependencies (includes @sema4ai/* packages from vendored/)
- `package.json` - Active manifest (copied from tier-specific file during build)

**Important**: Do not manually edit `package.json`. Always edit the tier-specific files (`package.json.community` or `package.json.enterprise`).

## Installation

Install dependencies:

```
npm install
```

## Development

1. Start the dev server:

```
npm run dev
```

3. Open your browser at http://localhost:8080

## Production

To build the production code, run:

```
npm run build
```
