"""End-to-end integration tests for complete workflow (T102).

Tests the full pipeline: input → extraction → validation → output → CSV.
Verifies all components work together seamlessly.
"""

import pytest
import tempfile
import yaml
import csv
from pathlib import Path
from slice_oas.parser import parse_oas, detect_oas_version
from slice_oas.slicer import EndpointSlicer
from slice_oas.validator import EndpointValidator
from slice_oas.generator import OASGenerator
from slice_oas.batch_processor import BatchProcessor
from slice_oas.models import BatchExtractionRequest, ValidationPhase
from slice_oas.csv_manager import CSVIndexManager


class TestCompleteWorkflow:
    """Test complete extraction workflow from start to finish."""

    @pytest.fixture
    def complete_oas_spec(self):
        """Create a complete OAS spec for end-to-end testing."""
        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Complete E2E Test API",
                "version": "1.0.0",
                "description": "API for end-to-end workflow testing"
            },
            "servers": [
                {"url": "https://api.example.com/v1"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List all users",
                        "operationId": "listUsers",
                        "tags": ["users"],
                        "parameters": [
                            {"name": "page", "in": "query", "schema": {"type": "integer"}},
                            {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "summary": "Create a new user",
                        "operationId": "createUser",
                        "tags": ["users"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "User created",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    }
                },
                "/users/{userId}": {
                    "get": {
                        "summary": "Get user by ID",
                        "operationId": "getUser",
                        "tags": ["users"],
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "integer"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "User found",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    },
                    "put": {
                        "summary": "Update user",
                        "operationId": "updateUser",
                        "tags": ["users"],
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "integer"}}
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "User updated",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    "delete": {
                        "summary": "Delete user",
                        "operationId": "deleteUser",
                        "tags": ["users"],
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "integer"}}
                        ],
                        "responses": {
                            "204": {
                                "description": "User deleted"
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    }
                },
                "/products": {
                    "get": {
                        "summary": "List products",
                        "operationId": "listProducts",
                        "tags": ["products"],
                        "responses": {
                            "200": {
                                "description": "Product list",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Product"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "required": ["id", "email"],
                        "properties": {
                            "id": {"type": "integer"},
                            "email": {"type": "string", "format": "email"},
                            "name": {"type": "string"}
                        }
                    },
                    "Product": {
                        "type": "object",
                        "required": ["id", "name", "price"],
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "price": {"type": "number", "format": "float"}
                        }
                    }
                },
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_input_file(self, complete_oas_spec, temp_output_dir):
        """Write spec to temporary input file."""
        input_path = temp_output_dir / "input_spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(complete_oas_spec, f)
        return input_path

    def test_single_extraction_complete_flow(self, complete_oas_spec, temp_output_dir):
        """Test complete single endpoint extraction workflow."""
        # Step 1: Parse input
        version = detect_oas_version(complete_oas_spec)
        assert version == "3.0.x"

        # Step 2: Extract endpoint
        slicer = EndpointSlicer(complete_oas_spec, "3.0.3")
        extracted = slicer.extract("/users/{userId}", "GET")
        assert extracted is not None

        # Step 3: Validate extracted document
        validator = EndpointValidator(extracted, "3.0.3")
        result = validator.validate()
        assert result.passed, f"Validation failed: {result.error_message}"

        # Step 4: Generate output
        output_path = temp_output_dir / "get_users_userid.yaml"
        generator = OASGenerator(extracted, "3.0.3", format="yaml")
        output_content = generator.generate()
        with open(output_path, "w") as f:
            f.write(output_content)
        assert output_path.exists()

        # Step 5: Verify output is valid OAS
        with open(output_path) as f:
            output_doc = yaml.safe_load(f)
        assert output_doc["openapi"] == "3.0.3"
        assert "/users/{userId}" in output_doc["paths"]
        assert "components" in output_doc
        assert "User" in output_doc["components"]["schemas"]

    def test_batch_extraction_complete_flow(self, temp_input_file, temp_output_dir):
        """Test complete batch extraction workflow with CSV."""
        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        # Create batch request
        request = BatchExtractionRequest(
            input_file=temp_input_file,
            output_dir=output_subdir,
            filter_pattern="/users*",
            filter_type="glob",
            output_version="auto",
            concurrency=2,
            output_format="yaml",
            generate_csv=True,
            dry_run=False
        )

        # Execute batch processing
        processor = BatchProcessor(request)
        result = processor.process()

        # Verify results
        assert result.extracted_count >= 4  # 4 user endpoints
        assert result.failed_count == 0
        assert result.validation_pass_rate == 1.0  # 100% as fraction

        # Verify output files exist
        yaml_files = list(output_subdir.glob("*.yaml"))
        assert len(yaml_files) >= 4

        # Verify CSV index
        assert result.csv_index_path is not None
        assert result.csv_index_path.exists()

        # Verify CSV content
        with open(result.csv_index_path, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 4
            assert all(row["path"].startswith("/users") for row in rows)

    def test_batch_with_auto_version(self, temp_input_file, temp_output_dir):
        """Test batch extraction preserving auto version."""
        output_subdir = temp_output_dir / "output_auto"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=temp_input_file,
            output_dir=output_subdir,
            filter_pattern="/products*",
            filter_type="glob",
            output_version="auto",  # Preserve original version
            concurrency=1,
            output_format="yaml",
            generate_csv=True,
            dry_run=False
        )

        processor = BatchProcessor(request)
        result = processor.process()

        assert result.extracted_count >= 1
        assert result.failed_count == 0

        # Verify output preserves version
        yaml_files = list(output_subdir.glob("*.yaml"))
        assert len(yaml_files) >= 1
        with open(yaml_files[0]) as f:
            doc = yaml.safe_load(f)
        assert doc["openapi"].startswith("3.0")

    def test_all_endpoints_extracted(self, complete_oas_spec, temp_output_dir):
        """Test extracting all endpoints from spec."""
        # Write spec to file
        input_path = temp_output_dir / "full_spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(complete_oas_spec, f)

        output_subdir = temp_output_dir / "all_output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            filter_pattern=None,  # No filter = all
            output_version="auto",
            concurrency=4,
            output_format="yaml",
            generate_csv=True,
            dry_run=False
        )

        processor = BatchProcessor(request)
        result = processor.process()

        # 6 total endpoints: GET/POST /users, GET/PUT/DELETE /users/{userId}, GET /products
        assert result.total_endpoints == 6
        assert result.extracted_count == 6
        assert result.failed_count == 0
        assert result.validation_pass_rate == 1.0  # 100% as fraction


class TestWorkflowErrorHandling:
    """Test error handling in complete workflow."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_invalid_endpoint_extraction(self):
        """Test handling of non-existent endpoint."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/exists": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        with pytest.raises(Exception):
            slicer.extract("/does-not-exist", "GET")

    def test_invalid_method_extraction(self):
        """Test handling of non-existent method."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/exists": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        with pytest.raises(Exception):
            slicer.extract("/exists", "POST")  # POST doesn't exist

    def test_batch_with_failures_continues(self, temp_output_dir):
        """Test batch processing continues despite individual failures."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Mixed API", "version": "1.0.0"},
            "paths": {
                "/valid": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                },
                "/also-valid": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }

        input_path = temp_output_dir / "spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            output_version="auto",
            concurrency=2,
            output_format="yaml",
            generate_csv=True,
            dry_run=False
        )

        processor = BatchProcessor(request)
        result = processor.process()

        # Both endpoints should succeed
        assert result.extracted_count == 2
        assert result.failed_count == 0


class TestWorkflowValidation:
    """Test validation at each stage of workflow."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_all_validation_phases_pass(self):
        """Test all 7 validation phases pass for valid extraction."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "getTest",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/TestModel"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "TestModel": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"}
                        }
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/test", "GET")

        validator = EndpointValidator(extracted, "3.0.0")
        result = validator.validate()

        # Should pass validation
        assert result.passed, f"Validation failed: {result.error_message}"

    def test_validation_detects_missing_component(self):
        """Test validation catches missing referenced component."""
        # Manually create doc with broken reference
        broken_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Missing"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
            # Missing components section entirely
        }

        validator = EndpointValidator(broken_doc, "3.0.0")
        result = validator.validate()

        # Should fail validation due to missing reference
        assert not result.passed, "Validation should fail for missing component"


class TestCSVIndexIntegration:
    """Test CSV index generation in complete workflow."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_csv_contains_all_columns(self, temp_output_dir):
        """Test CSV has all 15 required columns."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "operationId": "testOp",
                        "tags": ["test"],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }

        input_path = temp_output_dir / "spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            generate_csv=True
        )

        processor = BatchProcessor(request)
        result = processor.process()

        # Check CSV columns
        with open(result.csv_index_path, newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)

        expected_headers = [
            "path", "method", "summary", "description", "operation_id",
            "tags", "filename", "file_size_kb", "schema_count", "parameter_count",
            "response_codes", "security_required", "deprecated", "created_at",
            "output_oas_version"
        ]
        assert headers == expected_headers

    def test_csv_metadata_accuracy(self, temp_output_dir):
        """Test CSV metadata values are accurate."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/users/{id}": {
                    "get": {
                        "summary": "Get user",
                        "operationId": "getUser",
                        "tags": ["users", "public"],
                        "deprecated": True,
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            },
                            "404": {"description": "Not found"}
                        },
                        "security": [{"apiKey": []}]
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"}
                        }
                    }
                },
                "securitySchemes": {
                    "apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"}
                }
            }
        }

        input_path = temp_output_dir / "spec.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            generate_csv=True
        )

        processor = BatchProcessor(request)
        result = processor.process()

        with open(result.csv_index_path, newline='') as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["path"] == "/users/{id}"
        assert row["method"] == "GET"
        assert row["summary"] == "Get user"
        assert row["operation_id"] == "getUser"
        assert "users" in row["tags"]
        assert row["deprecated"] == "yes"
        assert row["security_required"] == "yes"
        assert "200" in row["response_codes"]
        assert "404" in row["response_codes"]
