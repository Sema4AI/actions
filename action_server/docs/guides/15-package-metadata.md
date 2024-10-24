# Collecting metadata from an Action Package:

To collect metadata from a given Action Package (which must be extracted in the
filesystem), it's possible to run:

`action-server package metadata`

By doing so it'll write to `stdout` the metadata from the `Action Package`
(in version `0.2.0` this only includes one `openapi.json` entry with the
`openapi.json` contents, but it's expected that this will have more information
in the future).

Note: logging may still be written to `stderr` and if the process returns with
a non-zero value the `stderr` should have information on what failed.

From `Action-server` `0.3.0` onwards, data on the expected secrets is also available
in the returned metadata.

The full structure given in the output is something as:

```yaml
openapi.json: <OpenAPI Contents>

metadata: # Note: optional as no additional metadata may be needed
  name: <action-package-name>
  description: <action-package-description>
  action_package_version: <action-package-version>
  metadata_version: "2"
  secrets: # Note: optional as secrets may not be there
    <url-for-secret>:
      action: <action-name>
      actionPackage: <action-package-name>
      secrets:
        <secret-name>:
          description: <secret description -- only available when used with sema4ai-actions 0.5.0 onwards>
          type: Secret
    <url-for-oauth2-secret>:
      action: <action-name>
      actionPackage: <action-package-name>
      secrets:
        <oauth2-secret-name>:
          description: <secret description -- only available when used with sema4ai-actions 0.5.0 onwards>
          type: OAuth2Secret
          provider: <oauth2-provider-name>
          scopes: <list of scopes>
```

Changes:

metadata_version:

- "1":
  - Initial structure with:
    - `openapi.json`
    - `metadata`
      - `name`
      - `description`
- "2":
  - Support for:
    - `metadata_version`
    - `action_package_version`
    - `metadata`
      - `secrets`
