#!/usr/bin/env python
"""
Invoke task wrapper for RCC toolkit.

This script is called by RCC via toolkit.yaml tasks. It changes to the
action_server directory (parent of this script) and runs the invoke task.

Usage (via RCC):
    rcc run -r developer/toolkit.yaml --dev -t build-frontend

Direct usage (for debugging):
    cd developer && python call_invoke.py build-frontend-community
"""
import os
import subprocess
import sys

# Get the action_server directory (parent of this script's directory)
use_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if len(sys.argv) < 2:
    print("Usage: python call_invoke.py <task> [args...]")
    print("\nAvailable tasks can be listed with: invoke --list")
    sys.exit(1)

# Build invoke command with all arguments
task = sys.argv[1]
args = sys.argv[2:] if len(sys.argv) > 2 else []

cmd = ["invoke", task] + args
print(f"Running: {' '.join(cmd)} (in {use_dir})")

sys.exit(subprocess.run(cmd, cwd=use_dir).returncode)
