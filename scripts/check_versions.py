#!/usr/bin/env python3

"""Check that versions in pyproject.toml and manifest.json match."""

import json
import sys

import toml

try:
    pyproject = toml.load("pyproject.toml")
    py_version = pyproject["project"]["version"]
except (FileNotFoundError, KeyError):
    print("Could not find version in pyproject.toml")
    sys.exit(1)

try:
    with open("custom_components/rainsensor/manifest.json") as f:
        manifest = json.load(f)
    manifest_version = manifest["version"]
except (FileNotFoundError, KeyError):
    print("Could not find version in manifest.json")
    sys.exit(1)

if py_version != manifest_version:
    print(
        f"Versions do not match: pyproject.toml {py_version} != manifest.json {manifest_version}"
    )
    sys.exit(1)
