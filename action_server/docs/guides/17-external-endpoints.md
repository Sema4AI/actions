# Configuring external endpoints

Depending on where the `Action Server` will be deployed, it might be necessary to make outgoing requests to other services.

For example, an action might need to make requests to google maps or open weather map APIs, etc.

In tightly controlled environments, firewalls might block such requests, in which case it's be important that
action packages specify which external endpoints need to be accessed.

For this purpose, it's possible to add an `external-endpoints` section to the `package.yaml` file, so that when
an action package is deployed in the action server, the appropriate rules are applied to the firewall.

### Example:

```yaml
external-endpoints:
  - name: "OpenWeatherMap"
    description: "Accesses OpenWeatherMap to retrieve daily weather forecast."
    additional-info-link: "https://openweathermap.org/api/one-call-3"
    rules:
      - host: "*.openweathermap.org"
        port: 443
  - name: "GoogleMaps"
    description: "Accesses GoogleMaps to retrieve daily weather forecast."
    additional-info-link: "https://maps.google.com"
    rules:
      - host: "maps.google.com"
        port: 443
```

### Description of the fields

- `name`: The name of the service the access is to e.g. ServiceNow, Sharepoint.

- `description`: Details on why the action needs the access to the service.

- `additional-info-link`: Optional link to docs on how to find the endpoint rules for the service.

- `rules` (list) optional

  - `host`: hostname url in a `firewall rule format` e.g. `\*.openweathermap.org`, `maps.google.com`

  - `port`: optional port number (needs to be a valid port number)

Note: the `host` and `port` fields are optional and are mostly provided as defaults during the
deployment (where the Admin will be able to actually set the rules as needed).
