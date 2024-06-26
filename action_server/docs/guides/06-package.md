# Building Action Package zip to distribute:

The action server can be used to serve Action Packages, which is a project
containing multiple defined actions (specified by using the `@action` decorator
in `.py` files), with the related metadata (`package.yaml`).

To share these Action Packages the action server has the following command:

`action-server package build`

This will build a `.zip` containing the files from the Action Package. By
default all the files from the Action Package directory are recursively added
to the `.zip`, and it's possible to customize files which shouldn't be added
to the action server by specifying them in the `package.yaml` in the
`packaging/exclude` section (entries are based on the
[glob format](https://docs.python.org/3/library/glob.html).

Example:

```yaml
name: CRM automation

description: Automates dealing with the CRM.

dependencies:
  conda-forge:
    - python=3.10.12
    - pip=23.2.1
    - robocorp-truststore=0.8.0

  pypi:
    - robocorp-actions=0.1.0
    - robocorp=1.4.3
    - pytz=2023.3

packaging:
  exclude:
    - "*.pyc" # Excludes .pyc files anywhere
    - "./devdata/**" # Excludes the `devdata` directory in the current dir
    - "**/secret/**" # Excludes any `secret` folder anywhere
```

Note: using `action-server package build` with the `package.yaml` above will
create a `.zip` named: `crm-automation.zip` in the current directory.

# Documentation for the action package

An action package is expected to have a `README.md` in the root of the folder, right next to the
`package.yaml`.

Note that it's possible to use links and images in the README.md pointing to other files inside the action package.

Example:

- Link syntax: `[link to others readme](./docs/others.md)`
- Image syntax: `![plot image](./images/plot image.png)`

# Icon for the action package

To define an icon for the action package, add a `package.png` in the root of the folder, right next to
the `package.yaml`.

# Extracting zip with Action Package:

To extract the Action Package from the `crm-automation.zip`
previously created, it's possible to use:

`action-server package extract crm-automation.zip --output-dir=v023`

Note: if `--output-dir` is not given, the current directory will be used.

Note: `--override` can be given to override the contents of the directory
without asking for confirmation.

# Collecting metadata from an Action Package:

To collect metadata from a given Action Package (which must be extracted in the
filesystem), it's possible to run:

`action-server package metadata`

By doing so it'll write to `stdout` the metadata from the Action Package
(in version `0.2.0` this only includes one `openapi.json` entry with the
`openapi.json` contents, but it's expected that this will have more information
in the future).

Note: logging may still be written to `stderr` and if the process returns with
a non-zero value the `stderr` should have information on what failed.

From action-server `0.3.0` onwards, data on the expected secrets is also available
in the returned metadata.

The full structure given in the output is something as:

```yaml
openapi.json: <OpenAPI Contents>

metadata: # Note: optional as no additional metadata may be needed
  secrets: # Note: optional as secrets may not be there
    <url-for-secret>:
      action: <action-name>
      actionPackage: <action-package-name>
      secrets:
        <secret-name>:
          description: <secret description -- only available when used with sema4ai-actions 0.5.0 onwards>
          type: Secret
```
