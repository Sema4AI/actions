# HTTP helper library for enterprise networks

## Overview

`sema4ai_http` -library provides HTTPS request handling that works inside enterprise networks that use MITM firewalls/proxies for outbound traffic.

### The Problem:

- Modern firewalls need to track outbound traffic to detect malware
- To track the traffic, the SSL/TLS needs to be terminated on the firewall/proxy
- This means a separate certificate is needed for the internal network HTTPS to function
- These certificates are typically distributed using the OS-specific certificate stores
- Libraries like `requests`, `urllib3`, `aiohttp`,.. do not yet native support the certificate store

👉 In enterprise networks, HTTPS requests without the correct SSL context set will fail, and it is a hassle to get it right.

### The solution

Every outbound HTTPS request needs the correct SSL context, but 95% of HTTPS code is just downloading files and simple GET / POST calls, so we provide a helper library.

We use [truststore](https://pypi.org/project/truststore/) -library to access the certificate stores and `urllib3` to avoid extra dependencies.

The key features of the library are:

- SSL context creation that uses OS certificate store and provided optional SSL legacy renegotiation support.
    - To use the SSL context with other libraries, please refer to the [user guide from truststore](https://truststore.readthedocs.io/en/latest/#user-guide)
- Network profile retrieval for accessing SSL context and proxy configuration.
- HTTPS request methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) using `urllib3`.
- Resumable file downloads with retry logic and error handling.
- Support for making downloaded files executable.

## Usage Examples

### File Download Example

```python
from pathlib import Path
from sema4ai_http import download_with_resume

url = "https://example.com/file.zip"
target = Path("/path/to/save/file.zip")

result = download_with_resume(url, target)

print(f"Download status: {result.status}")
print(f"File saved to: {result.path}")
```

## Documentation

### Functions:

#### 1. HTTPS Request Functions

These functions handle different HTTPS request methods and return the response from `urllib3`:

- `get(url, **kwargs)`: Sends a GET request.
- `post(url, **kwargs)`: Sends a POST request.
- `put(url, **kwargs)`: Sends a PUT request.
- `patch(url, **kwargs)`: Sends a PATCH request.
- `delete(url, **kwargs)`: Sends a DELETE request.

#### 2. Build SSL Context

`build_ssl_context(protocol: int = None, *, enable_legacy_server_connect: bool = False) -> ssl.SSLContext`\*\*

This function creates an SSL context for use with `urllib3` requests that use the `truststore` library. It also supports enabling SSL legacy renegotiation connections.

**Parameters:**

- `protocol`: The SSL protocol to be used.
- `enable_legacy_server_connect`: Enables support for legacy servers.

**Returns:** An SSL context with the appropriate configurations.

#### 3. File download with resume support

`download_with_resume(url: str, target: str | Path, **kwargs) -> DownloadResult`\*\*

Downloads a file from a URL with support for resuming interrupted downloads. This function can also retry downloads multiple times in case of failure and ensures the file is downloaded completely before marking it as done.

**Parameters:**

- `url`: The URL of the file to download.
- `target`: The target path where the file should be saved.
- `headers`: Optional headers for the request.
- `make_executable`: Whether to make the file executable.
- `chunk_size`: The size of the data chunks to be downloaded.
- `poll_manager`: The `urllib3.PoolManager` instance to use.
- `max_retries`: Maximum number of retries for the download.
- `timeout`: Timeout for the request.
- `wait_interval`: Time to wait between retries.
- `overwrite_existing`: Whether to overwrite an existing file.
- `resume_from_existing_part_file`: Whether to resume the download from an existing partial file. Defaults to True.

**Returns:** A `DownloadResult` object containing the download status and file path.

#### 4. Partial file exists

`partial_file_exists(target: str | Path) -> bool`\*\*

A helper function to check if a partial download file exists for a given target path.

**Parameters:**

- `target`: The file path to check for an existing partial file.

**Returns:** A boolean indicating if a partial file exists.

#### 5. Get Network Profile

`get_network_profile() -> NetworkProfile`\*\*

Retrieves the current network profile configuration including SSL context and proxy settings from the system.

**Returns:** A `NetworkProfile` object containing the SSL context and proxy configuration.

### Classes:

#### Network Profile class

`NetworkProfile`

A dataclass that contains network configuration information:

- `ssl_context`: The SSL context configured for the current environment.
- `proxy_config`: The proxy configuration (HTTP, HTTPS, and no_proxy settings).

#### File download result class

`DownloadResult`

A `NamedTuple` that stores the results of a download operation. It contains:

- `status`: The final status of the download (from the `DownloadStatus` enum).
- `path`: The path to the downloaded file.

## Using with 3'rd Party Libraries

### httpx

You can use the `get_network_profile()` method to set up proxy connections with httpx:

```python
from sema4ai_http import get_network_profile
from itertools import chain
import httpx

# Get the network profile which contains SSL context and proxy configuration
network_config = get_network_profile()

# Set up mounts for proxy configuration
mounts: dict[str, httpx.HTTPTransport | None] = {}

for http_proxy in chain(
    network_config.proxy_config.http, network_config.proxy_config.https
):
    mounts[http_proxy] = httpx.HTTPTransport(network_config.ssl_context)

for no_proxy in network_config.proxy_config.no_proxy:
    mounts[no_proxy] = None

# Create httpx client with the configured mounts and SSL context
client = httpx.Client(mounts=mounts, verify=network_config.ssl_context)
```

### Dependencies

This repository uses the following external libraries:

- `urllib3`: For making HTTPS requests.
- [truststore](https://pypi.org/project/truststore/): For SSL context creation and management.