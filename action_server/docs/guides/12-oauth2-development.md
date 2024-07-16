## Configuring OAuth2

In this case, a developer must create an application in the proper service
(say, `google` and `slack`), and fill in the details in the `OAuth2 Settings YAML`.

- On Windows it's default location is `%LOCALAPPDATA%/sema4ai/action-server/oauth2-settings.yaml`.
- On Linux/Mac it's default location is `~/.sema4ai/action-server/oauth2-settings.yaml`.
- It's also possible to specify a different `oauth2-settings.yaml` location in the `start` arguments.

Below is an example showing how to configure it.

Keep in mind that the `devServerInfo` information is only used from VSCode to
launch the action server to collect OAuth2 data.

```yaml
# The "devServerInfo" information is only used to require tokens from VSCode:
#
# This is the server information which will be used to create a server
# which will be used to collect the OAuth2 tokens as needed.
# Note that this is ONLY USED WHEN tokens are requested from 
# a separate application, such as VSCode, as when the action
# server is manually started it'll use host/port provided when
# it was initialized.
devServerInfo:
  redirectUri: "http://localhost:4567/oauth2/redirect"
  # If the redirectUri starts with `https`, ssl information is
  # needed. In this case it's possible to either set `sslSelfSigned`
  # to true to automatically create a self-signed certificate or
  # set the `sslKeyfile` and `sslCertfile` to be used to serve
  # the page.
  #
  # Note: the redirectUri needs to be specified here and in the service.
  # Keep in mind that the port must not be used by any other service
  # in the machine and it must match the format below (where only
  # <protocol> and <port> can be configured, the remainder must be kept as is):
  #
  # <protocol>://localhost:<port>/oauth2/redirect/
  #
  # Disclaimer: if using a self-signed certificate, the browser may complain
  # and an exception needs to be accepted to proceed to the site unless
  # the self-signed certificate is imported in the system.
  sslSelfSigned: false
  sslKeyfile: ""
  sslCertfile: ""

# Details for each provider need to be manually set.
#
# The following providers just require "clientId" and "clientSecret":
# - google, github, slack, and hubspot
#
# The following providers require "server", "clientId" and "clientSecret":
# - microsoft, zendesk
#
# Any other provider besides those also needs to specify
# "server", "tokenEndpoint" and "authorizationEndpoint"
#
# Note: if the "tokenEndpoint"/"authorizationEndpoint" are relative,
# the "server" is prefixed to it to get the absolute version.
google:
  clientId: "XXXX-YYYYYYYYY.apps.googleusercontent.com"
  clientSecret: "XXXXX-yyyyyyyyyyyyyyyy"

slack:
  clientId: "XXXXXXXXXXXX.YYYYYYYYYYY"
  clientSecret: "zzzzzzzzzzzzzzz"

hubspot:
  clientId: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
  clientSecret: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"

microsoft:
  clientId: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
  clientSecret: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
  server: "https://<service.microsoft.com>"

custom:
  clientId: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
  clientSecret: "xxxxxx-yyyyy-zzzz-aaaa-bbbbbbbbbbbbb"
  server: "https://<service.microsoft.com>"
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
redirect uri is added (by default it's `http://localhost:4567/oauth2/redirect/`
note that it should usually not use the same port used to launch the action server
so that there are no conflicts with a running action server instance).

It's possible to use the VSCode command `Sema4.ai: Open OAuth2 Settings` to
create a file in the proper place with the default structure to be filled
(the created file has comments explaining how to configure it -- it's the
same file used by the Action Server explained above).
