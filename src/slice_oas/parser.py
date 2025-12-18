"""OAS file parsing and version detection."""

import json
import yaml
from pathlib import Path
from typing import Dict, Optional


def parse_oas(file_path: str) -> Optional[Dict]:
    """Parse OpenAPI specification file (JSON or YAML).

    Args:
        file_path: Path to OAS file (JSON or YAML)

    Returns:
        Parsed OAS document as dict, or None if parsing fails
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return None

        content = path.read_text()

        # Detect file type and parse accordingly
        if path.suffix.lower() in ['.json']:
            return json.loads(content)
        elif path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(content)
        else:
            # Try YAML first (more permissive), then JSON
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                return json.loads(content)

    except (json.JSONDecodeError, yaml.YAMLError, IOError, OSError):
        return None


def detect_oas_version(doc: Optional[Dict]) -> Optional[str]:
    """Detect OpenAPI version from document.

    Args:
        doc: Parsed OAS document

    Returns:
        Version family ("3.0.x" or "3.1.x") or None if not detected
    """
    if not doc or not isinstance(doc, dict):
        return None

    openapi_field = doc.get('openapi', '')
    if not isinstance(openapi_field, str):
        return None

    # Parse version string (e.g., "3.0.0" -> "3.0.x")
    parts = openapi_field.split('.')
    if len(parts) >= 2:
        major = parts[0]
        minor = parts[1]

        if major == '3':
            if minor == '0':
                return "3.0.x"
            elif minor == '1':
                return "3.1.x"

    return None
