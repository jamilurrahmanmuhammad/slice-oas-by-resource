"""Batch processing orchestrator for extracting multiple endpoints in parallel."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from .models import (
    BatchExtractionRequest,
    BatchExtractionResult,
    OASDocument,
    Resource,
    ValidationPhase,
)
from .parser import parse_oas, detect_oas_version
from .filters import EndpointFilter
from .slicer import EndpointSlicer
from .validator import EndpointValidator
from .generator import OASGenerator
from .output_manager import write_output_file, sanitize_path
from .exceptions import InvalidOASError


class BatchProcessor:
    """Orchestrates parallel batch extraction of multiple endpoints."""

    def __init__(self, request: BatchExtractionRequest, progress_callback: Optional[Callable] = None):
        """Initialize batch processor.

        Args:
            request: BatchExtractionRequest with extraction parameters
            progress_callback: Optional callback(extracted_count, total_count, current_path, current_method)
        """
        self.request = request
        self.progress_callback = progress_callback or self._default_callback
        self.oas_doc: Optional[Dict[str, Any]] = None
        self.oas_version: Optional[str] = None
        self.extracted_count = 0
        self.failed_count = 0
        self.failed_endpoints: list = []
        self.output_files: list = []
        self.start_time = 0.0

    def _default_callback(self, extracted: int, total: int, path: str = "", method: str = ""):
        """Default no-op callback."""
        pass

    def process(self) -> BatchExtractionResult:
        """Execute batch extraction with parallel processing.

        Returns:
            BatchExtractionResult with metrics and output paths
        """
        self.start_time = time.time()

        # Load input OAS file
        if not self.request.input_file.exists():
            raise InvalidOASError(f"Input file not found: {self.request.input_file}")

        self.oas_doc = parse_oas(str(self.request.input_file))
        if not self.oas_doc:
            raise InvalidOASError(f"Failed to parse OAS file: {self.request.input_file}")

        # Detect OAS version
        self.oas_version = detect_oas_version(self.oas_doc)
        if not self.oas_version:
            self.oas_version = "3.0.x"  # Default fallback

        # Apply filter to get endpoints
        filter_obj = EndpointFilter(
            pattern=self.request.filter_pattern,
            filter_type=self.request.filter_type,
        )

        paths_dict = self.oas_doc.get("paths", {})
        endpoints = filter_obj.filter_endpoints(paths_dict)
        total_endpoints = len(endpoints)

        if not endpoints:
            return BatchExtractionResult(
                total_endpoints=0,
                extracted_count=0,
                failed_count=0,
                validation_pass_rate=1.0,
                elapsed_time=time.time() - self.start_time,
                csv_index_path=None,
                failed_endpoints=[],
                output_files=[],
            )

        # Create output directory
        self.request.output_dir.mkdir(parents=True, exist_ok=True)

        # Process in parallel if not dry-run
        if self.request.dry_run:
            # Dry-run: just count without processing
            self.extracted_count = total_endpoints
            result = BatchExtractionResult(
                total_endpoints=total_endpoints,
                extracted_count=total_endpoints,
                failed_count=0,
                validation_pass_rate=1.0,
                elapsed_time=time.time() - self.start_time,
                csv_index_path=None,
                failed_endpoints=[],
                output_files=[],
            )
            return result

        # Process with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.request.concurrency) as executor:
            futures = {}
            for path, method in endpoints:
                future = executor.submit(self._extract_endpoint, path, method)
                futures[future] = (path, method)

            # Collect results as completed
            for future in as_completed(futures):
                path, method = futures[future]
                try:
                    output_path = future.result()
                    if output_path:
                        self.output_files.append(output_path)
                        self.extracted_count += 1
                    else:
                        self.failed_count += 1
                except Exception as e:
                    self.failed_count += 1
                    self.failed_endpoints.append((path, method, str(e)))

                # Report progress
                self.progress_callback(
                    self.extracted_count + self.failed_count,
                    total_endpoints,
                    path,
                    method,
                )

        # Calculate metrics
        elapsed = time.time() - self.start_time
        validation_pass_rate = (
            self.extracted_count / total_endpoints if total_endpoints > 0 else 1.0
        )

        return BatchExtractionResult(
            total_endpoints=total_endpoints,
            extracted_count=self.extracted_count,
            failed_count=self.failed_count,
            validation_pass_rate=validation_pass_rate,
            elapsed_time=elapsed,
            csv_index_path=None,  # Set by CSV manager if needed
            failed_endpoints=self.failed_endpoints,
            output_files=self.output_files,
        )

    def _extract_endpoint(self, path: str, method: str) -> Optional[Path]:
        """Extract single endpoint (called in thread).

        Args:
            path: OpenAPI path (e.g., "/users/{id}")
            method: HTTP method (e.g., "GET")

        Returns:
            Path to output file, or None if extraction failed
        """
        try:
            # Extract endpoint using EndpointSlicer
            slicer = EndpointSlicer(self.oas_doc, self.oas_version)
            extracted_doc = slicer.extract(path, method)
            if not extracted_doc:
                self.failed_endpoints.append((path, method, "Extraction returned empty"))
                return None

            # Validate extracted endpoint using EndpointValidator
            validator = EndpointValidator(extracted_doc, self.oas_version, self.oas_doc)
            validation_result = validator.validate()
            if not validation_result.passed:
                self.failed_endpoints.append(
                    (path, method, f"Validation failed: {validation_result.error_message}")
                )
                return None

            # Generate output format using OASGenerator
            generator = OASGenerator(extracted_doc, self.oas_version, self.request.output_format)
            output_content = generator.generate()
            if not output_content:
                self.failed_endpoints.append((path, method, "Generation failed"))
                return None

            # Write output file
            filename = self._generate_filename(path, method)
            output_path = self.request.output_dir / filename
            write_output_file(output_path, output_content)

            return output_path

        except Exception as e:
            self.failed_endpoints.append((path, method, str(e)))
            return None

    def _generate_filename(self, path: str, method: str) -> str:
        """Generate sanitized filename for endpoint.

        Args:
            path: OpenAPI path
            method: HTTP method

        Returns:
            Sanitized filename with extension
        """
        sanitized = sanitize_path(path)
        extension = "json" if self.request.output_format == "json" else "yaml"
        return f"{sanitized}_{method.upper()}.{extension}"


def create_batch_processor(
    request: BatchExtractionRequest,
    progress_callback: Optional[Callable] = None,
) -> BatchProcessor:
    """Factory function for creating batch processors.

    Args:
        request: BatchExtractionRequest
        progress_callback: Optional progress callback

    Returns:
        BatchProcessor instance
    """
    return BatchProcessor(request, progress_callback)
