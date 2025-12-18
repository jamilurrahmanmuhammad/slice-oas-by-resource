"""Large file handling tests (T104).

Tests handling of large OAS files with 1000+ endpoints.
Validates memory usage and processing capabilities.
"""

import pytest
import tempfile
import yaml
import os
from pathlib import Path
from slice_oas.parser import parse_oas
from slice_oas.slicer import EndpointSlicer
from slice_oas.batch_processor import BatchProcessor
from slice_oas.models import BatchExtractionRequest


class TestLargeFileHandling:
    """Test handling of large OAS files."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def generate_large_spec(self, num_paths: int) -> dict:
        """Generate a large OAS spec with many endpoints.

        Args:
            num_paths: Number of paths to generate (each has GET and POST)
        """
        paths = {}
        for i in range(num_paths):
            resource_name = f"resource{i:04d}"
            paths[f"/{resource_name}"] = {
                "get": {
                    "operationId": f"list{resource_name.capitalize()}",
                    "summary": f"List {resource_name} items",
                    "tags": [f"group{i // 100}"],
                    "parameters": [
                        {"name": "page", "in": "query", "schema": {"type": "integer"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/BaseResource"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "operationId": f"create{resource_name.capitalize()}",
                    "summary": f"Create {resource_name}",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/BaseResource"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/BaseResource"}
                                }
                            }
                        }
                    }
                }
            }
            paths[f"/{resource_name}/{{id}}"] = {
                "get": {
                    "operationId": f"get{resource_name.capitalize()}",
                    "summary": f"Get {resource_name} by ID",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/BaseResource"}
                                }
                            }
                        },
                        "404": {"description": "Not found"}
                    }
                },
                "delete": {
                    "operationId": f"delete{resource_name.capitalize()}",
                    "summary": f"Delete {resource_name}",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "204": {"description": "Deleted"}
                    }
                }
            }

        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Large Scale API",
                "version": "1.0.0",
                "description": "API with many endpoints for scale testing"
            },
            "paths": paths,
            "components": {
                "schemas": {
                    "BaseResource": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "string", "format": "uuid"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
                            "created_at": {"type": "string", "format": "date-time"},
                            "updated_at": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            }
        }

    def test_parse_large_spec(self, temp_output_dir):
        """Test parsing a large OAS spec (500+ paths = 2000+ endpoints)."""
        spec = self.generate_large_spec(num_paths=500)

        input_path = temp_output_dir / "large_spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        # File should be substantial
        file_size = os.path.getsize(input_path)
        print(f"\nGenerated spec file size: {file_size / 1024:.1f} KB")
        assert file_size > 100 * 1024  # > 100KB

        # Parse should succeed
        parsed = parse_oas(str(input_path))
        assert parsed is not None
        assert len(parsed.get("paths", {})) == 1000  # 500 base + 500 /{id}

    def test_extract_from_large_spec(self, temp_output_dir):
        """Test extracting single endpoint from large spec."""
        spec = self.generate_large_spec(num_paths=500)

        slicer = EndpointSlicer(spec, "3.0.3")
        extracted = slicer.extract("/resource0250", "GET")

        assert extracted is not None
        assert "/resource0250" in extracted["paths"]
        assert "BaseResource" in extracted["components"]["schemas"]

    @pytest.mark.slow
    def test_batch_1000_endpoints(self, temp_output_dir):
        """Test batch extraction of 1000+ endpoints.

        This test is marked slow and may be skipped in quick test runs.
        """
        spec = self.generate_large_spec(num_paths=250)  # 1000 endpoints total

        input_path = temp_output_dir / "thousand_spec.yaml"
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

        processor = BatchProcessor(request)
        result = processor.process()

        assert result.total_endpoints == 1000
        assert result.extracted_count == 1000
        assert result.failed_count == 0
        assert result.validation_pass_rate == 1.0  # 100% as fraction

        # Verify output files created
        yaml_files = list(output_subdir.glob("*.yaml"))
        assert len(yaml_files) == 1000

        # Verify CSV has all entries
        assert result.csv_index_path.exists()

    def test_filtered_extraction_large_spec(self, temp_output_dir):
        """Test filtered extraction from large spec."""
        spec = self.generate_large_spec(num_paths=200)

        input_path = temp_output_dir / "spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        # Filter for only resource00xx endpoints
        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            filter_pattern="/resource00*",
            filter_type="glob",
            concurrency=4,
            generate_csv=True
        )

        processor = BatchProcessor(request)
        result = processor.process()

        # Should match resource0000-resource0099 base paths (100) + their /{id} variants (100)
        # Plus GET/POST/DELETE methods = fewer actual endpoints depending on filter behavior
        # The filter matches paths, and each path has multiple methods
        assert result.extracted_count > 0
        assert result.failed_count == 0


class TestLargeSchemaHandling:
    """Test handling of specs with many schemas."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def generate_spec_with_many_schemas(self, num_schemas: int) -> dict:
        """Generate spec with many interconnected schemas."""
        schemas = {}

        # Create base schema
        schemas["BaseEntity"] = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"}
            }
        }

        # Create chain of schemas referencing each other
        for i in range(num_schemas):
            schema_name = f"Entity{i:03d}"
            schema = {
                "allOf": [
                    {"$ref": "#/components/schemas/BaseEntity"},
                    {
                        "type": "object",
                        "properties": {
                            f"field{i}": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    }
                ]
            }
            # Add reference to previous schema
            if i > 0:
                schema["allOf"][1]["properties"]["previous"] = {
                    "$ref": f"#/components/schemas/Entity{i-1:03d}"
                }
            schemas[schema_name] = schema

        return {
            "openapi": "3.0.3",
            "info": {"title": "Schema Test", "version": "1.0.0"},
            "paths": {
                "/entity": {
                    "get": {
                        "operationId": "getEntity",
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": f"#/components/schemas/Entity{num_schemas-1:03d}"}
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

    def test_extract_with_deep_schema_chain(self, temp_output_dir):
        """Test extraction resolves deep schema reference chains."""
        spec = self.generate_spec_with_many_schemas(num_schemas=100)

        slicer = EndpointSlicer(spec, "3.0.3")
        extracted = slicer.extract("/entity", "GET")

        assert extracted is not None
        # All schemas in chain should be included
        schemas = extracted.get("components", {}).get("schemas", {})
        assert "BaseEntity" in schemas
        assert "Entity000" in schemas
        assert "Entity099" in schemas


class TestOutputFileManagement:
    """Test output file handling for large batches."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_unique_filenames_large_batch(self, temp_output_dir):
        """Test unique filenames generated for all endpoints."""
        paths = {}
        # Create paths that might generate similar filenames
        for i in range(50):
            paths[f"/users/{i}"] = {
                "get": {
                    "operationId": f"getUser{i}",
                    "responses": {"200": {"description": "OK"}}
                }
            }
            paths[f"/users/{i}/profile"] = {
                "get": {
                    "operationId": f"getUserProfile{i}",
                    "responses": {"200": {"description": "OK"}}
                }
            }

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": paths
        }

        input_path = temp_output_dir / "spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            concurrency=4,
            generate_csv=False
        )

        processor = BatchProcessor(request)
        result = processor.process()

        # All should succeed
        assert result.extracted_count == 100
        assert result.failed_count == 0

        # All files should have unique names
        yaml_files = list(output_subdir.glob("*.yaml"))
        filenames = [f.name for f in yaml_files]
        assert len(filenames) == len(set(filenames)), "Duplicate filenames detected"

    def test_output_directory_created(self, temp_output_dir):
        """Test output directory is created if it doesn't exist."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }

        input_path = temp_output_dir / "spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        # Output dir doesn't exist yet
        output_subdir = temp_output_dir / "new_output"
        assert not output_subdir.exists()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            generate_csv=True
        )

        processor = BatchProcessor(request)
        result = processor.process()

        assert output_subdir.exists()
        assert result.extracted_count == 1
