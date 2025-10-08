#!/bin/bash -e

# Store the script directory path
SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_PATH"

PROJECT_NAME="doc-intel"
RCC_PATH="$SCRIPT_PATH/rcc"
CONDA_YAML="$SCRIPT_PATH/develop.yaml"
ACTIVATE_PATH="$SCRIPT_PATH/activate.sh"

echo

# Get RCC binary based on platform
RCC_URL="https://cdn.sema4.ai/rcc/releases/v20.1.2"
if [[ "$(uname)" == "Darwin" ]]; then
    RCC_URL="$RCC_URL/macos-arm64/rcc"
else
    RCC_URL="$RCC_URL/linux64/rcc"
fi

# Download RCC if it doesn't exist
if [ ! -f "$RCC_PATH" ]; then
    curl -o "$RCC_PATH" "$RCC_URL" --fail || {
        echo -e "\nDevelopment environment setup failed!"
        exit 1
    }
    chmod +x "$RCC_PATH"
fi

# Check if environment exists and ask for clean environment
if [ -f "$ACTIVATE_PATH" ]; then
    echo "Detected existing development environment."
    read -p "Do you want to create a clean environment? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Creating a clean environment..."
        "$RCC_PATH" ht vars "$CONDA_YAML" --space "$PROJECT_NAME" --sema4ai > "$ACTIVATE_PATH"
    fi
else
    echo "Creating a clean environment..."
    "$RCC_PATH" ht vars "$CONDA_YAML" --space "$PROJECT_NAME" --sema4ai > "$ACTIVATE_PATH"
fi

# Activate the virtual environment
echo "Calling: source $ACTIVATE_PATH"
chmod +x "$ACTIVATE_PATH"
source "$ACTIVATE_PATH"

echo -e "\nDeveloper env. ready!"

# Clean up variables
unset RCC_PATH CONDA_YAML ACTIVATE_PATH SCRIPT_PATH PROJECT_NAME