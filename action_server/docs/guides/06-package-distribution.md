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
[glob format](https://docs.python.org/3/library/glob.html)).

Example:

```yaml
name: CRM automation

description: Automates dealing with the CRM.

dependencies:
  conda-forge:
    - python=3.10.12
    - uv=0.4.19

  pypi:
    - sema4ai-actions=1.0.1
    - robocorp=1.4.3

packaging:
  exclude:
    - "*.pyc" # Excludes .pyc files anywhere
    - "./devdata/**" # Excludes the `devdata` directory in the current dir
    - "**/secret/**" # Excludes any `secret` folder anywhere
```

Note: using `action-server package build` with the `package.yaml` above will
create a `.zip` named: `crm-automation.zip` in the current directory.

Note: A file named `__action_server_metadata__.json` will be added to the root of the zip file,
containing the metadata of the `Action Package` (see: [Package Metadata](./15-package-metadata.md) for more details).

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
