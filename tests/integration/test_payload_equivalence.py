"""Integration tests for Validation Phase 6: Payload Equivalence.

Tests verify that the validator detects when extracted endpoints are missing
components that are referenced via $ref.

User Story 6 (US6): Payload Equivalence Validation
Per FR-011: Validation Phase 6 MUST compare extracted endpoint against parent
to verify all required components are included.

Follows TDD approach per FR-016 through FR-020.
"""

import pytest
from slice_oas.validator import EndpointValidator
from slice_oas.models import ValidationPhase


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def complete_original_doc():
    """A complete OAS document with all component types.

    Note: Responses are inlined rather than using $ref to avoid Phase 3
    validation issues (Phase 3 expects description on response objects,
    but $ref objects don't contain description).
    """
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUser",
                    "parameters": [
                        {"$ref": "#/components/parameters/userId"}
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "headers": {
                                "X-Rate-Limit": {"$ref": "#/components/headers/X-Rate-Limit"}
                            },
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
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
                        "name": {"type": "string"}
                    }
                },
                "Error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "message": {"type": "string"}
                    }
                }
            },
            "headers": {
                "X-Rate-Limit": {
                    "description": "Rate limit header",
                    "schema": {"type": "integer"}
                }
            },
            "parameters": {
                "userId": {
                    "name": "userId",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"}
                }
            },
            "responses": {
                "NotFound": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def complete_extracted_doc():
    """A properly extracted document with all referenced components included."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUser",
                    "parameters": [
                        {"$ref": "#/components/parameters/userId"}
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "headers": {
                                "X-Rate-Limit": {"$ref": "#/components/headers/X-Rate-Limit"}
                            },
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
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
                        "name": {"type": "string"}
                    }
                },
                "Error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "message": {"type": "string"}
                    }
                }
            },
            "headers": {
                "X-Rate-Limit": {
                    "description": "Rate limit header",
                    "schema": {"type": "integer"}
                }
            },
            "parameters": {
                "userId": {
                    "name": "userId",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"}
                }
            },
            "responses": {
                "NotFound": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"}
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def extracted_missing_header():
    """Extracted document missing a header component but still referencing it."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUser",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "headers": {
                                # This $ref points to a header NOT in components
                                "X-Rate-Limit": {"$ref": "#/components/headers/X-Rate-Limit"}
                            },
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
                    "properties": {"id": {"type": "integer"}}
                }
            }
            # NOTE: headers section is MISSING - X-Rate-Limit not included
        }
    }


@pytest.fixture
def extracted_missing_schema():
    """Extracted document missing a schema component but still referencing it."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUser",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    # This $ref points to a schema NOT in components
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
                # NOTE: User schema is MISSING despite being referenced
            }
        }
    }


@pytest.fixture
def extracted_missing_response():
    """Extracted document with a response that refs a missing schema."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUser",
                    "responses": {
                        "200": {
                            "description": "Success"
                        },
                        "404": {
                            "description": "Not found",
                            "content": {
                                "application/json": {
                                    # This $ref points to a schema NOT in components
                                    "schema": {"$ref": "#/components/schemas/NotFoundError"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            # NOTE: schemas.NotFoundError is MISSING
        }
    }


@pytest.fixture
def extracted_missing_parameter():
    """Extracted document missing a parameter component."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "getUser",
                    "parameters": [
                        # This $ref points to a parameter NOT in components
                        {"$ref": "#/components/parameters/userId"}
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        },
        "components": {
            # NOTE: parameters section is MISSING
        }
    }


# ============================================================================
# User Story 6: Payload Equivalence Validation (T039-T048)
# ============================================================================

class TestPayloadEquivalenceValidation:
    """Tests for Validation Phase 6: Payload Equivalence.

    Verifies FR-011: Validation Phase 6 compares extracted endpoint against
    parent to verify all required components are included.
    """

    def test_phase6_passes_when_all_refs_present(
        self, complete_extracted_doc, complete_original_doc
    ):
        """T039: Phase 6 passes when all referenced components are present.

        Given a complete extraction with all $ref targets included,
        When validation runs,
        Then Phase 6 should pass.
        """
        validator = EndpointValidator(
            doc=complete_extracted_doc,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        # Should pass all phases including Phase 6
        assert result.passed, f"Validation failed: {result.error_message}"
        # Verify we got to or past Phase 6
        assert result.phase.value >= ValidationPhase.PAYLOAD_EQUIVALENCE.value

    def test_phase6_fails_when_header_missing(
        self, extracted_missing_header, complete_original_doc
    ):
        """T040: Phase 6 fails when a header component is missing.

        Given an extracted document with $ref: "#/components/headers/X-Rate-Limit"
        But the headers section does not contain X-Rate-Limit,
        When validation runs,
        Then Phase 6 should fail indicating the missing header.

        Verifies FR-012: Validation Phase 6 fails with specific error message.
        """
        validator = EndpointValidator(
            doc=extracted_missing_header,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        # Should fail at Phase 4 (Reference Resolution) or Phase 6
        assert not result.passed, "Expected validation to fail for missing header"
        assert result.phase in [
            ValidationPhase.REFERENCE_RESOLUTION,
            ValidationPhase.PAYLOAD_EQUIVALENCE
        ]
        assert "X-Rate-Limit" in result.error_message or "headers" in result.error_message

    def test_phase6_fails_when_schema_missing(
        self, extracted_missing_schema, complete_original_doc
    ):
        """T041: Phase 6 fails when a schema component is missing.

        Given an extracted document with $ref: "#/components/schemas/User"
        But the schemas section does not contain User,
        When validation runs,
        Then Phase 6 should fail indicating the missing schema.
        """
        validator = EndpointValidator(
            doc=extracted_missing_schema,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        # Should fail at Phase 4 or Phase 6
        assert not result.passed, "Expected validation to fail for missing schema"
        assert result.phase in [
            ValidationPhase.REFERENCE_RESOLUTION,
            ValidationPhase.PAYLOAD_EQUIVALENCE
        ]
        assert "User" in result.error_message or "schemas" in result.error_message

    def test_phase6_returns_specific_error_message(
        self, extracted_missing_header, complete_original_doc
    ):
        """T042: Phase 6 returns a specific, actionable error message.

        Given a validation failure due to missing component,
        When the error message is returned,
        Then it should clearly identify:
        - The component type (headers, schemas, etc.)
        - The component name (X-Rate-Limit, User, etc.)

        Verifies FR-012: Specific error message when component is missing.
        """
        validator = EndpointValidator(
            doc=extracted_missing_header,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        assert not result.passed
        # Error message should be specific and actionable
        error_msg = result.error_message.lower()

        # Should mention the reference that failed
        assert "ref" in error_msg or "reference" in error_msg or "x-rate-limit" in error_msg

        # Should indicate what's missing
        assert "not found" in error_msg or "missing" in error_msg or "header" in error_msg


class TestPayloadEquivalenceWithoutOriginal:
    """Tests for Phase 6 behavior when original_doc is not provided."""

    def test_phase6_passes_without_original_doc(self, complete_extracted_doc):
        """Phase 6 passes (skipped) when no original_doc provided.

        The original_doc is optional; if not provided, Phase 6
        assumes extraction is valid.
        """
        validator = EndpointValidator(
            doc=complete_extracted_doc,
            version="3.0.3",
            original_doc=None  # No original provided
        )

        result = validator.validate()

        # Should pass - Phase 6 is effectively skipped
        assert result.passed


class TestPayloadEquivalenceAllComponentTypes:
    """Tests for Phase 6 validation across all component types."""

    def test_missing_response_schema_detected(
        self, extracted_missing_response, complete_original_doc
    ):
        """Missing schema in response is detected by validation."""
        validator = EndpointValidator(
            doc=extracted_missing_response,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        assert not result.passed
        assert "NotFoundError" in result.error_message or "schemas" in result.error_message

    def test_missing_parameter_detected(
        self, extracted_missing_parameter, complete_original_doc
    ):
        """Missing parameter component is detected by validation."""
        validator = EndpointValidator(
            doc=extracted_missing_parameter,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        assert not result.passed
        assert "userId" in result.error_message or "parameters" in result.error_message


class TestPayloadEquivalenceEdgeCases:
    """Edge case tests for Phase 6 validation."""

    def test_transitive_dependency_missing(self, complete_original_doc):
        """Transitive dependency chain failure is detected.

        If a header references a schema, and that schema is missing,
        validation should fail.
        """
        extracted_with_missing_transitive = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users/{userId}": {
                    "get": {
                        "operationId": "getUser",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "headers": {
                                    "X-Custom": {"$ref": "#/components/headers/X-Custom"}
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "headers": {
                    "X-Custom": {
                        "description": "Custom header",
                        # This refs a schema which is MISSING
                        "schema": {"$ref": "#/components/schemas/CustomType"}
                    }
                }
                # NOTE: schemas.CustomType is MISSING (transitive dependency)
            }
        }

        validator = EndpointValidator(
            doc=extracted_with_missing_transitive,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        assert not result.passed
        assert "CustomType" in result.error_message or "schemas" in result.error_message

    def test_multiple_missing_components(self, complete_original_doc):
        """Multiple missing components are detected."""
        extracted_multiple_missing = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users/{userId}": {
                    "get": {
                        "operationId": "getUser",
                        "parameters": [
                            {"$ref": "#/components/parameters/userId"}
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "headers": {
                                    "X-Rate-Limit": {"$ref": "#/components/headers/X-Rate-Limit"}
                                },
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
                # ALL components are MISSING
            }
        }

        validator = EndpointValidator(
            doc=extracted_multiple_missing,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        # Should fail - at least one missing component detected
        assert not result.passed

    def test_path_mismatch_detected(self, complete_original_doc):
        """Extracted path not in original is detected."""
        extracted_wrong_path = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                # This path doesn't exist in original
                "/nonexistent/path": {
                    "get": {
                        "operationId": "getNothing",
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            }
        }

        validator = EndpointValidator(
            doc=extracted_wrong_path,
            version="3.0.3",
            original_doc=complete_original_doc
        )

        result = validator.validate()

        assert not result.passed
        assert "nonexistent" in result.error_message.lower() or "path" in result.error_message.lower()
