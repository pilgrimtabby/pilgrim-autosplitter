#!/usr/bin/env bash

# Helper script for building on MacOS (see build.sh)

# This script is injected into the Platypus app when injecting the PyInstaller executible.
# It enables the app to work while retaining the app's name and icon.


SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
open "$SCRIPT_DIR"/"Pilgrim Autosplitter"
