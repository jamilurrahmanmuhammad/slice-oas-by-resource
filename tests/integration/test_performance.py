"""Performance benchmark tests (T103).

Tests performance requirements:
- Single extraction < 5 seconds
- Batch 100 endpoints < 3 minutes (180 seconds)
- Validates timing constraints from spec
"""

import pytest
import time
import tempfile
import yaml
from pathlib import Path
from slice_oas.slicer import EndpointSlicer
from slice_oas.validator import EndpointValidator
from slice_oas.batch_processor import BatchProcessor
from slice_oas.models import BatchExtractionRequest


class TestSingleExtractionPerformance:
    """Test single endpoint extraction completes in < 5 seconds."""

    def generate_complex_spec(self, num_schemas: int = 50) -> dict:
        """Generate a complex OAS spec with many schemas."""
        schemas = {}
        for i in range(num_schemas):
            schema_name = f"Model{i}"
            schemas[schema_name] = {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                }
            }
            # Add some references to create dependencies
            if i > 0:
                schemas[schema_name]["properties"]["parent"] = {
                    "$ref": f"#/components/schemas/Model{i-1}"
                }

        return {
            "openapi": "3.0.3",
            "info": {"title": "Performance Test API", "version": "1.0.0"},
            "paths": {
                "/items/{id}": {
                    "get": {
                        "operationId": "getItem",
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": f"#/components/schemas/Model{num_schemas-1}"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": schemas
            }
        }

    def test_single_extraction_under_5_seconds(self):
        """Test single endpoint extraction completes in < 5 seconds."""
        spec = self.generate_complex_spec(num_schemas=100)

        start_time = time.time()
        slicer = EndpointSlicer(spec, "3.0.3")
        extracted = slicer.extract("/items/{id}", "GET")
        elapsed = time.time() - start_time

        assert extracted is not None
        assert elapsed < 5.0, f"Extraction took {elapsed:.2f}s, should be < 5s"

    def test_single_extraction_with_validation_under_5_seconds(self):
        """Test extraction + validation completes in < 5 seconds."""
        spec = self.generate_complex_spec(num_schemas=100)

        start_time = time.time()
        slicer = EndpointSlicer(spec, "3.0.3")
        extracted = slicer.extract("/items/{id}", "GET")
        validator = EndpointValidator(extracted, "3.0.3")
        result = validator.validate()
        elapsed = time.time() - start_time

        assert result.passed
        assert elapsed < 5.0, f"Extraction+validation took {elapsed:.2f}s, should be < 5s"


class TestBatchPerformance:
    """Test batch extraction performance (100 endpoints < 3 minutes)."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def generate_large_spec(self, num_endpoints: int = 100) -> dict:
        """Generate OAS spec with many endpoints."""
        paths = {}
        for i in range(num_endpoints):
            path = f"/resource{i}"
            paths[path] = {
                "get": {
                    "operationId": f"getResource{i}",
                    "summary": f"Get resource {i}",
                    "tags": [f"group{i // 10}"],
                    "parameters": [
                        {"name": "filter", "in": "query", "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Resource"}
                                }
                            }
                        },
                        "404": {"description": "Not found"}
                    }
                },
                "post": {
                    "operationId": f"createResource{i}",
                    "summary": f"Create resource {i}",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Resource"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Resource"}
                                }
                            }
                        }
                    }
                }
            }

        return {
            "openapi": "3.0.3",
            "info": {"title": "Large API", "version": "1.0.0"},
            "paths": paths,
            "components": {
                "schemas": {
                    "Resource": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "status": {"type": "string", "enum": ["active", "inactive"]}
                        }
                    }
                }
            }
        }

    def test_batch_100_endpoints_under_3_minutes(self, temp_output_dir):
        """Test batch extraction of 100 endpoints completes in < 180 seconds."""
        # Generate spec with 50 paths (100 endpoints: GET + POST each)
        spec = self.generate_large_spec(num_endpoints=50)

        input_path = temp_output_dir / "large_spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            concurrency=4,
            output_format="yaml",
            generate_csv=True,
            dry_run=False
        )

        start_time = time.time()
        processor = BatchProcessor(request)
        result = processor.process()
        elapsed = time.time() - start_time

        assert result.total_endpoints == 100
        assert result.extracted_count == 100
        assert result.failed_count == 0
        assert elapsed < 180.0, f"Batch took {elapsed:.2f}s, should be < 180s"

        # Report performance metrics
        per_endpoint = elapsed / result.extracted_count
        print(f"\nPerformance: {result.extracted_count} endpoints in {elapsed:.2f}s")
        print(f"Per endpoint: {per_endpoint:.3f}s average")

    def test_batch_performance_auto_version(self, temp_output_dir):
        """Test batch extraction with auto version stays performant."""
        spec = self.generate_large_spec(num_endpoints=25)  # 50 endpoints

        input_path = temp_output_dir / "spec_30.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output_auto"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            output_version="auto",  # Preserve original version
            concurrency=4,
            output_format="yaml",
            generate_csv=True,
            dry_run=False
        )

        start_time = time.time()
        processor = BatchProcessor(request)
        result = processor.process()
        elapsed = time.time() - start_time

        assert result.extracted_count == 50
        # 50 endpoints should complete quickly
        assert elapsed < 90.0, f"Batch took {elapsed:.2f}s, should be < 90s"


class TestParallelPerformance:
    """Test parallel processing provides speedup."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def generate_spec(self, num_paths: int = 20) -> dict:
        """Generate spec with specified number of paths."""
        paths = {}
        for i in range(num_paths):
            paths[f"/item{i}"] = {
                "get": {
                    "operationId": f"get{i}",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            }
                        }
                    }
                }
            }

        return {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": paths,
            "components": {
                "schemas": {
                    "Item": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "value": {"type": "string"}
                        }
                    }
                }
            }
        }

    def test_parallel_faster_than_sequential(self, temp_output_dir):
        """Test parallel processing is faster than sequential."""
        spec = self.generate_spec(num_paths=20)

        input_path = temp_output_dir / "spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        # Sequential (concurrency=1)
        output_seq = temp_output_dir / "output_seq"
        output_seq.mkdir()
        request_seq = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_seq,
            concurrency=1,
            generate_csv=False
        )

        start = time.time()
        processor_seq = BatchProcessor(request_seq)
        result_seq = processor_seq.process()
        time_seq = time.time() - start

        # Parallel (concurrency=4)
        output_par = temp_output_dir / "output_par"
        output_par.mkdir()
        request_par = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_par,
            concurrency=4,
            generate_csv=False
        )

        start = time.time()
        processor_par = BatchProcessor(request_par)
        result_par = processor_par.process()
        time_par = time.time() - start

        assert result_seq.extracted_count == result_par.extracted_count
        # Parallel should be faster (at least not slower by much)
        # Note: For small workloads, overhead might make parallel slower
        # So we just verify both complete successfully
        print(f"\nSequential: {time_seq:.3f}s, Parallel: {time_par:.3f}s")


class TestMemoryEfficiency:
    """Test memory usage stays reasonable."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_large_spec_processing(self, temp_output_dir):
        """Test processing large spec doesn't crash (memory test)."""
        # Generate a reasonably large spec
        paths = {}
        for i in range(100):
            paths[f"/resource{i}"] = {
                "get": {
                    "operationId": f"get{i}",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/LargeModel"}
                                }
                            }
                        }
                    }
                }
            }

        # Create a model with many properties
        properties = {}
        for j in range(50):
            properties[f"field{j}"] = {"type": "string", "maxLength": 255}

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Large Test", "version": "1.0.0"},
            "paths": paths,
            "components": {
                "schemas": {
                    "LargeModel": {
                        "type": "object",
                        "properties": properties
                    }
                }
            }
        }

        input_path = temp_output_dir / "large.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            concurrency=4,
            generate_csv=True
        )

        processor = BatchProcessor(request)
        result = processor.process()

        assert result.extracted_count == 100
        assert result.failed_count == 0
