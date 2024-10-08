# Development

## Release process

To release a new version use `inv` commands (in the `/action_server` directory):

- First, check that the `CHANGELOG.md` is updated with the new changes (keep the `## Unreleased` section for the current release).
- `inv set-version <version>`: will set the version and update the `CHANGELOG.md` `## Unreleased` section to have the specified version/current date.
- Commit/get the changes (open a PR, merge it, get the contents locally).
- `inv make-release`: will create a tag and push it to the remote repository (which will in turn trigger the release pipeline).

## Beta releases

If for creating a normal release of version 0.0.1 you would need to create
a tag `sema4ai-action_server-0.0.1`, for creating a beta release you only
need to create a similar tag that ends in `-beta`, so it would be
`sema4ai-action_server-0.0.1-beta`. Pushing this tag will automatically
start a release pipeline that will build and upload to S3 the binaries.
Keep in mind that only one beta version can exist at a time and if you run
the pipeline again, it will overwrite the previous version.

In order to use the beta binaries, you can just download them directly.
For example this is the URL for Windows: `https://cdn.sema4.ai/action-server/beta/windows64/action-server.exe`
The name for the Linux and Mac binaries is just `action-server` and you can just replace
windows64 with linux64 or mac64 for the respective OS's. If you also need to
have a reference of what version was used, you can find the version file at:
`https://cdn.sema4.ai/action-server/beta/version.txt`
