"""Progress reporting for batch extraction operations."""

from typing import Callable, Optional


class ProgressReporter:
    """Callback-based progress reporter for batch operations."""

    def __init__(self, verbose: bool = True):
        """Initialize progress reporter.

        Args:
            verbose: If False, suppresses progress output
        """
        self.verbose = verbose
        self.last_reported = 0

    def __call__(self, extracted: int, total: int, path: str = "", method: str = ""):
        """Report progress (acts as callback for ThreadPoolExecutor).

        Args:
            extracted: Number of endpoints extracted so far
            total: Total endpoints to process
            path: Current endpoint path (optional)
            method: Current HTTP method (optional)
        """
        if not self.verbose:
            return

        # Calculate percentage
        percentage = (extracted / total * 100) if total > 0 else 0

        # Format message
        if path and method:
            msg = f"Extracting endpoint {extracted}/{total} ({percentage:.0f}%): {method} {path}"
        else:
            msg = f"Extracting endpoint {extracted}/{total} ({percentage:.0f}%)"

        print(msg)

    @staticmethod
    def silent_callback(extracted: int, total: int, path: str = "", method: str = ""):
        """Silent callback that does nothing."""
        pass

    @staticmethod
    def summary(extracted_count: int, failed_count: int, total_count: int, elapsed_time: float):
        """Print completion summary.

        Args:
            extracted_count: Number of successfully extracted endpoints
            failed_count: Number of failed endpoints
            total_count: Total endpoints processed
            elapsed_time: Total elapsed time in seconds
        """
        pass_rate = (extracted_count / total_count * 100) if total_count > 0 else 0
        print(f"\n✓ Batch extraction complete:")
        print(f"  Extracted: {extracted_count}/{total_count}")
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
