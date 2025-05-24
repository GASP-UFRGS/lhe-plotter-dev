#!/bin/bash

ENV_NAME=lhe-env

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔍 Checking for ROOT..."

if command -v root >/dev/null 2>&1; then
    ROOT_PATH=$(command -v root)
    echo -e "ROOT is already installed at: ${GREEN}${ROOT_PATH}${NC}"
else
    echo -e "${RED}ROOT not found.${NC}"

    if ! command -v conda >/dev/null 2>&1; then
        echo -e "${RED}Conda is not available. Please install Miniconda or Anaconda.${NC}"
        exit 1
    fi

    echo "Installing ROOT with conda..."
    conda install -y -c conda-forge root
fi

echo "🐍 Checking for Python 3..."

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Python 3 is not available. Please install or activate a Python 3 environment.${NC}"
    exit 1
fi

# Set up Python virtual environment
echo "Setting up Python virtual environment in ${ENV_NAME}"
python3 -m venv $ENV_NAME

echo "Activating virtual environment and installing requirements..."
source ${ENV_NAME}/bin/activate

# Upgrade pip and install requirements
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo -e "${GREEN}Setup complete.${NC}"
python3 -c "import ROOT; print(f'ROOT Version: {ROOT.gROOT.GetVersion()}')"

