# Slice OAS by Resource

Decompose large OpenAPI specifications into individual, self-contained OAS files—one for each path and HTTP method combination.

## Overview

This tool enables API teams to extract individual endpoints from large OpenAPI specifications while maintaining complete fidelity with the parent specification. Each extracted file is a valid, standalone OpenAPI document that can be immediately used by downstream tools.

## Features

- **Single Endpoint Extraction**: Extract a single API endpoint with all dependencies resolved
- **Batch Processing**: Process 100+ endpoints efficiently (under 3 minutes)
- **Version Conversion**: Convert between OpenAPI 3.0.x and 3.1.x
- **CSV Indexing**: Generate searchable, traceable CSV index of all sliced resources
- **Black-Box UX**: Non-technical users can complete the entire workflow without seeing code or technical details

## Installation

```bash
pip install slice-oas
```

Or using Poetry:

```bash
poetry install
```

## Quick Start

Extract a single endpoint:

```bash
slice-oas --input api.yaml --output-dir ./sliced --resource "/users/{id}:GET"
```

Batch extract all endpoints:

```bash
slice-oas --input api.yaml --output-dir ./sliced --batch
```

## Status

🚧 Early development - Phase 1-2 infrastructure complete. Core extraction features in progress.
