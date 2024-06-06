![Sema4ai](./docs/include/header.svg)

<samp>[Docs](https://robocorp.com/docs) | [Blog](https://medium.com/sema4-ai) | [Examples](https://github.com/sema4ai/cookbook) | [CodeGen](https://chat.robocorp.com) | [Slack](https://sema4ai-users.slack.com/) | [Youtube](https://www.youtube.com/@Robocorp) | [𝕏](https://twitter.com/sema4ai)</samp>

[![PyPI - Version](https://img.shields.io/pypi/v/sema4ai-actions?label=sema4ai-actions&color=%23733CFF)](https://pypi.org/project/sema4ai-actions)
[![PyPI - Version](https://img.shields.io/pypi/v/sema4ai-action-server?label=sema4ai-action-server&color=%23733CFF)](https://pypi.org/project/sema4ai-action-server)
[![GitHub issues](https://img.shields.io/github/issues/sema4ai/actions?color=%232080C0)](https://github.com/sema4ai/actions/issues)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> **NOTE:**  
> This project started as Robocorp Action Server, and is currently being migrated under Sema4.ai organization. You will still likely find links to Robocorp resources. It's all the same company!

# Build Semantic Actions that connect AI Agents with the real-world - all in 🐍 Python.

Sema4.ai is the easiest way to extend the capabilities of AI agents, assistants and copilots with custom actions, written in Python. Create and deploy tools, skills, loaders and plugins that securely connect any AI Assistant platform to your data and applications.

Sema4.ai Action Server makes your Python scripts compatible with e.g. OpenAI's [custom GPTs](https://chat.openai.com/gpts/editor), [LangChain](https://python.langchain.com/docs/integrations/toolkits/robocorp/) and [OpenGPTs](https://github.com/langchain-ai/opengpts) by automatically creating and exposing an API based on function declaration, type hints and docstrings. Just add `@action` and start!

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./docs/include/sema4ai-flow-dark_1x.webp">
  <img alt="Text changing depending on mode. Light: 'So light!' Dark: 'So dark!'" src="./docs/include/sema4ai-flow-light_1x.webp">
</picture>

---

<div id="quickstart"></div>

# 🏃‍♂️ Quickstart

There are two main ways using the Action Server: use the command line, or with our VS Code extension. This section gets you going!

<details open>
<summary><b>CLI For macOS</b></summary>

```sh
brew update
brew install sema4ai/tools/action-server
```

</details>

<details>
<summary><b>CLI For Windows</b></summary>

```sh
# Download Sema4.ai Action Server
curl -o action-server.exe https://cdn.sema4.ai/action-server/releases/latest/windows64/action-server.exe
```

You can download/move the executable into a folder that is in your `PATH`, or you can [add the folder into PATH](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/) so that you can call `action-server` wherever you are.

</details>

<details>
<summary><b>CLI For Linux</b></summary>

```sh
# Download Sema4.ai Action Server
curl -o action-server https://cdn.sema4.ai/action-server/releases/latest/linux64/action-server
chmod a+x action-server

# Add to PATH or move to a folder that is in PATH
sudo mv action-server /usr/local/bin/
```

</details>

<details>
<summary><b>Robocorp Code extension for VS Code</b></summary>

> **NOTE:**  
> Robocorp VS Code extension is in the process to be renamed to Sema4.ai extension.

After installing [Robocorp Code extension from the VS Code Markeplace](https://marketplace.visualstudio.com/items?itemName=robocorp.robocorp-code), open the Command Palette (`Command-Shift-P` or `Ctrl-Shift-P`) and select `Robocorp: Create Action Package`. This will bootstrap a new project. You can then run/debug indvidual Actions from the Extension's sidebar, or start the Action Server.

![github-extension](https://github.com/robocorp/robocorp/assets/40179958/d53000bf-558e-48a7-bb30-4610b9bf24c5)

</details>

<br/>

Bootstrap a new project from a template. You’ll be prompted for the name of the project:

```sh
action-server new
```

Navigate to the freshly created project folder and start the server:

```sh
cd my-project
action-server start --expose
```

👉 You should now have an Action Server running locally at: http://localhost:8080, to open the web UI.

👉 Using the --expose -flag, you also get a public internet-facing URL (something like _twently-cuddly-dinosaurs.sema4ai.link_) and an API key. These are the details that you need to configure your AI Agent.

Head over to [Action Server docs](./action_server/README.md) for more.

---

<div id="python-action"></div>

# What makes a Python function an⚡️Action?

1️⃣ `package.yaml` file that describes the set of Actions your are working on, and defines up your **Python environment and dependencies**:

```yaml
name: Package name
description: Action package description
documentation: https://github.com/...

dependencies:
  conda-forge:
    - python=3.10.12
    - uv=0.1.37
  pypi:
    - sema4ai-actions=0.3.1
    - pytz=2024.1
```

<details>
  <summary>🙋‍♂️ "Why not just pip install...?"</summary>

Think of this as an equivalent of the requirements.txt, but much better. 👩‍💻 With `package.yaml` you are not just controlling your PyPI dependencies, you control the complete Python environment, which makes things repeatable and easy.

👉 You will probably not want run the Actions just on your machine, so by using `package.yaml`:

- You can avoid `Works on my machine` -cases
- You do not need to manage Python installations on all the machines
- You can control exactly which version of Python your automation will run on
  - ..as well as the pip version to avoid dependency resolution changes
- No need for venv, pyenv, ... tooling and knowledge sharing inside your team.
- Define dependencies in package.yaml let our tooling do the heavy lifting.
- You get all the content of [conda-forge](https://prefix.dev/channels/conda-forge) without any extra tooling

> The environment management is provided by another open-source project of ours, [RCC](https://github.com/robocorp/rcc).

</details>
<br/>

2️⃣ [@action decorator](./actions) that determines the **action entry point** and [Type hints and docstring](./actions#describe-your-action) to let AI agents know **what the Action does** in natural language.

```py
@action
def greeting(name: str) -> str:
    """
    Greets the user

    Args:
        name (str): The user name

    Returns:
        str: Final user greeting
    """
```

---

<div id="connect-gpt"></div>

## Connect with OpenAI GPTs Actions

Once you have started the Action Server with `--expose` flag, you’ll get a URL available to the public, along with the authentication token. The relevant part of the output from the terminal looks like this, of course with your own details:

```sh
...
Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
🌍 URL: https://seventy-six-helpless-dragonflies.sema4ai.link
🔑 Add following header api authorization header to run actions: { "Authorization": "Bearer xxx_xxx" }
```

<h3 id="actions-video" align="center">
  <a href="https://www.youtube.com/watch?v=7aq6QDCaUmA">
    👉 Example video in Youtube 👈
  </a>
</h3>

Adding the Action Server-hosted AI Action to your custom GPT is super simple: basically just navigate to “Actions” section of the GPT configuration, add the link to import the actions, and **Add Authentication** with **Authentication method** set to _“API key”_ and **Auth Type** to _“Bearer”_.

> **TIP:**  
> Use the `@action(is_consequential=False)` flag to avoid the user needing to accept the action execution separately each time on your GPT.

<div id="langchain"></div>

## Add Action Server as a Toolkit to [🦜️🔗 LangChain](https://github.com/robocorp/langchain)

> **NOTE:**  
> This section is still under Robocorp, but pending rename to Sema4.ai soon.

Sema4.ai Action Server has everything needed to connect it to your Langchain AI app project. The easiest way is to start with the template provided in the Langchain project. Here’s how to do it:

```sh
# Install LangChain cli tool if not already there
pip install langchain-cli

# Create a new LangChain app using Action Server template
langchain app new my-awesome-app --package robocorp-action-server
```

Then define the route inside the created `./my-awesome-app/app/server.py` file:

```diff
from langserve import add_routes
+ from robocorp_action_server import agent_executor as action_server_chain

# Edit this to add the chain you want to add
- add_routes(app, NotImplemented)
+ add_routes(app, action_server_chain, path="/robocorp-action-server")
```

After the setup make sure you have:

- An environment variable `OPENAI_API_KEY` with your OpenAI API key set
- You have a running Action Server at http://localhost:8080

Finally, inside the project directory `./my-awesome-app` spin up a LangServe instance directly by:

```sh
langchain serve
```

After running the steps above, you’ll have a Playground available at http://127.0.0.1:8000/robocorp-action-server/playground/ where you can test your Actions with an AI agent.

**Want to build your own thing?** Adding your Robocorp AI Actions to a Langchain project is as easy as the code below. Just remember to change the URL of the Action Server if you are not running both the Action Server and Langchain app on the same machine.

```py
from langchain_robocorp import ActionServerToolkit

# Initialize Action Server Toolkit
toolkit = ActionServerToolkit(url="http://localhost:8080")
tools = toolkit.get_tools()
```

---

<div id="why-actions"></div>

## Why use Sema4.ai AI Actions

- ❤️ “when it comes to automation, the (ex)Robocorp suite is the best one” _[/u/disturbing_nickname](https://old.reddit.com/r/rpa/comments/18qqspn/codeonly_rpa_pet_project/kez2jds/?context=3)_
- ❤️ “(ex)Robocorp seems to be a good player in this domain” _[/u/thankred](https://old.reddit.com/r/rpa/comments/18r5gne/recommendation_for_open_source_or_somewhat_less/kez6aw6/?context=3)_
- ❤️ “Since you know Python, check out (ex)Robocorp. Their product is crazy good.” _[/u/Uomis](https://old.reddit.com/r/rpa/comments/18n5sah/c/ke8qz2g?context=3)_

Sema4.ai stack is hands down the easiest way to give AI agents more capabilities. It’s an end-to-end stack supporting every type of connection between AI and your apps and data. You are in control where to run the code and everything is built for easiness, security, and scalability.

- 🔐 **Decouple AI and Actions that touches your data/apps** - Clarity and security with segregation of duties between your AI agent and code that touches your data and apps. Build `@action` and use from multiple AI frameworks.
- 🏎️ **Develop Actions faster with Sema4.ai's `robocorp` automation libraries** - [Robocorp libraries](https://github.com/robocorp/robocorp) and the Python ecosystem lets you act on anything - from data to API to Browser to Desktops.
- 🕵️ **Observability out of the box** - Log and trace every `@action` run automatically without a single `print` statement. _Pro tip: connect [LangSmith](https://www.langchain.com/langsmith) traces with Action logs!_
- 🤯 **No-pain Python environment management** - Don't do [this](https://xkcd.com/1987/). Sema4.ai manages a full Python environment for your actions with ease.
- 🚀 **Deploy with zero config and infra** - One step deployment, and you'll be connecting your `@action` to AI apps like Langchain and OpenAI GPTs in seconds.

<div id="inspiration"></div>

## Inspiration

Check out these example projects for inspiration.

- 🐣 [Simplest possible AI Action](https://github.com/Sema4AI/cookbook/tree/main/actions/simple-greeter)
- 🤡 [Get a random joke or jokes per theme. Showcases how easy it is to work with APIs.](https://github.com/Sema4AI/cookbook/tree/main/actions/api-jokes)
- 🕸️ [Open a local Playwright browser and make some Google searches.](https://github.com/Sema4AI/cookbook/tree/main/actions/browser-google)
- 🖥️ [Securely fetch contents of `.txt` and `.pdf` files from your local machine's folder in real time.](https://github.com/Sema4AI/cookbook/tree/main/actions/desktop-files)
- 📝 [Read and write with local Excel file.](https://github.com/Sema4AI/cookbook/tree/main/actions/excel-local)

Build more `@actions` and be awesome! We'd love to hear and see what have you built. Join our [Slack community](https://sema4ai-users.slack.com/) to share your work.

<div id="contribute"></div>

## Contributing and issues

> ⭐️ First, please star the repo - your support is highly appreciated!

- 🚩 Issues – our [GitHub Issues](https://github.com/Sema4AI/actions/issues) is kept up to date with bugs, improvements, and feature requests
- 🙋 Help - you are welcome to [join our Community Slack](https://sema4ai-users.slack.com/) if you experience any difficulty getting setup
- 🌟 Contribution and recognition – Start [here](https://github.com/Sema4AI/actions/blob/master/CONTRIBUTING.md), [PR's](https://github.com/Sema4AI/actions/pulls) are welcome!
- 🔐 Refer to our [Security policy](https://sema4.ai/.well-known/security.txt) for details

### Contributors

![Contributors](https://contrib.nn.ci/api?repo=sema4ai/actions)
