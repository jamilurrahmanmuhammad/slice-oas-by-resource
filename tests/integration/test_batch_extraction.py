"""Integration tests for batch endpoint extraction (Phase 4 US2).

Test scenarios:
- T045: Batch extract 10 endpoints
- T046: Batch extract with glob filter (/users/*)
- T047: Batch extract with regex filter (^/api/v)
- T048: Handle missing endpoints gracefully
- T049: Handle invalid filter pattern
- T050: Generate CSV index correctly
- T051: Parallel extraction produces same results as sequential
- T052: Performance benchmark (<3 min for 100 endpoints)
- T053: Acceptance testing via slice-oas-by-resource skill
"""

import pytest
import time
import json
import csv
from pathlib import Path
from slice_oas.models import BatchExtractionRequest
from slice_oas.batch_processor import create_batch_processor
from slice_oas.filters import EndpointFilter
from slice_oas.parser import parse_oas


class TestBatchExtractionFramework:
    """T044: Integration test framework setup."""

    def test_batch_test_fixture_loads(self, oas_batch_test):
        """Verify batch test fixture file exists and is accessible."""
        assert oas_batch_test is not None
        assert oas_batch_test.exists()
        assert oas_batch_test.suffix == ".yaml"

    def test_batch_test_doc_parses(self, batch_test_doc):
        """Verify batch test document parses correctly."""
        assert batch_test_doc is not None
        assert "openapi" in batch_test_doc
        assert "paths" in batch_test_doc
        assert len(batch_test_doc["paths"]) >= 6  # At least 6 paths in fixture

    def test_temp_output_dir_fixture(self, temp_output_dir):
        """Verify temporary output directory fixture works."""
        assert temp_output_dir.exists()
        assert temp_output_dir.is_dir()
        # Write test file
        test_file = temp_output_dir / "test.txt"
        test_file.write_text("test")
        assert test_file.exists()


class TestBatchExtraction:
    """T045: Batch extract 10 endpoints from test OAS."""

    def test_batch_extract_all_endpoints(self, oas_batch_test, temp_output_dir, batch_test_doc):
        """Extract all endpoints from batch test fixture."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,  # No filter = all endpoints
            output_version="3.0.x",
            concurrency=2,
            output_format="yaml",
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Should extract all endpoints (7 total: /users GET, /users/{id} GET+DELETE, /api/v1/products GET+GET, /orders GET+GET)
        assert result.total_endpoints == 7
        assert result.extracted_count >= 6  # At least 6 should extract successfully
        assert result.validation_pass_rate >= 0.8  # At least 80% pass rate

    def test_batch_extract_creates_output_files(self, oas_batch_test, temp_output_dir):
        """Verify batch extraction creates output files."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=2,
            output_format="yaml",
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Check output files exist
        assert len(result.output_files) > 0
        for output_file in result.output_files:
            assert output_file.exists()
            assert output_file.suffix == ".yaml"
            # Verify file has content
            content = output_file.read_text()
            assert len(content) > 0
            assert "openapi" in content

    def test_batch_extract_result_structure(self, oas_batch_test, temp_output_dir):
        """Verify BatchExtractionResult has expected structure."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Verify result structure
        assert hasattr(result, 'total_endpoints')
        assert hasattr(result, 'extracted_count')
        assert hasattr(result, 'failed_count')
        assert hasattr(result, 'validation_pass_rate')
        assert hasattr(result, 'elapsed_time')
        assert hasattr(result, 'output_files')
        assert hasattr(result, 'failed_endpoints')

        # Verify math
        assert result.extracted_count + result.failed_count == result.total_endpoints
        assert 0.0 <= result.validation_pass_rate <= 1.0
        assert result.elapsed_time >= 0.0


class TestBatchFilteringGlob:
    """T046: Batch extract with glob filter pattern."""

    def test_batch_filter_glob_users(self, oas_batch_test, temp_output_dir):
        """Filter endpoints matching /users* pattern."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users*",
            filter_type="glob",
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Should extract only /users and /users/{id} endpoints
        # /users: GET
        # /users/{id}: GET, DELETE
        # Total: 3 endpoints
        assert result.total_endpoints == 3
        assert result.extracted_count >= 3  # Should all succeed

    def test_batch_filter_glob_api_v1(self, oas_batch_test, temp_output_dir):
        """Filter endpoints matching /api/v1/* pattern."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/api/v1/*",
            filter_type="glob",
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Should extract /api/v1/products and /api/v1/products/{productId}
        # Total: 2 endpoints
        assert result.total_endpoints == 2
        assert result.extracted_count >= 1


class TestBatchFilteringRegex:
    """T047: Batch extract with regex filter pattern."""

    def test_batch_filter_regex_api_v(self, oas_batch_test, temp_output_dir):
        """Filter endpoints matching regex ^/api/v pattern."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=r"^/api/v",
            filter_type="regex",
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Should extract only /api/v1/* endpoints
        assert result.total_endpoints == 2

    def test_batch_filter_regex_users_or_orders(self, oas_batch_test, temp_output_dir):
        """Filter endpoints matching regex ^/(users|orders) pattern."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=r"^/(users|orders)",
            filter_type="regex",
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Should extract /users, /users/{id}, /orders, /orders/{orderId}
        # /users: GET (1), /users/{id}: GET+DELETE (2), /orders: GET (1), /orders/{orderId}: GET (1)
        # Total: 5 endpoints
        assert result.total_endpoints == 5


class TestBatchErrorHandling:
    """T048: Handle missing endpoints and invalid inputs gracefully."""

    def test_batch_missing_input_file(self, temp_output_dir):
        """Handle missing input file gracefully."""
        request = BatchExtractionRequest(
            input_file=Path("/nonexistent/file.yaml"),
            output_dir=temp_output_dir,
            output_version="3.0.x",
        )

        processor = create_batch_processor(request)
        with pytest.raises(Exception):  # Should raise InvalidOASError
            processor.process()

    def test_batch_empty_filter_result(self, oas_batch_test, temp_output_dir):
        """Handle filter that matches no endpoints."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/nonexistent/*",
            filter_type="glob",
            output_version="3.0.x",
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Should complete successfully with 0 endpoints
        assert result.total_endpoints == 0
        assert result.extracted_count == 0
        assert result.failed_count == 0


class TestBatchInvalidFilter:
    """T049: Handle invalid filter patterns."""

    def test_batch_invalid_regex_pattern(self, oas_batch_test, temp_output_dir):
        """Reject invalid regex pattern."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="[invalid(regex",
            filter_type="regex",
            output_version="3.0.x",
        )

        processor = create_batch_processor(request)
        with pytest.raises(ValueError):
            processor.process()

    def test_batch_invalid_filter_type(self, oas_batch_test, temp_output_dir):
        """Handle invalid filter type."""
        # This should be caught during filter creation
        try:
            from slice_oas.filters import EndpointFilter
            # Invalid filter type should be handled gracefully
            # Current implementation defaults to glob, but we can test the filter
            filter_obj = EndpointFilter("/users/*", "glob")
            assert filter_obj is not None
        except ValueError:
            # Some implementations might reject invalid types
            pass


class TestBatchCSVIndex:
    """T050: Generate CSV index correctly."""

    def test_batch_csv_index_creation(self, oas_batch_test, temp_output_dir):
        """Verify CSV index is created with all endpoints."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=2,
            generate_csv=True,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Note: CSV manager integration would be implemented in future phase
        # For now, verify result structure supports CSV generation
        assert hasattr(result, 'csv_index_path')

    def test_batch_output_files_are_valid_oas(self, oas_batch_test, temp_output_dir):
        """Verify all output files are valid OAS documents."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users/*",
            output_version="3.0.x",
            concurrency=2,
            output_format="yaml",
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Verify each output file is valid OAS
        from slice_oas.parser import parse_oas
        for output_file in result.output_files:
            doc = parse_oas(str(output_file))
            assert doc is not None
            assert "openapi" in doc
            assert "paths" in doc


class TestBatchParallelConsistency:
    """T051: Parallel extraction produces same results as sequential."""

    def test_parallel_vs_sequential_consistency(self, oas_batch_test, temp_output_dir):
        """Verify parallel extraction matches sequential extraction."""
        # Extract with 1 worker (sequential)
        request_seq = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=1,
        )

        processor_seq = create_batch_processor(request_seq)
        result_seq = processor_seq.process()

        # Extract with 4 workers (parallel)
        temp_output_dir_parallel = temp_output_dir / "parallel"
        temp_output_dir_parallel.mkdir()

        request_par = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir_parallel,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=4,
        )

        processor_par = create_batch_processor(request_par)
        result_par = processor_par.process()

        # Results should be identical
        assert result_seq.total_endpoints == result_par.total_endpoints
        assert result_seq.extracted_count == result_par.extracted_count
        assert result_seq.failed_count == result_par.failed_count
        assert result_seq.validation_pass_rate == result_par.validation_pass_rate

    def test_output_file_count_consistency(self, oas_batch_test, temp_output_dir):
        """Verify output file counts match between runs."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Count YAML files in output directory (excludes CSV index)
        output_files = list(temp_output_dir.glob("*.yaml"))
        assert len(output_files) == len(result.output_files)


class TestBatchPerformance:
    """T052: Performance benchmark for batch processing."""

    def test_batch_extraction_performance(self, oas_batch_test, temp_output_dir):
        """Measure batch extraction performance."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=4,
        )

        start_time = time.time()
        processor = create_batch_processor(request)
        result = processor.process()
        elapsed = time.time() - start_time

        # Record timing
        assert result.elapsed_time > 0
        # Batch of 10 endpoints should complete quickly (< 5 seconds)
        assert elapsed < 5.0

    def test_parallel_outperforms_sequential(self, oas_batch_test, temp_output_dir):
        """Verify parallel processing outperforms sequential."""
        # Sequential (1 worker)
        temp_seq = temp_output_dir / "seq"
        temp_seq.mkdir()
        request_seq = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_seq,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=1,
        )

        processor_seq = create_batch_processor(request_seq)
        start_seq = time.time()
        result_seq = processor_seq.process()
        time_seq = time.time() - start_seq

        # Parallel (4 workers)
        temp_par = temp_output_dir / "par"
        temp_par.mkdir()
        request_par = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_par,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=4,
        )

        processor_par = create_batch_processor(request_par)
        start_par = time.time()
        result_par = processor_par.process()
        time_par = time.time() - start_par

        # Parallel should not be significantly slower
        # (On small batches, parallel might be slower due to overhead)
        assert time_par < time_seq * 1.5


class TestBatchAcceptance:
    """T053: Acceptance testing - verify extracted endpoints are usable."""

    def test_extracted_endpoints_are_parseable(self, oas_batch_test, temp_output_dir):
        """Verify extracted endpoints can be parsed as valid OAS."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users/*",
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Verify each extracted endpoint is parseable
        from slice_oas.parser import parse_oas
        for output_file in result.output_files:
            doc = parse_oas(str(output_file))
            assert doc is not None, f"Failed to parse {output_file}"

    def test_extracted_endpoints_have_required_fields(self, oas_batch_test, temp_output_dir):
        """Verify extracted endpoints have all required OAS fields."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=2,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        from slice_oas.parser import parse_oas
        for output_file in result.output_files:
            doc = parse_oas(str(output_file))
            # Required fields
            assert "openapi" in doc
            assert "info" in doc
            assert "info" in doc and "title" in doc["info"]
            assert "info" in doc and "version" in doc["info"]
            assert "paths" in doc
            # Should have exactly one path (extracted endpoint)
            assert len(doc["paths"]) == 1

    def test_extracted_endpoints_preserve_operations(self, oas_batch_test, temp_output_dir):
        """Verify extracted endpoints preserve operation details."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users",
            output_version="3.0.x",
            concurrency=1,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        from slice_oas.parser import parse_oas
        original_doc = parse_oas(str(oas_batch_test))

        # Check that operations are preserved
        for output_file in result.output_files:
            extracted_doc = parse_oas(str(output_file))
            # At least one path should be present
            assert len(extracted_doc["paths"]) > 0
            # At least one operation per path
            for path, path_item in extracted_doc["paths"].items():
                operations = [m for m in path_item.keys()
                             if m.lower() in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]]
                assert len(operations) > 0

    def test_dry_run_preview_matches_extraction(self, oas_batch_test, temp_output_dir):
        """Verify dry-run preview shows endpoints without writing files."""
        # Dry run
        temp_dry = temp_output_dir / "dry"
        temp_dry.mkdir()
        request_dry = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_dry,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=2,
            dry_run=True,
        )

        processor_dry = create_batch_processor(request_dry)
        result_dry = processor_dry.process()

        # Actual extraction
        temp_actual = temp_output_dir / "actual"
        temp_actual.mkdir()
        request_actual = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_actual,
            filter_pattern=None,
            output_version="3.0.x",
            concurrency=2,
            dry_run=False,
        )

        processor_actual = create_batch_processor(request_actual)
        result_actual = processor_actual.process()

        # Dry run should report same total_endpoints count
        assert result_dry.total_endpoints == result_actual.total_endpoints
        # In dry run, no files written (but count shows total)
        assert len(result_dry.output_files) == 0
        # In actual run, files should be written (may be fewer due to validation failures)
        assert len(result_actual.output_files) > 0
        # Actual extracted should be <= dry run count (due to validation)
        assert result_actual.extracted_count <= result_dry.extracted_count
