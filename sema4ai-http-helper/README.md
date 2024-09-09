# README

## Overview

This repository provides functionality for handling HTTP requests with support for SSL/TLS contexts, and file downloading with resumable capabilities. It includes a variety of public methods for downloading and managing files via HTTP, supporting partial downloads, retries, and custom SSL contexts.

### Key Features:
- Custom SSL context creation with optional legacy server support.
- HTTP request methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) using `urllib3`.
- Resumable file downloads with retry logic and error handling.
- Support for making downloaded files executable.

## Public Classes and Functions

### 1. **HTTP Request Functions**
   These functions handle different HTTP request methods and return the response from `urllib3`:
   - `get(url, **kwargs)`: Sends a GET request.
   - `post(url, **kwargs)`: Sends a POST request.
   - `put(url, **kwargs)`: Sends a PUT request.
   - `patch(url, **kwargs)`: Sends a PATCH request.
   - `delete(url, **kwargs)`: Sends a DELETE request.


### 3. **Function: `build_ssl_context(protocol: int = None, *, enable_legacy_server_connect: bool = False) -> ssl.SSLContext`**
   Creates an SSL context for use with `urllib3` requests that uses the `truststore` library. Supports enabling legacy server connections.

   **Parameters:**
   - `protocol`: The SSL protocol to be used.
   - `enable_legacy_server_connect`: Enables support for legacy servers.

   **Returns:** An SSL context with the appropriate configurations.


### 4. **Function: `download_with_resume(url: str, target: str | Path, **kwargs) -> DownloadResult`**
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
   - `resume_existing`: Whether to resume downloading if a partial file exists.

   **Returns:** A `DownloadResult` object containing the download status and file path.

### 5. **Class: `DownloadResult`**
   A `NamedTuple` that stores the results of a download operation. It contains:
   - `status`: The final status of the download (from the `DownloadStatus` enum).
   - `path`: The path to the downloaded file.

### 6. **Function: `partial_file_exists(target: str | Path) -> bool`**
   Helper function to check if a partial download file exists for a given target path.

   **Parameters:**
   - `target`: The file path to check for an existing partial file.

   **Returns:** A boolean indicating if a partial file exists.


## Dependencies
This repository uses the following external libraries:
- `urllib3`: For making HTTP requests.
- `truststore`: For SSL context creation and management.

## Usage Example

```python
from pathlib import Path
from sema4ai_http import download_with_resume

url = "https://example.com/file.zip"
target = Path("/path/to/save/file.zip")

result = download_with_resume(url, target)

print(f"Download status: {result.status}")
print(f"File saved to: {result.path}")
```
