#!/bin/bash
# Wrapper script to launch Chrome via Flatpak for chrome-devtools-mcp

exec flatpak run com.google.Chrome "$@"
