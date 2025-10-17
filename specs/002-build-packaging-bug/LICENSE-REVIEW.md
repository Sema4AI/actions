# License Review: Vendored Design System Packages

**Date**: October 3, 2025  
**Feature**: Remove Private Package Dependencies from Build  
**Reviewed By**: Automated Documentation

## Summary

This document reviews the licensing compliance for the three vendored design system packages included in this repository.

## Vendored Packages

The following packages are vendored in `action_server/frontend/vendored/`:

1. **@sema4ai/components** v0.1.1
2. **@sema4ai/icons** v0.1.2
3. **@sema4ai/theme** v0.1.1-RC1

## License Information

### All Packages

**License**: "SEE LICENSE IN LICENSE"  
**Owner**: Sema4.ai, Inc.  
**Status**: ✅ **Proprietary - Internal Use**

All three packages are:
- **Owned by Sema4.ai, Inc.** (the same organization that owns this repository)
- **Licensed for internal use** within Sema4.ai projects
- **Not third-party dependencies** (no external licensing concerns)

## License Files

Each vendored package directory contains its own LICENSE file:
- `action_server/frontend/vendored/components/LICENSE`
- `action_server/frontend/vendored/icons/LICENSE`
- `action_server/frontend/vendored/theme/LICENSE`

## Third-Party Dependencies

None of the vendored packages introduce problematic third-party dependencies:

- All packages are **compiled/bundled** before vendoring
- No external dependencies are vendored alongside the packages
- Standard npm dependencies (React, etc.) remain in package.json as usual

## Constitutional Compliance

This vendoring approach satisfies **Constitution V: Vendored Builds**:

> "When vendoring is necessary, the repository MUST document:
> - The source of the vendored code
> - The reason for vendoring
> - The license of the vendored code
> - A checksum or signature for verification"

✅ **Source**: Documented in manifest.json (`source` field)  
✅ **Reason**: Documented in multiple places (README, CONTRIBUTING, quickstart)  
✅ **License**: Documented in manifest.json and individual LICENSE files  
✅ **Checksum**: SHA256 checksums in manifest.json, verified by CI

## Redistribution

**Important**: The vendored packages are included in this repository to enable building, but they remain proprietary to Sema4.ai, Inc.

- ✅ **Internal use**: Permitted for Sema4.ai projects and contributors
- ✅ **Building from source**: Permitted for external contributors
- ❌ **Redistribution**: Not permitted without explicit permission
- ❌ **Use in other projects**: Not permitted without explicit permission

## Verification

License compliance can be verified by:

1. **Checking manifest.json**:
   ```bash
   cat action_server/frontend/vendored/manifest.json | jq '.packages[] | {name: .source, license: .license}'
   ```

2. **Reading individual LICENSE files**:
   ```bash
   cat action_server/frontend/vendored/components/LICENSE
   ```

3. **Running integrity tests** (includes license checks):
   ```bash
   cd action_server
   pytest tests/action_server_tests/test_vendored_integrity.py -v
   ```

## Risks and Mitigations

### Risk: License Violation
**Mitigation**: All packages are Sema4.ai-owned, eliminating external license concerns.

### Risk: Unauthorized Redistribution
**Mitigation**: 
- LICENSE files in each package clearly state proprietary nature
- Repository README and CONTRIBUTING.md include usage restrictions
- Manifest notes indicate packages are for internal use

### Risk: Third-Party Dependencies
**Mitigation**:
- Packages are pre-compiled/bundled
- No third-party code is vendored
- Standard dependencies remain in package.json (managed by npm)

## Sign-off

**Approval**: Automated documentation based on Constitutional requirements  
**Notes**: All packages are Sema4.ai-owned proprietary software  
**Compliance Status**: ✅ **APPROVED**

## Future Reviews

This license review should be updated when:
- New packages are vendored
- Package versions are updated (automated monthly check)
- Licensing terms change for any vendored package
- Constitutional requirements are updated

## Related Documentation

- [Constitution V: Vendored Builds](.specify/memory/constitution.md)
- [Vendored Packages README](../../action_server/frontend/vendored/README.md)
- [Repository Size Impact](./REPOSITORY-SIZE.md)
- [Build Contract](./contracts/build-contract.md)
