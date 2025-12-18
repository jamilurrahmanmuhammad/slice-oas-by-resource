"""Output generation for extracted endpoints.

Formats extracted endpoints as JSON or YAML for file output.
"""

from typing import Dict, Any
import json
import yaml


class OASGenerator:
    """Generates OAS output in JSON or YAML format."""

    def __init__(self, doc: Dict[str, Any], version: str, format: str = "yaml"):
        """Initialize generator with extracted document.

        Args:
            doc: Extracted OAS document
            version: OAS version string
            format: Output format ("json" or "yaml")
        """
        self.doc = doc
        self.version = version
        self.format = format

    def generate(self) -> str:
        """Generate output in specified format.

        Returns:
            String containing formatted OAS document

        Raises:
            ValueError: If format is not supported
        """
        if self.format == "json":
            return json.dumps(self.doc, indent=2)
        elif self.format == "yaml":
            return yaml.dump(self.doc, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(f"Unsupported format: {self.format}")
