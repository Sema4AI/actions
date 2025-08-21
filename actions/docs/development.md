# Development guides

## Requires

- Python 3.12 or 3.13
- invoke==2.2.0 or later

## Develop

`inv -l`:
- `inv install` : Get dependencies
  - `inv install --update` : Update lock file (CVE updates)
- `inv build`
- `inv test`
- `inv set-version a.b.c`: Update the library version numbers
- `inv check-all` : Run all checks

## Publish
- `inv set-version a.b.c`: Update the library version numbers
- `inv make-release` : Create a release tag
- Publish to PyPI only via GHA: https://github.com/Sema4AI/actions/blob/master/.github/workflows/actions_release.yml
  - Correct tag triggers GHA runs  
