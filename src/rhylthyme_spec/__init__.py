#!/usr/bin/env python3
"""
Rhylthyme Specifications Package

This package provides JSON schemas and specifications for Rhylthyme programs and environments.
"""

__version__ = "0.1.0-alpha"
__author__ = "Rhylthyme Team"
__description__ = "JSON schemas and specifications for Rhylthyme programs and environments"

import os
import pkg_resources

# Get the path to the schemas directory
def get_schema_path(schema_name):
    """Get the full path to a schema file."""
    return pkg_resources.resource_filename('rhylthyme_spec', f'schemas/{schema_name}')

# Program schema versions shipped in this package, oldest first.
PROGRAM_SCHEMA_VERSIONS = ("0.2.0-alpha", "0.3.0-alpha")

# Convenience functions for accessing schemas
def get_program_schema_path(version="0.2.0-alpha"):
    """Get the path to the program schema (default 0.2.0-alpha; see PROGRAM_SCHEMA_VERSIONS)."""
    return get_schema_path(f'program_schema_{version}.json')

def get_environment_schema_path():
    """Get the path to the environment schema."""
    return get_schema_path('environment_schema_0.1.0-alpha.json')

def get_runs_schema_path():
    """Get the path to the run record schema (execution history)."""
    return get_schema_path('runs_schema_0.1.0-alpha.json')

__all__ = ['get_schema_path', 'get_program_schema_path', 'get_environment_schema_path', 'get_runs_schema_path', 'PROGRAM_SCHEMA_VERSIONS'] 