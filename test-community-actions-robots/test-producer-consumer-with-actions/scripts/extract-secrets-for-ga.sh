#!/bin/bash

# Script to extract specific configurations and prepare them for GitHub Actions
# Outputs files to be used as content for GitHub Actions secrets.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VERBOSE=false
OUTPUT_DIR="github_actions_secret_files" # Default output directory

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Extracts specific configurations and prepares them as files for GitHub Actions secrets."
    echo "The output files will be placed in the \'$OUTPUT_DIR\' directory."
    echo ""
    echo "OPTIONS:"
    echo "  -d, --output-dir DIR      Output directory for secret files (default: $OUTPUT_DIR)"
    echo "  -v, --verbose             Enable verbose output (includes an example GitHub Actions workflow)"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "This script will generate:"
    echo "  - $OUTPUT_DIR/KUBECONFIG_DATA: Base64 encoded kubeconfig."
    echo "  - $OUTPUT_DIR/ARC_PRIVATE_KEY: Base64 encoded content of the latest \'*.private-key.pem\' file."
    echo ""
    echo "These filenames match the secret names used in \'.github/workflows/deploy-arc.yaml\'."
}

# Function to log messages
log() {
    local level=$1
    shift
    local message="$*"
    
    case $level in
        INFO)
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        DEBUG)
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "${BLUE}[DEBUG]${NC} $message"
            fi
            ;;
    esac
}

# Function to check if required tools are installed
check_dependencies() {
    log DEBUG "Checking dependencies..."
    local missing_tools=()
    if ! command -v base64 &> /dev/null; then missing_tools+=("base64"); fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log ERROR "Missing required tools: ${missing_tools[*]}"
        log INFO "Please install the missing tools and try again."
        exit 1
    fi
    log DEBUG "All dependencies are available."
}

# Function to show example GitHub Actions workflow
show_example_workflow() {
    cat << EOF

# Example GitHub Actions workflow using these secrets:
# (based on .github/workflows/deploy-arc.yaml)

name: Deploy ARC Runner

on:
  push:
    branches:
      - main
    paths:
      - \'repos/fetch-repos/values.yaml\'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Kubeconfig
        run: |
          mkdir -p \\$HOME/.kube
          echo "\\${{ secrets.KUBECONFIG_DATA }}" | base64 -d > \\$HOME/.kube/config
          log DEBUG "Kubeconfig created at \\$HOME/.kube/config"
          kubectl get nodes # Test command
        env:
          KUBECONFIG_DATA: \\${{ secrets.KUBECONFIG_DATA }}

      - name: Create ARC Private Key file from secret
        run: |
          # The filename must match what install-upgrade-arc.sh expects or can find.
          echo "\\${{ secrets.ARC_PRIVATE_KEY }}" | base64 -d > arc-private-key.pem
          log DEBUG "arc-private-key.pem created from secret."
        env:
          ARC_PRIVATE_KEY: \\${{ secrets.ARC_PRIVATE_KEY }}
      
      - name: Set up Helm
        uses: azure/setup-helm@v4
        with:
          version: \'latest\'

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: \'latest\'

      - name: Run install script
        run: |
          chmod +x scripts/install-upgrade-arc.sh
          ./scripts/install-upgrade-arc.sh fetch-repos
EOF
}

# Main function to extract targeted secrets for GitHub Actions
extract_targeted_secrets() {
    mkdir -p "$OUTPUT_DIR"
    log INFO "Secret files will be created in: $(pwd)/$OUTPUT_DIR/"

    # 1. Kubeconfig
    log INFO "Attempting to extract Kubeconfig..."
    local kubeconfig_path_default="$HOME/.kube/config"
    local kubeconfig_path_vscode="/home/vscode/.kube/config"
    local kubeconfig_path_env="\${KUBECONFIG:-}"
    local k3s_kubeconfig_path="/etc/rancher/k3s/k3s.yaml"
    local final_kubeconfig_path=""

    log DEBUG "Checking for kubeconfig at: $kubeconfig_path_env, $kubeconfig_path_default, $kubeconfig_path_vscode, $k3s_kubeconfig_path"

    if [[ -n "$kubeconfig_path_env" && -f "$kubeconfig_path_env" ]]; then
        final_kubeconfig_path="$kubeconfig_path_env"
        log DEBUG "Using KUBECONFIG environment variable: $final_kubeconfig_path"
    elif [[ -f "$kubeconfig_path_default" ]]; then
        final_kubeconfig_path="$kubeconfig_path_default"
        log DEBUG "Using default kubeconfig: $final_kubeconfig_path"
    elif [[ -f "$kubeconfig_path_vscode" ]]; then
        final_kubeconfig_path="$kubeconfig_path_vscode"
        log DEBUG "Using vscode home kubeconfig: $final_kubeconfig_path"
    elif [[ -f "$k3s_kubeconfig_path" ]]; then
        final_kubeconfig_path="$k3s_kubeconfig_path"
        log DEBUG "Using k3s kubeconfig: $final_kubeconfig_path"
    fi

    if [[ -n "$final_kubeconfig_path" && -f "$final_kubeconfig_path" ]]; then
        if base64 -w 0 "$final_kubeconfig_path" > "$OUTPUT_DIR/KUBECONFIG_DATA"; then
            log INFO "Successfully created $OUTPUT_DIR/KUBECONFIG_DATA"
            log INFO "In GitHub Actions, create a secret named KUBECONFIG_DATA with the content of this file."
        else
            log ERROR "Failed to create $OUTPUT_DIR/KUBECONFIG_DATA from $final_kubeconfig_path"
        fi
    else
        log WARN "Kubeconfig file not found. Searched KUBECONFIG env, $HOME/.kube/config, /home/vscode/.kube/config, and /etc/rancher/k3s/k3s.yaml. Skipping KUBECONFIG_DATA."
    fi
    echo "" # Newline for readability

    # 2. ARC Private Key
    log INFO "Attempting to process ARC Private Key..."
    local pem_file
    pem_file=$(find . -maxdepth 1 -name '*.private-key.pem' -print -quit)
    local secret_yaml="pre-defined-secret.yaml"
    
    if [[ -f "$pem_file" ]]; then
        log DEBUG "Found PEM file: $pem_file"
        if base64 -w 0 "$pem_file" > "$OUTPUT_DIR/ARC_PRIVATE_KEY"; then
            log INFO "Successfully created $OUTPUT_DIR/ARC_PRIVATE_KEY from PEM file"
            log INFO "In GitHub Actions, create a secret named ARC_PRIVATE_KEY with the content of this file."
        else
            log ERROR "Failed to create $OUTPUT_DIR/ARC_PRIVATE_KEY from $pem_file"
        fi
    elif [[ -f "$secret_yaml" ]]; then
        log DEBUG "Found pre-defined-secret.yaml, extracting private key..."
        # Extract the base64-encoded private key from the secret yaml
        if awk '/github_app_private_key:/{print $2}' "$secret_yaml" > "$OUTPUT_DIR/ARC_PRIVATE_KEY"; then
            log INFO "Successfully created $OUTPUT_DIR/ARC_PRIVATE_KEY from pre-defined-secret.yaml"
            log INFO "In GitHub Actions, create a secret named ARC_PRIVATE_KEY with the content of this file."
        else
            log ERROR "Failed to extract private key from $secret_yaml"
        fi
    else
        log WARN "Neither PEM file nor pre-defined-secret.yaml found in $(pwd)."
        log WARN "One of these files is required for the ARC_PRIVATE_KEY GitHub Action secret."
    fi
    echo ""

    log INFO "Secret file generation process finished."
    log INFO "Review the files in \'$OUTPUT_DIR\' and add their contents as secrets in your GitHub repository:"
    log INFO "Go to: Repository Settings > Secrets and variables > Actions > New repository secret"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log ERROR "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log INFO "GitHub Actions Secret File Generator"
    log INFO "Output directory: $(pwd)/$OUTPUT_DIR"
    log INFO ""
    
    check_dependencies
    extract_targeted_secrets
    
    if [[ "$VERBOSE" == "true" ]]; then
        show_example_workflow
    fi
    
    log INFO "Done! 🚀"
}

# Run main function
main "$@"
