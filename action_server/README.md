# sema4ai-action-server

[Sema4.ai Action Server](https://github.com/sema4ai/actions#readme) is a Python framework designed to provide your Python functions to AI Agents. It works both as an MCP Server (hosting tools, resources and prompts) and also provides an OpenAPI compatible API.

A `tool` or `action` in this case is defined as a Python function (which has inputs/outputs defined), which is served by the `Sema4.ai Action Server`.

The `Sema4.ai Action Server` automatically provides a `/mcp` endpoint for connecting `MCP` clients and also generates an OpenAPI spec for your Python code, enabling different AI/LLM Agents to understand and call your Action. It also manages the Action lifecycle and provides full traceability of what happened during any tool or action call (open the `/runs` endpoint in a browser to see not only inputs and output, but also a full `log.html` with internal details, such as variables and function calls that your Python function executed).

## 1. Install Action Server

Action Server is available as a stand-alone fully signed executable and via `pip install sema4ai-action-server`.

> We recommend the executable to prevent confusion in case you have multiple/crowded Python environments, etc.

#### For macOS

```sh
# Install Sema4.ai Action Server
brew update
brew install sema4ai/tools/action-server
```

#### For Windows

```sh
# Download Sema4.ai Action Server
curl -o action-server.exe https://cdn.sema4.ai/action-server/releases/latest/windows64/action-server.exe

# Add to PATH or move to a folder that is in PATH
setx PATH=%PATH%;%CD%
```

#### For Linux

```sh
# Download Sema4.ai Action Server
curl -o action-server https://cdn.sema4.ai/action-server/releases/latest/linux64/action-server
chmod a+x action-server

# Add to PATH or move to a folder that is in PATH
sudo mv action-server /usr/local/bin/
```

## 2. Run your first MCP tool

```sh
# Bootstrap a new project using this template.
# You'll be prompted for the name of the project (directory):
action-server new

# Start Action Server
cd my-project
action-server start
```

👉 You should now have an Action Server running locally at: [http://localhost:8080](http://localhost:8080), so open that in your browser and the web UI will guide you further.

## What do you need in your Action Package

An `Action Package` is currently defined as a local folder that contains at least one Python file containing an action entry point (a Python function marked with `@action` -decorator from `sema4ai.actions`).

The `package.yaml` file is required for specifying the Python environment and dependencies for your Action ([RCC](https://github.com/joshyorko/rcc/) will be used to automatically bootstrap it and keep it updated given the `package.yaml` contents).

> Note: the `package.yaml` is optional if the action server is not being used as a standalone (i.e.: if it was pip-installed it can use the same python environment where it's installed).

### Bootstrapping a new Action

Start new projects with:

`action-server new`

Note: the `action-server` executable should be automatically added to your python installation after `pip install sema4ai-action-server`, but if for some reason it wasn't pip-installed, it's also possible to use `python -m sema4ai.action_server` instead of `action-server`.

After creating the project, it's possible to serve the actions under the current directory with:

`action-server start`

For example: When running `action-server start`, the action server will scan for existing actions under the current directory, and it'll start serving those.

After it's started, it's possible to access the following URLs:

- `/index.html`: UI for the Action Server.
- `/openapi.json`: Provides the openapi spec for the action server.
- `/docs`: Provides access to the APIs available in the server and a UI to test it.

## Documentation

Explore our [docs](https://github.com/sema4ai/actions/tree/master/action_server/docs) for extensive documentation.

## Changelog

A list of releases and corresponding changes can be found in the [changelog](https://github.com/sema4ai/actions/blob/master/action_server/docs/CHANGELOG.md).
