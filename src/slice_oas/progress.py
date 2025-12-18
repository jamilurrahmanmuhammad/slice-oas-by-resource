"""Progress reporting for batch extraction operations."""

from typing import Callable, Optional
from enum import Enum


class ProcessPhase(str, Enum):
    """Phases in endpoint processing pipeline."""
    EXTRACTION = "Extracting"
    CONVERSION = "Converting"
    VALIDATION = "Validating"
    OUTPUT = "Writing"


class ProgressReporter:
    """Callback-based progress reporter for batch operations."""

    def __init__(self, verbose: bool = True, phase: ProcessPhase = ProcessPhase.EXTRACTION):
        """Initialize progress reporter.

        Args:
            verbose: If False, suppresses progress output
            phase: Current processing phase (extraction, conversion, etc.)
        """
        self.verbose = verbose
        self.last_reported = 0
        self.phase = phase

    def set_phase(self, phase: ProcessPhase):
        """Update the current processing phase.

        Args:
            phase: New processing phase
        """
        self.phase = phase

    def __call__(self, extracted: int, total: int, path: str = "", method: str = ""):
        """Report progress (acts as callback for ThreadPoolExecutor).

        Args:
            extracted: Number of endpoints processed so far
            total: Total endpoints to process
            path: Current endpoint path (optional)
            method: Current HTTP method (optional)
        """
        if not self.verbose:
            return

        # Calculate percentage
        percentage = (extracted / total * 100) if total > 0 else 0

        # Format message with current phase
        if path and method:
            msg = f"{self.phase.value} endpoint {extracted}/{total} ({percentage:.0f}%): {method} {path}"
        else:
            msg = f"{self.phase.value} endpoint {extracted}/{total} ({percentage:.0f}%)"

        print(msg)

    @staticmethod
    def silent_callback(extracted: int, total: int, path: str = "", method: str = ""):
        """Silent callback that does nothing."""
        pass

    @staticmethod
    def summary(extracted_count: int, failed_count: int, total_count: int, elapsed_time: float,
                conversion_count: Optional[int] = None):
        """Print completion summary.

        Args:
            extracted_count: Number of successfully extracted endpoints
            failed_count: Number of failed endpoints
            total_count: Total endpoints processed
            elapsed_time: Total elapsed time in seconds
            conversion_count: Number of endpoints that were version-converted (optional)
        """
        pass_rate = (extracted_count / total_count * 100) if total_count > 0 else 0
        print(f"\n✓ Batch processing complete:")
        print(f"  Extracted: {extracted_count}/{total_count}")
        if conversion_count is not None and conversion_count > 0:
            print(f"  Converted: {conversion_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Pass rate: {pass_rate:.1f}%")
        print(f"  Time: {elapsed_time:.1f}s")


def create_progress_callback(
    verbose: bool = True,
) -> Callable[[int, int, str, str], None]:
    """Factory function for creating progress callbacks.

    Args:
        verbose: If False, returns silent callback

    Returns:
        Callback function
    """
    if verbose:
        reporter = ProgressReporter(verbose=True)
        return reporter
    else:
        return ProgressReporter.silent_callback
