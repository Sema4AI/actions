## Configuring OAuth2

In this case, a developer must create an application in the proper service
(say, `google` and `slack`), and fill in the details in the `OAuth2 Settings YAML`.

- On Windows it's default location is `%LOCALAPPDATA%/sema4ai/action-server/oauth2_config.yaml`.
- On Linux/Mac it's default location is `~/.sema4ai/action-server/oauth2_config.yaml`.
- It's also possible to specify a different `oauth2_config.yaml` location in the `start` arguments.

Below is an example showing how to configure it.

Keep in mind that the `devServerInfo` information is only used from VSCode to
launch the action server to collect OAuth2 data.

```yaml
formatVersion: "1.0.0"

# OAuth2 configuration for Development
# This configuration is shared by Sema4 Ai tools like Studio, VS Code extension and Action Server

# NOTE: Only edit this file manually if you know you way around OAuth2
oauth2Config:
  # For the localhost development to work the redirect urls must be set when registering the OAuth applications
  # and also known by the applications.
  # For Sema4 Ai tools the valid redirect url list is as follows:
  # - http://localhost:61080/sema4ai/oauth2/
  # - http://localhost:61081/sema4ai/oauth2/
  # - https://localhost:61080/sema4ai/oauth2/
  # - https://localhost:61081/sema4ai/oauth2/
  #
  # We need to have two ports to mitigate potential port collisiont and we need the ´http://´ and `https://`
  # Variants because some OAuth providers demand https even in localhost.
  #
  # !!! If you are creating your own OAuth app you must register these redirect urls !!!

  # Some OAuth providers e.g. Slack require the redirects to only happen to
  # HTTPS addresses.
  # If your company has a shared certicate for this you can add it below.
  #
  # If one is not provided and a provider with `requiresHttps: true` is found,
  # Sema4 Ai tooling creates a set of self-signed certificates and uses them
  #
  # Disclaimer: When using a self-signed certificate, the browser may complain
  # and an exception needs to be accepted to proceed to the site unless
  # the self-signed certificate is imported in the system.

  sslKeyfile: ""
  sslCertfile: ""

  # List supported OAuth providers
  providers:
    # The provider names here are lowercase and reserved word.
    # There are hardcoded features to the names listed here.
    microsoft:
      # This mode uses a validated OAuth app provided and configured by Sema4 Ai
      mode: sema4ai

    slack:
      mode: custom
      name: Slack
      clientId: "xxx"
      clientSecret: "yyy"

    github:
      mode: custom
      name: GitHub
      clientId: ""
      clientSecret: ""

    hubspot:
      mode: custom
      name: HubSpot
      clientId: ""
      clientSecret: ""

    google:
      mode: custom
      name: Google
      clientId: ""
      clientSecret: ""

    zendesk:
      mode: custom
      name: Zendesk
      clientId: ""
      clientSecret: ""
      server: ""
```

Now, with the OAuth2 settings configured, it should be possible to make a
`login` into the needed provider when running the action in the Action Server UI.

## VSCode development

When developing inside of VSCode it's possible to run/debug actions directly
from the `TASK/ACTION PACKAGES` view.

When running an action, it's expected that an `input_<action-name>.json` file
is created and the required inputs for the action are set (so, if a parameter
such as `count` is required the json will have a `count` set in the json).

Starting with `Sema4.ai VSCode Extension 2.2.0`, it's now possible to add
an entry to that input json with `vscode:request:oauth2` which will then
prompt automatically when the action is run to make the OAuth2 login flow
so that the required `access_token` is collected and sent to the action.

The example belows shows a json which will provide a `count` as well as a
`google_secret` with the proper `access_token` received from the user authentication
requesting for the `drive.readonly` and `gmail.send` permissions.

```
{
  "count": 1,
  "vscode:request:oauth2": {
    "google_secret": {
      "type": "OAuth2Secret",
      "scopes": [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/gmail.send"
      ],
      "provider": "google"
    }
  }
}
```

Note that when running the action a browser window will automatically open
for each provider requested in the action.

Also make sure that when registering the OAuth2 client/secret the proper
redirect uris are added ( `http://localhost:61080/sema4ai/oauth2/`, `http://localhost:61081/sema4ai/oauth2/`,
`https://localhost:61080/sema4ai/oauth2/`, `https://localhost:61081/sema4ai/oauth2/`)
note that to use the oauth2 authentication from the action server itself, the url with the port used
by the Action Server must also be registered -- so, for instance, if the default port: `8080` is
used, then a redirect url such as `http://localhost:8080/sema4ai/oauth2/` or  
`https://localhost:8080/sema4ai/oauth2/` must also be added).

It's possible to use the VSCode command `Sema4.ai: Open OAuth2 Settings` to
create a file in the proper place with the default structure to be filled
(the created file has comments explaining how to configure it -- it's the
same file used by the Action Server explained above).
