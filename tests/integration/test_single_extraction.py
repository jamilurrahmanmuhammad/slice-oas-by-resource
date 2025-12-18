"""Integration tests for single endpoint extraction (Phase 3 US1).

Tests the complete flow: extract endpoint → resolve references → validate → output.
"""

import pytest
import json
import yaml
from pathlib import Path
from slice_oas.parser import parse_oas, detect_oas_version
from slice_oas.resolver import ReferenceResolver
from slice_oas.slicer import EndpointSlicer
from slice_oas.validator import EndpointValidator
from slice_oas.generator import OASGenerator
from slice_oas.models import ValidationPhase


class TestSimpleEndpointExtraction:
    """Test extracting endpoint without schema references (T017)."""

    @pytest.fixture
    def simple_spec(self):
        """Simple OAS with single endpoint, no refs."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "Simple API", "version": "1.0.0"},
            "paths": {
                "/ping": {
                    "get": {
                        "summary": "Health check",
                        "operationId": "getPing",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def test_extract_simple_endpoint(self, simple_spec):
        """Test extracting endpoint with inline schema (no $ref)."""
        slicer = EndpointSlicer(simple_spec, "3.0.0")
        result = slicer.extract("/ping", "GET")

        assert result is not None
        assert result.get("paths", {}).get("/ping") is not None
        assert "operationId" in result["paths"]["/ping"]["get"]
        assert result["paths"]["/ping"]["get"]["operationId"] == "getPing"

    def test_simple_endpoint_has_valid_structure(self, simple_spec):
        """Test extracted endpoint is valid OAS document."""
        slicer = EndpointSlicer(simple_spec, "3.0.0")
        result = slicer.extract("/ping", "GET")

        # Must have required OAS fields
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result

    def test_simple_endpoint_preserves_metadata(self, simple_spec):
        """Test extracted endpoint preserves summary and operationId."""
        slicer = EndpointSlicer(simple_spec, "3.0.0")
        result = slicer.extract("/ping", "GET")

        operation = result["paths"]["/ping"]["get"]
        assert operation["summary"] == "Health check"
        assert operation["operationId"] == "getPing"


class TestDirectSchemaReferences:
    """Test extracting endpoint with direct $ref to schema (T018)."""

    @pytest.fixture
    def spec_with_refs(self):
        """OAS with endpoint referencing schemas."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "API with Refs", "version": "1.0.0"},
            "paths": {
                "/users/{id}": {
                    "get": {
                        "summary": "Get user by ID",
                        "operationId": "getUser",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
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
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        }
                    }
                }
            }
        }

    def test_resolve_direct_schema_reference(self, spec_with_refs):
        """Test resolver includes referenced schema in output."""
        resolver = ReferenceResolver(spec_with_refs, "3.0.0")
        refs = resolver.resolve_endpoint_refs("/users/{id}", "GET")

        # Should include User schema
        assert any("User" in str(ref) for ref in refs)

    def test_extracted_endpoint_includes_schema(self, spec_with_refs):
        """Test extracted endpoint includes resolved schemas."""
        slicer = EndpointSlicer(spec_with_refs, "3.0.0")
        result = slicer.extract("/users/{id}", "GET")

        # Should have components/schemas with User
        assert "components" in result
        assert "schemas" in result["components"]
        assert "User" in result["components"]["schemas"]
        assert result["components"]["schemas"]["User"]["type"] == "object"


class TestTransitiveSchemaDependencies:
    """Test extracting endpoint with transitive schema dependencies (T019)."""

    @pytest.fixture
    def spec_with_transitive_refs(self):
        """OAS with transitive schema dependencies (User -> Profile -> Contact)."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "API with Transitive Refs", "version": "1.0.0"},
            "paths": {
                "/users/{id}": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
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
                        "properties": {
                            "id": {"type": "integer"},
                            "profile": {"$ref": "#/components/schemas/Profile"}
                        }
                    },
                    "Profile": {
                        "type": "object",
                        "properties": {
                            "bio": {"type": "string"},
                            "contact": {"$ref": "#/components/schemas/Contact"}
                        }
                    },
                    "Contact": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "phone": {"type": "string"}
                        }
                    }
                }
            }
        }

    def test_resolve_transitive_dependencies(self, spec_with_transitive_refs):
        """Test resolver collects all transitive dependencies."""
        resolver = ReferenceResolver(spec_with_transitive_refs, "3.0.0")
        refs = resolver.resolve_endpoint_refs("/users/{id}", "GET")

        # Should include all three schemas
        schema_names = [str(ref) for ref in refs]
        assert any("User" in name for name in schema_names)
        assert any("Profile" in name for name in schema_names)
        assert any("Contact" in name for name in schema_names)

    def test_extracted_endpoint_includes_all_dependencies(self, spec_with_transitive_refs):
        """Test extracted endpoint includes all transitive dependencies."""
        slicer = EndpointSlicer(spec_with_transitive_refs, "3.0.0")
        result = slicer.extract("/users/{id}", "GET")

        schemas = result["components"]["schemas"]
        assert "User" in schemas
        assert "Profile" in schemas
        assert "Contact" in schemas


class TestCircularSchemaReferences:
    """Test extracting endpoint with circular schema references (T020)."""

    @pytest.fixture
    def spec_with_circular_refs(self):
        """OAS with circular schema references (Node references itself)."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "API with Circular Refs", "version": "1.0.0"},
            "paths": {
                "/nodes/{id}": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
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
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "children": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Node"}
                            }
                        }
                    }
                }
            }
        }

    def test_detect_circular_references(self, spec_with_circular_refs):
        """Test resolver detects and handles circular refs without infinite loop."""
        resolver = ReferenceResolver(spec_with_circular_refs, "3.0.0")
        refs = resolver.resolve_endpoint_refs("/nodes/{id}", "GET")

        # Should complete without hanging
        assert refs is not None
        # Node should be included
        assert any("Node" in str(ref) for ref in refs)

    def test_extracted_endpoint_handles_circular_refs(self, spec_with_circular_refs):
        """Test extracted endpoint with circular refs is valid."""
        slicer = EndpointSlicer(spec_with_circular_refs, "3.0.0")
        result = slicer.extract("/nodes/{id}", "GET")

        # Should have Node schema
        assert "Node" in result["components"]["schemas"]
        # Circular ref should be preserved
        node_schema = result["components"]["schemas"]["Node"]
        assert "children" in node_schema["properties"]


class TestResponseHeaderReferences:
    """Test extracting endpoint with $ref in response headers (T021).

    Constitutional requirement: scan responses[*].headers[*].$ref explicitly.
    """

    @pytest.fixture
    def spec_with_header_refs(self):
        """OAS with $ref in response headers."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "API with Header Refs", "version": "1.0.0"},
            "paths": {
                "/resources": {
                    "post": {
                        "responses": {
                            "201": {
                                "description": "Created",
                                "headers": {
                                    "X-Rate-Limit": {
                                        "description": "Rate limit header",
                                        "schema": {"$ref": "#/components/schemas/RateLimit"}
                                    }
                                },
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Resource"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Resource": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}}
                    },
                    "RateLimit": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer"},
                            "remaining": {"type": "integer"}
                        }
                    }
                }
            }
        }

    def test_scan_response_header_references(self, spec_with_header_refs):
        """Test resolver explicitly scans response headers for $ref."""
        resolver = ReferenceResolver(spec_with_header_refs, "3.0.0")
        refs = resolver.resolve_endpoint_refs("/resources", "POST")

        # Should include both Resource and RateLimit schemas
        schema_names = [str(ref) for ref in refs]
        assert any("Resource" in name for name in schema_names)
        assert any("RateLimit" in name for name in schema_names)

    def test_extracted_endpoint_includes_header_schemas(self, spec_with_header_refs):
        """Test extracted endpoint includes schemas from response headers."""
        slicer = EndpointSlicer(spec_with_header_refs, "3.0.0")
        result = slicer.extract("/resources", "POST")

        schemas = result["components"]["schemas"]
        assert "Resource" in schemas
        assert "RateLimit" in schemas


class TestJSONOutputFormat:
    """Test extracting endpoint and outputting as JSON (T022)."""

    @pytest.fixture
    def spec(self):
        """Basic OAS spec."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def test_generate_json_output(self, spec):
        """Test generator produces valid JSON output."""
        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/test", "GET")

        generator = OASGenerator(extracted, "3.0.0", "json")
        output = generator.generate()

        # Must be valid JSON
        parsed = json.loads(output)
        assert parsed["info"]["title"] == "API"

    def test_json_output_is_valid_oas(self, spec):
        """Test JSON output is valid OAS document."""
        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/test", "GET")

        generator = OASGenerator(extracted, "3.0.0", "json")
        output = generator.generate()
        parsed = json.loads(output)

        assert "openapi" in parsed
        assert "info" in parsed
        assert "paths" in parsed


class TestYAMLOutputFormat:
    """Test extracting endpoint and outputting as YAML (T023)."""

    @pytest.fixture
    def spec(self):
        """Basic OAS spec."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def test_generate_yaml_output(self, spec):
        """Test generator produces valid YAML output."""
        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/test", "GET")

        generator = OASGenerator(extracted, "3.0.0", "yaml")
        output = generator.generate()

        # Must be valid YAML
        parsed = yaml.safe_load(output)
        assert parsed["info"]["title"] == "API"

    def test_yaml_output_is_valid_oas(self, spec):
        """Test YAML output is valid OAS document."""
        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/test", "GET")

        generator = OASGenerator(extracted, "3.0.0", "yaml")
        output = generator.generate()
        parsed = yaml.safe_load(output)

        assert "openapi" in parsed
        assert "info" in parsed
        assert "paths" in parsed


class TestErrorHandling:
    """Test error handling for invalid inputs (T024)."""

    @pytest.fixture
    def spec(self):
        """Basic OAS spec."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def test_endpoint_not_found_error(self, spec):
        """Test extraction error when endpoint not found."""
        slicer = EndpointSlicer(spec, "3.0.0")

        # Should handle missing endpoint gracefully
        with pytest.raises((KeyError, ValueError)):
            slicer.extract("/nonexistent", "GET")

    def test_invalid_method_error(self, spec):
        """Test extraction error when method not found on endpoint."""
        slicer = EndpointSlicer(spec, "3.0.0")

        # /users exists but no POST method
        with pytest.raises((KeyError, ValueError)):
            slicer.extract("/users", "POST")

    def test_validation_failure_handling(self, spec):
        """Test validator reports validation failures."""
        slicer = EndpointSlicer(spec, "3.0.0")
        extracted = slicer.extract("/users", "GET")

        validator = EndpointValidator(extracted, "3.0.0")
        result = validator.validate()

        # Should return validation result (may pass or fail)
        assert result is not None
        assert hasattr(result, 'passed')
