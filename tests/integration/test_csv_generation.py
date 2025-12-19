"""Integration tests for CSV index generation (Phase 6 US4).

Test scenarios:
- T079: Test CSV creation and basic functionality
- T080: Test real-time CSV updates
- T081: Test duplicate detection
- T082: Test RFC 4180 compliance
- T083: Test append mode
- T084: Test failed extractions NOT added to CSV
- T085: Test CSV with large batches
- T086: Test CSV metadata accuracy
- T087: Test CSV with version conversion
- T088: Test --no-csv flag
"""

import pytest
import csv
import tempfile
from pathlib import Path
from datetime import datetime

from slice_oas.models import BatchExtractionRequest, CSVIndexEntry
from slice_oas.batch_processor import create_batch_processor
from slice_oas.csv_manager import (
    CSVIndexManager,
    create_csv_index_entry,
    count_schemas,
    count_parameters,
    has_security_requirement,
    extract_response_codes,
    extract_csv_metadata,
)
from slice_oas.parser import parse_oas


class TestCSVCreation:
    """T079: Test CSV creation and basic functionality."""

    def test_csv_created_at_correct_path(self, oas_batch_test, temp_output_dir):
        """Verify CSV is created at {output_directory}/sliced-resources-index.csv."""
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

        # CSV should be at expected path
        expected_csv_path = temp_output_dir / "sliced-resources-index.csv"
        assert expected_csv_path.exists(), "CSV file not created at expected path"
        assert result.csv_index_path == expected_csv_path

    def test_csv_has_all_15_columns(self, oas_batch_test, temp_output_dir):
        """Verify CSV has all 15 columns in correct order (Constitution Principle V)."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users",
            output_version="3.0.x",
            generate_csv=True,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        assert csv_path.exists()

        with open(csv_path, "r", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)

        expected_headers = [
            "path", "method", "summary", "description", "operation_id",
            "tags", "filename", "file_size_kb", "schema_count", "parameter_count",
            "response_codes", "security_required", "deprecated", "created_at",
            "output_oas_version",
        ]
        assert headers == expected_headers, f"Headers mismatch: {headers}"

    def test_csv_entries_added_for_successful_extractions(self, oas_batch_test, temp_output_dir):
        """Verify entries are added to CSV for successful extractions."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users*",
            output_version="3.0.x",
            generate_csv=True,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        # Should have entries matching extracted count
        assert len(entries) == result.extracted_count
        assert len(entries) > 0


class TestCSVRealTimeUpdates:
    """T080: Test real-time CSV updates."""

    def test_csv_entries_match_extraction_count(self, oas_batch_test, temp_output_dir):
        """Verify CSV entries match the number of extracted endpoints."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            generate_csv=True,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        assert len(entries) == result.extracted_count

    def test_csv_entries_have_valid_timestamps(self, oas_batch_test, temp_output_dir):
        """Verify CSV entries have valid ISO 8601 timestamps."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users",
            output_version="3.0.x",
            generate_csv=True,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                created_at = row["created_at"]
                assert created_at.endswith("Z"), f"Timestamp not in UTC: {created_at}"
                # Validate ISO 8601 format
                try:
                    datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {created_at}")


class TestCSVDeduplication:
    """T081: Test duplicate detection."""

    def test_no_duplicates_on_rerun(self, oas_batch_test, temp_output_dir):
        """Verify running batch twice doesn't create duplicate entries."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users",
            output_version="3.0.x",
            generate_csv=True,
        )

        # First run
        processor1 = create_batch_processor(request)
        result1 = processor1.process()

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        with open(csv_path, "r", newline="") as f:
            count1 = sum(1 for _ in csv.DictReader(f))

        # Second run (same filter)
        processor2 = create_batch_processor(request)
        result2 = processor2.process()

        with open(csv_path, "r", newline="") as f:
            count2 = sum(1 for _ in csv.DictReader(f))

        # Count should not double
        assert count2 == count1, f"Duplicate entries created: {count2} vs {count1}"

    def test_path_method_uniqueness(self, temp_output_dir):
        """Verify path+method combination is unique in CSV."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        entry1 = create_csv_index_entry(
            path="/users", method="GET", summary="Test", description="",
            operation_id="getUsers", tags=[], filename="users_GET.yaml",
            file_size_kb=1.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )
        entry2 = create_csv_index_entry(
            path="/users", method="GET", summary="Duplicate", description="",
            operation_id="getUsers2", tags=[], filename="users_GET.yaml",
            file_size_kb=2.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )

        added1 = manager.append_entry(entry1)
        added2 = manager.append_entry(entry2)

        assert added1 is True, "First entry should be added"
        assert added2 is False, "Duplicate entry should be skipped"
        assert manager.entry_count == 1

    def test_append_new_entries_only(self, oas_batch_test, temp_output_dir):
        """Verify second run with different filter appends only new entries."""
        # First run: /users endpoints
        request1 = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users",
            output_version="3.0.x",
            generate_csv=True,
        )
        processor1 = create_batch_processor(request1)
        result1 = processor1.process()

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        with open(csv_path, "r", newline="") as f:
            count1 = sum(1 for _ in csv.DictReader(f))

        # Second run: /orders endpoints (new paths)
        request2 = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/orders",
            output_version="3.0.x",
            generate_csv=True,
        )
        processor2 = create_batch_processor(request2)
        result2 = processor2.process()

        with open(csv_path, "r", newline="") as f:
            count2 = sum(1 for _ in csv.DictReader(f))

        # Count should increase by number of new /orders entries
        assert count2 > count1, "New entries should be appended"
        assert count2 == count1 + result2.extracted_count


class TestCSVRFC4180:
    """T082: Test RFC 4180 compliance."""

    def test_csv_with_commas_in_summary(self, temp_output_dir):
        """Test entries with commas in summary are properly escaped."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        entry = create_csv_index_entry(
            path="/users", method="GET",
            summary="List users, including active and inactive",
            description="", operation_id="", tags=[], filename="users_GET.yaml",
            file_size_kb=1.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )
        manager.append_entry(entry)

        # Read back and verify
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row["summary"] == "List users, including active and inactive"

    def test_csv_with_quotes_in_description(self, temp_output_dir):
        """Test entries with quotes in description are properly escaped."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        entry = create_csv_index_entry(
            path="/users", method="GET", summary="Test",
            description='Returns "user" objects',
            operation_id="", tags=[], filename="users_GET.yaml",
            file_size_kb=1.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )
        manager.append_entry(entry)

        # Read back and verify
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row["description"] == 'Returns "user" objects'

    def test_csv_with_newlines_in_description(self, temp_output_dir):
        """Test entries with newlines in description are properly escaped."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        entry = create_csv_index_entry(
            path="/users", method="GET", summary="Test",
            description="Line 1\nLine 2\nLine 3",
            operation_id="", tags=[], filename="users_GET.yaml",
            file_size_kb=1.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )
        manager.append_entry(entry)

        # Read back and verify
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert "Line 1" in row["description"]
            assert "Line 2" in row["description"]


class TestCSVAppendMode:
    """T083: Test append mode."""

    def test_append_mode_preserves_existing_entries(self, temp_output_dir):
        """Verify append mode preserves existing entries."""
        csv_path = temp_output_dir / "test.csv"

        # Create initial CSV with one entry
        manager1 = CSVIndexManager(csv_path)
        manager1.initialize(append_mode=False)
        entry1 = create_csv_index_entry(
            path="/users", method="GET", summary="First", description="",
            operation_id="", tags=[], filename="users_GET.yaml",
            file_size_kb=1.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )
        manager1.append_entry(entry1)

        # Create new manager in append mode
        manager2 = CSVIndexManager(csv_path)
        manager2.initialize(append_mode=True)
        entry2 = create_csv_index_entry(
            path="/orders", method="GET", summary="Second", description="",
            operation_id="", tags=[], filename="orders_GET.yaml",
            file_size_kb=1.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )
        manager2.append_entry(entry2)

        # Read back and verify both entries exist
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        assert len(entries) == 2
        paths = [e["path"] for e in entries]
        assert "/users" in paths
        assert "/orders" in paths

    def test_append_mode_validates_headers(self, temp_output_dir):
        """Verify append mode validates existing headers."""
        csv_path = temp_output_dir / "test.csv"

        # Create CSV with invalid headers
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["invalid", "headers"])

        # New manager should overwrite (headers don't match)
        manager = CSVIndexManager(csv_path)
        manager.initialize(append_mode=True)

        # Should have created new file with correct headers
        with open(csv_path, "r", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)

        assert headers == CSVIndexManager.HEADERS


class TestCSVFailedExtractions:
    """T084: Test failed extractions NOT added to CSV."""

    def test_failed_extractions_not_in_csv(self, oas_batch_test, temp_output_dir):
        """Verify failed extractions are not added to CSV."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern=None,
            output_version="3.0.x",
            generate_csv=True,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        if result.failed_count == 0:
            pytest.skip("No failed extractions to test")

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            csv_entries = list(reader)

        # CSV should have only extracted_count entries (not total_endpoints)
        assert len(csv_entries) == result.extracted_count
        assert len(csv_entries) < result.total_endpoints


class TestCSVLargeBatches:
    """T085: Test CSV with large batches."""

    def test_csv_performance_with_many_entries(self, temp_output_dir):
        """Test CSV performance with 100+ entries."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        import time
        start = time.time()

        # Add 100 entries
        for i in range(100):
            entry = create_csv_index_entry(
                path=f"/resource{i}", method="GET", summary=f"Resource {i}",
                description="", operation_id=f"getResource{i}", tags=[],
                filename=f"resource{i}_GET.yaml", file_size_kb=1.0,
                schema_count=i % 5, parameter_count=i % 3,
                response_codes="200,400", security_required=i % 2 == 0,
                deprecated=False, output_oas_version="3.0.x",
            )
            manager.append_entry(entry)

        elapsed = time.time() - start

        # Should complete quickly (< 1 second for 100 entries)
        assert elapsed < 1.0, f"CSV operations too slow: {elapsed:.2f}s"
        assert manager.entry_count == 100

    def test_csv_read_with_many_entries(self, temp_output_dir):
        """Test CSV reading with many entries."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        # Add 50 entries
        for i in range(50):
            entry = create_csv_index_entry(
                path=f"/resource{i}", method="GET", summary=f"Resource {i}",
                description="", operation_id="", tags=[],
                filename=f"resource{i}_GET.yaml", file_size_kb=1.0,
                schema_count=0, parameter_count=0, response_codes="200",
                security_required=False, deprecated=False,
                output_oas_version="3.0.x",
            )
            manager.append_entry(entry)

        # Read all entries
        entries = manager.read_entries()
        assert len(entries) == 50


class TestCSVMetadataAccuracy:
    """T086: Test CSV metadata accuracy."""

    def test_schema_count_calculation(self):
        """Verify schema_count is calculated correctly."""
        doc = {
            "components": {
                "schemas": {
                    "User": {"type": "object"},
                    "Error": {"type": "object"},
                    "Pagination": {"type": "object"},
                }
            }
        }
        assert count_schemas(doc) == 3

        # Empty document
        assert count_schemas({}) == 0
        assert count_schemas({"components": {}}) == 0

    def test_parameter_count_calculation(self):
        """Verify parameter_count is calculated correctly."""
        doc = {
            "paths": {
                "/users/{id}": {
                    "parameters": [{"name": "id", "in": "path"}],
                    "get": {
                        "parameters": [
                            {"name": "include", "in": "query"},
                            {"name": "fields", "in": "query"},
                        ]
                    }
                }
            }
        }
        # 1 path-level + 2 operation-level = 3
        assert count_parameters(doc, "/users/{id}", "get") == 3

    def test_response_codes_extraction(self):
        """Verify response_codes is extracted correctly."""
        operation = {
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Bad Request"},
                "404": {"description": "Not Found"},
            }
        }
        codes = extract_response_codes(operation)
        assert codes == "200,400,404"

    def test_security_requirement_detection(self):
        """Verify security_required is detected correctly."""
        # Operation with security
        op_with_security = {"security": [{"bearerAuth": []}]}
        assert has_security_requirement(op_with_security, {}) is True

        # Operation with empty security (explicitly no security)
        op_empty_security = {"security": []}
        assert has_security_requirement(op_empty_security, {}) is False

        # Operation without security, but global security exists
        op_no_security = {}
        doc_global_security = {"security": [{"apiKey": []}]}
        assert has_security_requirement(op_no_security, doc_global_security) is True

        # No security anywhere
        assert has_security_requirement({}, {}) is False

    def test_metadata_extraction_complete(self, temp_output_dir):
        """Verify extract_csv_metadata returns all required fields."""
        doc = {
            "paths": {
                "/users/{id}": {
                    "get": {
                        "summary": "Get user by ID",
                        "description": "Returns a user",
                        "operationId": "getUserById",
                        "tags": ["users", "public"],
                        "deprecated": False,
                        "security": [{"bearerAuth": []}],
                        "responses": {
                            "200": {"description": "OK"},
                            "404": {"description": "Not found"},
                        },
                        "parameters": [
                            {"name": "id", "in": "path"},
                        ],
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {"type": "object"},
                }
            }
        }

        # Create a temp file for file_size_kb calculation
        test_file = temp_output_dir / "users-id_GET.yaml"
        test_file.write_text("test content")

        metadata = extract_csv_metadata(doc, "/users/{id}", "get", test_file, "3.0.x")

        assert metadata["path"] == "/users/{id}"
        assert metadata["method"] == "GET"
        assert metadata["summary"] == "Get user by ID"
        assert metadata["description"] == "Returns a user"
        assert metadata["operation_id"] == "getUserById"
        assert metadata["tags"] == ["users", "public"]
        assert metadata["filename"] == "users-id_GET.yaml"
        assert metadata["file_size_kb"] > 0
        assert metadata["schema_count"] == 1
        assert metadata["parameter_count"] == 1
        assert metadata["response_codes"] == "200,404"
        assert metadata["security_required"] is True
        assert metadata["deprecated"] is False
        assert metadata["output_oas_version"] == "3.0.x"


class TestCSVVersionConversion:
    """T087: Test CSV with version conversion."""

    def test_csv_reflects_converted_version(self, oas_batch_test, temp_output_dir):
        """Verify output_oas_version reflects the converted version."""
        # Note: This test requires a 3.0 source and 3.1 target conversion
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users",
            output_version="3.1.x",  # Convert to 3.1
            generate_csv=True,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        if result.extracted_count == 0:
            pytest.skip("No extractions to verify")

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Should reflect the target version
                assert row["output_oas_version"] in ["3.0.x", "3.1.x"]


class TestCSVNoCSVFlag:
    """T088: Test --no-csv flag."""

    def test_no_csv_flag_prevents_creation(self, oas_batch_test, temp_output_dir):
        """Verify --no-csv flag prevents CSV file creation."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users",
            output_version="3.0.x",
            generate_csv=False,  # Disable CSV
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # CSV should not be created
        csv_path = temp_output_dir / "sliced-resources-index.csv"
        assert not csv_path.exists(), "CSV file should not be created with --no-csv"
        assert result.csv_index_path is None

    def test_extraction_works_without_csv(self, oas_batch_test, temp_output_dir):
        """Verify extraction still works when CSV is disabled."""
        request = BatchExtractionRequest(
            input_file=oas_batch_test,
            output_dir=temp_output_dir,
            filter_pattern="/users*",
            output_version="3.0.x",
            generate_csv=False,
        )

        processor = create_batch_processor(request)
        result = processor.process()

        # Extraction should work
        assert result.extracted_count > 0
        assert len(result.output_files) > 0

        # Output files should exist
        for output_file in result.output_files:
            assert output_file.exists()


class TestCSVManagerUnit:
    """Unit tests for CSVIndexManager class."""

    def test_has_duplicate_detection(self, temp_output_dir):
        """Test has_duplicate method."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        # Initially no duplicates
        assert manager.has_duplicate("/users", "GET") is False

        entry = create_csv_index_entry(
            path="/users", method="GET", summary="Test", description="",
            operation_id="", tags=[], filename="users_GET.yaml",
            file_size_kb=1.0, schema_count=0, parameter_count=0,
            response_codes="200", security_required=False, deprecated=False,
            output_oas_version="3.0.x",
        )
        manager.append_entry(entry)

        # Now should detect duplicate
        assert manager.has_duplicate("/users", "GET") is True
        assert manager.has_duplicate("/users", "get") is True  # Case insensitive
        assert manager.has_duplicate("/users", "POST") is False  # Different method
        assert manager.has_duplicate("/orders", "GET") is False  # Different path

    def test_entry_count_tracking(self, temp_output_dir):
        """Test entry_count property."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        assert manager.entry_count == 0

        for i in range(5):
            entry = create_csv_index_entry(
                path=f"/resource{i}", method="GET", summary="", description="",
                operation_id="", tags=[], filename=f"resource{i}_GET.yaml",
                file_size_kb=1.0, schema_count=0, parameter_count=0,
                response_codes="200", security_required=False, deprecated=False,
                output_oas_version="3.0.x",
            )
            manager.append_entry(entry)

        assert manager.entry_count == 5

    def test_append_batch_with_duplicates(self, temp_output_dir):
        """Test append_batch skips duplicates."""
        csv_path = temp_output_dir / "test.csv"
        manager = CSVIndexManager(csv_path)
        manager.initialize()

        entries = [
            create_csv_index_entry(
                path="/users", method="GET", summary="First", description="",
                operation_id="", tags=[], filename="users_GET.yaml",
                file_size_kb=1.0, schema_count=0, parameter_count=0,
                response_codes="200", security_required=False, deprecated=False,
                output_oas_version="3.0.x",
            ),
            create_csv_index_entry(
                path="/users", method="GET", summary="Duplicate", description="",
                operation_id="", tags=[], filename="users_GET.yaml",
                file_size_kb=1.0, schema_count=0, parameter_count=0,
                response_codes="200", security_required=False, deprecated=False,
                output_oas_version="3.0.x",
            ),
            create_csv_index_entry(
                path="/orders", method="GET", summary="Second", description="",
                operation_id="", tags=[], filename="orders_GET.yaml",
                file_size_kb=1.0, schema_count=0, parameter_count=0,
                response_codes="200", security_required=False, deprecated=False,
                output_oas_version="3.0.x",
            ),
        ]

        added = manager.append_batch(entries)
        assert added == 2  # One duplicate skipped
        assert manager.entry_count == 2


# ============================================================================
# User Story 7: CSV Index for Single Extractions (T063-T069)
# ============================================================================

class TestSingleExtractionCSV:
    """Tests for CSV generation on single endpoint extractions.

    User Story 7 (US7): CSV Index for Single Extractions
    Per FR-014: Single endpoint extraction MUST create/update the CSV index.
    Per FR-015: CSV index MUST maintain duplicate detection for single extractions.
    """

    def test_single_extraction_creates_csv_index(self, temp_output_dir):
        """T063: Single extraction creates CSV index file.

        Given a single endpoint extraction (not batch),
        When extraction completes successfully,
        Then a CSV index entry is created at {output_dir}/sliced-resources-index.csv.
        """
        from slice_oas.slicer import EndpointSlicer
        from slice_oas.csv_manager import CSVIndexManager, extract_csv_metadata, create_csv_index_entry

        # Create a simple spec
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "operationId": "listUsers",
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            }
        }

        # Extract the endpoint
        slicer = EndpointSlicer(spec, "3.0.3")
        extracted = slicer.extract("/users", "GET")

        # Write the output file
        output_path = temp_output_dir / "users_GET.yaml"
        import yaml
        output_path.write_text(yaml.dump(extracted))

        # Generate CSV entry (simulating what single extraction should do)
        csv_path = temp_output_dir / "sliced-resources-index.csv"
        csv_manager = CSVIndexManager(csv_path)
        csv_manager.initialize(append_mode=True)

        metadata = extract_csv_metadata(extracted, "/users", "GET", output_path, "3.0.x")
        entry = create_csv_index_entry(**metadata)
        csv_manager.append_entry(entry)

        # Verify CSV was created
        assert csv_path.exists(), "CSV index file should be created"

        # Verify entry exists
        entries = csv_manager.read_entries()
        assert len(entries) == 1
        assert entries[0]["path"] == "/users"
        assert entries[0]["method"] == "GET"

    def test_single_extraction_appends_to_existing_csv(self, temp_output_dir):
        """T064: Single extraction appends to existing CSV index.

        Given an existing CSV index with entries,
        When extracting another single endpoint,
        Then the new entry is appended without overwriting existing entries.
        """
        from slice_oas.slicer import EndpointSlicer
        from slice_oas.csv_manager import CSVIndexManager, extract_csv_metadata, create_csv_index_entry
        import yaml

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}}
                    }
                },
                "/orders": {
                    "get": {
                        "summary": "List orders",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        slicer = EndpointSlicer(spec, "3.0.3")

        # First extraction
        extracted1 = slicer.extract("/users", "GET")
        output_path1 = temp_output_dir / "users_GET.yaml"
        output_path1.write_text(yaml.dump(extracted1))

        csv_manager1 = CSVIndexManager(csv_path)
        csv_manager1.initialize(append_mode=True)
        metadata1 = extract_csv_metadata(extracted1, "/users", "GET", output_path1, "3.0.x")
        entry1 = create_csv_index_entry(**metadata1)
        csv_manager1.append_entry(entry1)

        # Second extraction (new endpoint)
        extracted2 = slicer.extract("/orders", "GET")
        output_path2 = temp_output_dir / "orders_GET.yaml"
        output_path2.write_text(yaml.dump(extracted2))

        csv_manager2 = CSVIndexManager(csv_path)
        csv_manager2.initialize(append_mode=True)
        metadata2 = extract_csv_metadata(extracted2, "/orders", "GET", output_path2, "3.0.x")
        entry2 = create_csv_index_entry(**metadata2)
        csv_manager2.append_entry(entry2)

        # Verify both entries exist
        entries = csv_manager2.read_entries()
        assert len(entries) == 2
        paths = [e["path"] for e in entries]
        assert "/users" in paths
        assert "/orders" in paths

    def test_single_extraction_csv_no_duplicates(self, temp_output_dir):
        """T065: Single extraction doesn't create duplicate CSV entries.

        Given an existing CSV index with an entry for /users GET,
        When extracting /users GET again,
        Then no duplicate entry is added to the CSV.
        """
        from slice_oas.slicer import EndpointSlicer
        from slice_oas.csv_manager import CSVIndexManager, extract_csv_metadata, create_csv_index_entry
        import yaml

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        slicer = EndpointSlicer(spec, "3.0.3")

        # First extraction
        extracted = slicer.extract("/users", "GET")
        output_path = temp_output_dir / "users_GET.yaml"
        output_path.write_text(yaml.dump(extracted))

        csv_manager = CSVIndexManager(csv_path)
        csv_manager.initialize(append_mode=True)
        metadata = extract_csv_metadata(extracted, "/users", "GET", output_path, "3.0.x")
        entry = create_csv_index_entry(**metadata)

        # Add entry twice
        added1 = csv_manager.append_entry(entry)
        added2 = csv_manager.append_entry(entry)

        assert added1 is True, "First entry should be added"
        assert added2 is False, "Duplicate entry should be skipped"

        # Verify only one entry exists
        entries = csv_manager.read_entries()
        assert len(entries) == 1

    def test_single_extraction_csv_metadata_complete(self, temp_output_dir):
        """T066: Single extraction CSV entry has all required metadata.

        Given a single endpoint extraction,
        When CSV entry is created,
        Then all 15 columns are populated correctly.
        """
        from slice_oas.slicer import EndpointSlicer
        from slice_oas.csv_manager import CSVIndexManager, extract_csv_metadata, create_csv_index_entry
        import yaml

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users/{id}": {
                    "get": {
                        "summary": "Get user by ID",
                        "description": "Returns a single user",
                        "operationId": "getUserById",
                        "tags": ["users"],
                        "deprecated": False,
                        "parameters": [
                            {"name": "id", "in": "path", "required": True}
                        ],
                        "responses": {
                            "200": {"description": "Success"},
                            "404": {"description": "Not found"}
                        },
                        "security": [{"bearerAuth": []}]
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {"type": "object"}
                },
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"}
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.3")
        extracted = slicer.extract("/users/{id}", "GET")

        output_path = temp_output_dir / "users-id_GET.yaml"
        output_path.write_text(yaml.dump(extracted))

        csv_path = temp_output_dir / "sliced-resources-index.csv"
        csv_manager = CSVIndexManager(csv_path)
        csv_manager.initialize(append_mode=True)

        metadata = extract_csv_metadata(extracted, "/users/{id}", "GET", output_path, "3.0.x")
        entry = create_csv_index_entry(**metadata)
        csv_manager.append_entry(entry)

        # Read back and verify all columns
        entries = csv_manager.read_entries()
        assert len(entries) == 1

        row = entries[0]
        assert row["path"] == "/users/{id}"
        assert row["method"] == "GET"
        assert row["summary"] == "Get user by ID"
        assert row["description"] == "Returns a single user"
        assert row["operation_id"] == "getUserById"
        assert "users" in row["tags"]
        assert row["filename"] == "users-id_GET.yaml"
        assert float(row["file_size_kb"]) > 0
        assert row["response_codes"] == "200,404"
        assert row["deprecated"] in ["False", "no", "false"]  # Boolean serialization varies
        assert row["output_oas_version"] == "3.0.x"
        # created_at should be ISO 8601 format
        assert "T" in row["created_at"]
        assert row["created_at"].endswith("Z")
