r"""Path filtering for batch endpoint selection.

Supports glob patterns (/users/*) and regex patterns (^/api/v\d+).
"""

import re
from fnmatch import fnmatch
from typing import List, Tuple, Callable, Optional


class EndpointFilter:
    """Filters endpoints based on path patterns (glob or regex)."""

    def __init__(self, pattern: Optional[str] = None, filter_type: str = "glob"):
        """Initialize filter with pattern.

        Args:
            pattern: Path pattern (e.g., "/users/*" or "^/api/v\\d+")
            filter_type: "glob" or "regex"

        Raises:
            ValueError: If regex pattern is invalid
        """
        self.pattern = pattern
        self.filter_type = filter_type

        # Compile regex if applicable
        self.regex = None
        if pattern and filter_type == "regex":
            try:
                self.regex = re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {pattern}") from e

    def matches(self, path: str) -> bool:
        """Check if path matches filter pattern.

        Args:
            path: Endpoint path (e.g., "/users/{id}")

        Returns:
            True if path matches, False otherwise
        """
        # No pattern = match all
        if not self.pattern:
            return True

        if self.filter_type == "regex":
            return bool(self.regex.match(path))
        else:  # glob
            return fnmatch(path, self.pattern)

    def filter_endpoints(
        self, paths: dict
    ) -> List[Tuple[str, str]]:
        """Filter endpoints from paths dict.

        Args:
            paths: paths dict from OAS document

        Returns:
            List of (path, method) tuples matching filter
        """
        endpoints = []

        for path, path_item in paths.items():
            if not self.matches(path):
                continue

            # Extract valid HTTP methods
            methods = [
                m for m in path_item.keys()
                if m.lower() in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]
            ]

            for method in methods:
                endpoints.append((path, method))

        return endpoints


def create_filter(pattern: Optional[str] = None, filter_type: str = "glob") -> EndpointFilter:
    """Factory function for creating filters.

    Args:
        pattern: Path pattern
        filter_type: "glob" or "regex"

    Returns:
        EndpointFilter instance
    """
    return EndpointFilter(pattern, filter_type)
