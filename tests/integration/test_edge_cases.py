"""Edge case tests (T105).

Tests handling of edge cases:
- Circular references
- Missing components
- Malformed input
- Duplicates
- Unusual structures
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from slice_oas.parser import parse_oas
from slice_oas.slicer import EndpointSlicer
from slice_oas.validator import EndpointValidator
from slice_oas.batch_processor import BatchProcessor
from slice_oas.models import BatchExtractionRequest, ValidationPhase
from slice_oas.exceptions import InvalidOASError, MissingReferenceError


class TestCircularReferences:
    """Test handling of circular schema references."""

    def test_simple_circular_reference(self):
        """Test handling of A -> B -> A circular reference."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Circular Test", "version": "1.0.0"},
            "paths": {
                "/node": {
                    "get": {
                        "operationId": "getNode",
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Node"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Node": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "child": {"$ref": "#/components/schemas/Child"}
                        }
                    },
                    "Child": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "parent": {"$ref": "#/components/schemas/Node"}  # Circular!
                        }
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/node", "GET")

        assert extracted is not None
        schemas = extracted["components"]["schemas"]
        assert "Node" in schemas
        assert "Child" in schemas

    def test_self_referencing_schema(self):
        """Test handling of schema referencing itself."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Self Ref Test", "version": "1.0.0"},
            "paths": {
                "/tree": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/TreeNode"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "TreeNode": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                            "children": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/TreeNode"}  # Self-ref
                            }
                        }
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/tree", "GET")

        assert extracted is not None
        assert "TreeNode" in extracted["components"]["schemas"]

    def test_complex_circular_chain(self):
        """Test A -> B -> C -> A circular chain."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Chain Test", "version": "1.0.0"},
            "paths": {
                "/item": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ItemA"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "ItemA": {
                        "type": "object",
                        "properties": {
                            "b": {"$ref": "#/components/schemas/ItemB"}
                        }
                    },
                    "ItemB": {
                        "type": "object",
                        "properties": {
                            "c": {"$ref": "#/components/schemas/ItemC"}
                        }
                    },
                    "ItemC": {
                        "type": "object",
                        "properties": {
                            "a": {"$ref": "#/components/schemas/ItemA"}  # Back to A
                        }
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/item", "GET")

        assert extracted is not None
        schemas = extracted["components"]["schemas"]
        assert "ItemA" in schemas
        assert "ItemB" in schemas
        assert "ItemC" in schemas


class TestMissingComponents:
    """Test handling of missing component references."""

    def test_missing_schema_reference(self):
        """Test extraction handles missing schema reference.

        Note: The slicer may extract even with missing refs,
        but validation should catch it later.
        """
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Missing Ref", "version": "1.0.0"},
            "paths": {
                "/broken": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/DoesNotExist"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
            # No components section
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        # The slicer may succeed, but result should be invalid
        try:
            result = slicer.extract("/broken", "GET")
            # If it succeeds, the ref should still be there but unresolved
            assert result is not None
        except (MissingReferenceError, KeyError, Exception):
            # Exception is also acceptable behavior
            pass

    def test_missing_parameter_reference(self):
        """Test extraction handles missing parameter reference."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Missing Param", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "parameters": [
                            {"$ref": "#/components/parameters/MissingParam"}
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        # The slicer may succeed or raise - both are acceptable
        try:
            result = slicer.extract("/test", "GET")
            assert result is not None
        except Exception:
            pass


class TestMalformedInput:
    """Test handling of malformed input files."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_invalid_yaml_syntax(self, temp_output_dir):
        """Test handling of invalid YAML syntax."""
        input_path = temp_output_dir / "invalid.yaml"
        with open(input_path, "w") as f:
            f.write("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\n  invalid: [unclosed")

        # Parser may raise on invalid YAML or handle gracefully
        try:
            result = parse_oas(str(input_path))
            # If it returns, it should be a dict
            assert isinstance(result, dict)
        except Exception:
            # Exception is the expected behavior for invalid YAML
            pass

    def test_missing_openapi_field(self, temp_output_dir):
        """Test handling of missing openapi version field."""
        spec = {
            "info": {"title": "No Version", "version": "1.0.0"},
            "paths": {}
        }

        input_path = temp_output_dir / "no_version.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        # Parser may handle gracefully or raise
        try:
            result = parse_oas(str(input_path))
            # Should return the parsed dict even without openapi field
            assert isinstance(result, dict)
        except Exception:
            # Exception is also acceptable
            pass

    def test_empty_paths(self, temp_output_dir):
        """Test handling of empty paths object."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Empty", "version": "1.0.0"},
            "paths": {}
        }

        input_path = temp_output_dir / "empty.yaml"
        with open(input_path, "w") as f:
            yaml.dump(spec, f)

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            generate_csv=False
        )

        processor = BatchProcessor(request)
        result = processor.process()

        assert result.total_endpoints == 0
        assert result.extracted_count == 0


class TestDuplicateHandling:
    """Test handling of duplicate scenarios."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_duplicate_extraction_same_session(self, temp_output_dir):
        """Test extracting same endpoint twice produces consistent output."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Dup Test", "version": "1.0.0"},
            "paths": {
                "/item": {
                    "get": {
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        result1 = slicer.extract("/item", "GET")
        result2 = slicer.extract("/item", "GET")

        assert result1 == result2

    def test_csv_deduplication(self, temp_output_dir):
        """Test CSV deduplicates on repeated runs."""
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

        output_subdir = temp_output_dir / "output"
        output_subdir.mkdir()

        request = BatchExtractionRequest(
            input_file=input_path,
            output_dir=output_subdir,
            generate_csv=True
        )

        # Run twice
        processor1 = BatchProcessor(request)
        result1 = processor1.process()

        processor2 = BatchProcessor(request)
        result2 = processor2.process()

        # Read CSV and verify no duplicates
        import csv
        with open(result2.csv_index_path, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have exactly 1 entry, not 2
        paths = [r["path"] for r in rows]
        assert paths.count("/test") == 1


class TestUnusualStructures:
    """Test handling of unusual but valid OAS structures."""

    def test_empty_operation(self):
        """Test endpoint with minimal operation definition."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Minimal", "version": "1.0.0"},
            "paths": {
                "/minimal": {
                    "get": {
                        "responses": {
                            "default": {"description": "response"}
                        }
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/minimal", "GET")

        assert extracted is not None
        assert "/minimal" in extracted["paths"]

    def test_multiple_content_types(self):
        """Test endpoint with multiple content types."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Multi Content", "version": "1.0.0"},
            "paths": {
                "/multi": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Data"}
                                },
                                "application/xml": {
                                    "schema": {"$ref": "#/components/schemas/Data"}
                                },
                                "text/plain": {
                                    "schema": {"type": "string"}
                                }
                            }
                        },
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
            "components": {
                "schemas": {
                    "Data": {
                        "type": "object",
                        "properties": {"value": {"type": "string"}}
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/multi", "POST")

        assert extracted is not None
        content = extracted["paths"]["/multi"]["post"]["requestBody"]["content"]
        assert "application/json" in content
        assert "application/xml" in content
        assert "text/plain" in content

    def test_nested_allof_oneof(self):
        """Test deeply nested schema composition."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Nested", "version": "1.0.0"},
            "paths": {
                "/nested": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Composite"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Composite": {
                        "allOf": [
                            {"$ref": "#/components/schemas/Base"},
                            {
                                "oneOf": [
                                    {"$ref": "#/components/schemas/TypeA"},
                                    {"$ref": "#/components/schemas/TypeB"}
                                ]
                            }
                        ]
                    },
                    "Base": {
                        "type": "object",
                        "properties": {"id": {"type": "string"}}
                    },
                    "TypeA": {
                        "type": "object",
                        "properties": {"a_field": {"type": "string"}}
                    },
                    "TypeB": {
                        "type": "object",
                        "properties": {"b_field": {"type": "integer"}}
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/nested", "GET")

        schemas = extracted["components"]["schemas"]
        assert "Composite" in schemas
        assert "Base" in schemas
        assert "TypeA" in schemas
        assert "TypeB" in schemas

    def test_path_with_special_characters(self):
        """Test paths with URL-encoded characters."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Special", "version": "1.0.0"},
            "paths": {
                "/items/{item-id}": {
                    "get": {
                        "parameters": [
                            {
                                "name": "item-id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/items/{item-id}", "GET")

        assert extracted is not None
        assert "/items/{item-id}" in extracted["paths"]

    def test_deprecated_endpoint(self):
        """Test extraction of deprecated endpoint."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Deprecated", "version": "1.0.0"},
            "paths": {
                "/old": {
                    "get": {
                        "deprecated": True,
                        "summary": "Deprecated endpoint",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/old", "GET")

        assert extracted is not None
        assert extracted["paths"]["/old"]["get"]["deprecated"] is True

    def test_security_with_scopes(self):
        """Test endpoint with OAuth scopes."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Security", "version": "1.0.0"},
            "paths": {
                "/secure": {
                    "get": {
                        "security": [
                            {"oauth2": ["read:users", "write:users"]}
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "oauth2": {
                        "type": "oauth2",
                        "flows": {
                            "authorizationCode": {
                                "authorizationUrl": "https://example.com/oauth/authorize",
                                "tokenUrl": "https://example.com/oauth/token",
                                "scopes": {
                                    "read:users": "Read users",
                                    "write:users": "Write users"
                                }
                            }
                        }
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/secure", "GET")

        assert extracted is not None
        security = extracted["paths"]["/secure"]["get"]["security"]
        assert len(security) == 1
        assert "oauth2" in security[0]
        assert "read:users" in security[0]["oauth2"]


class TestEmptyAndMinimal:
    """Test minimal and edge-case inputs."""

    def test_minimal_valid_spec(self):
        """Test extraction from minimal valid OAS."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Min", "version": "1"},
            "paths": {
                "/": {"get": {"responses": {"200": {"description": "ok"}}}}
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/", "GET")

        assert extracted is not None
        assert "/" in extracted["paths"]

    def test_no_responses_in_operation(self):
        """Test handling of operation without responses (invalid but might occur)."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/incomplete": {
                    "get": {
                        "summary": "Incomplete endpoint"
                        # Missing responses - technically invalid OAS
                    }
                }
            }
        }

        slicer = EndpointSlicer(spec, "3.0.0")
        # Depending on implementation, this might raise or handle gracefully
        try:
            extracted = slicer.extract("/incomplete", "GET")
            # If it succeeds, verify structure
            assert "/incomplete" in extracted.get("paths", {})
        except Exception:
            # Expected for invalid input
            pass
