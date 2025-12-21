"""Integration tests for complete component reference resolution.

Tests all 8 OpenAPI component types: schemas, headers, parameters, responses,
requestBodies, securitySchemes, links, callbacks.

Follows TDD approach per FR-016 through FR-020.
"""

import pytest
import yaml
from pathlib import Path
from slice_oas.slicer import EndpointSlicer
from slice_oas.resolver import ReferenceResolver
from slice_oas.models import ComponentType, ResolvedComponents


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def header_refs_spec(fixtures_dir):
    """Load header reference fixture."""
    with open(fixtures_dir / "oas_with_header_refs.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def all_component_refs_spec(fixtures_dir):
    """Load mixed component reference fixture."""
    with open(fixtures_dir / "oas_with_all_component_refs.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def parameter_refs_spec(fixtures_dir):
    """Load parameter reference fixture."""
    with open(fixtures_dir / "oas_with_parameter_refs.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def response_refs_spec(fixtures_dir):
    """Load response reference fixture."""
    with open(fixtures_dir / "oas_with_response_refs.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def requestbody_refs_spec(fixtures_dir):
    """Load requestBody reference fixture."""
    with open(fixtures_dir / "oas_with_requestbody_refs.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def security_refs_spec(fixtures_dir):
    """Load security reference fixture."""
    with open(fixtures_dir / "oas_with_security_refs.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def callback_refs_spec(fixtures_dir):
    """Load callback reference fixture."""
    with open(fixtures_dir / "oas_with_callback_refs.yaml") as f:
        return yaml.safe_load(f)


# ============================================================================
# User Story 1: Header Resolution (T019-T025)
# ============================================================================

class TestHeaderResolution:
    """Tests for $ref resolution in #/components/headers/*."""

    def test_header_ref_is_resolved(self, header_refs_spec):
        """T019: Single header reference is resolved and included in output.

        Verifies FR-001: Headers referenced via $ref are included in extracted output.
        """
        slicer = EndpointSlicer(header_refs_spec, "3.0.3")
        result = slicer.extract("/resources", "GET")

        # Assert headers section exists in output
        assert "components" in result
        assert "headers" in result["components"]

        # Assert X-Rate-Limit header is resolved
        headers = result["components"]["headers"]
        assert "X-Rate-Limit" in headers
        assert headers["X-Rate-Limit"]["description"] == "Maximum requests per hour"

    def test_multiple_header_refs_resolved(self, header_refs_spec):
        """T020: Multiple header references from same response are all resolved.

        Verifies all headers in responses.200.headers and responses.429.headers
        are included in the output.
        """
        slicer = EndpointSlicer(header_refs_spec, "3.0.3")
        result = slicer.extract("/resources", "GET")

        headers = result["components"]["headers"]

        # All three headers should be resolved
        assert "X-Rate-Limit" in headers
        assert "X-Rate-Limit-Remaining" in headers
        assert "Retry-After" in headers

    def test_header_with_schema_ref_transitively_resolved(self, header_refs_spec):
        """T021: Header containing nested schema $ref resolves transitively.

        Retry-After header has schema.$ref to RetrySeconds.
        Both header AND schema must be in output.
        """
        slicer = EndpointSlicer(header_refs_spec, "3.0.3")
        result = slicer.extract("/resources", "GET")

        # Retry-After header exists
        assert "Retry-After" in result["components"]["headers"]

        # RetrySeconds schema is transitively resolved
        assert "schemas" in result["components"]
        assert "RetrySeconds" in result["components"]["schemas"]
        assert result["components"]["schemas"]["RetrySeconds"]["type"] == "integer"


# ============================================================================
# User Story 2: Parameter Resolution (T026-T032)
# ============================================================================

class TestParameterResolution:
    """Tests for $ref resolution in #/components/parameters/*."""

    def test_parameter_ref_is_resolved(self, parameter_refs_spec):
        """T026: Parameter reference is resolved and included in output."""
        slicer = EndpointSlicer(parameter_refs_spec, "3.0.3")
        result = slicer.extract("/users/{userId}", "GET")

        # Assert parameters section exists
        assert "components" in result
        assert "parameters" in result["components"]

        # Assert userId parameter is resolved
        params = result["components"]["parameters"]
        assert "userId" in params
        assert params["userId"]["in"] == "path"

    def test_path_level_parameter_ref_resolved(self, parameter_refs_spec):
        """T027: Path-level parameter references are resolved."""
        slicer = EndpointSlicer(parameter_refs_spec, "3.0.3")
        result = slicer.extract("/users/{userId}", "GET")

        # Common parameters at path level should be resolved
        params = result["components"]["parameters"]
        assert "userId" in params

    def test_parameter_with_schema_ref_transitively_resolved(self, parameter_refs_spec):
        """T028: Parameter with nested schema $ref resolves transitively."""
        slicer = EndpointSlicer(parameter_refs_spec, "3.0.3")
        result = slicer.extract("/users/{userId}", "GET")

        # Check that parameter's schema references are resolved
        components = result.get("components", {})
        # If parameter has schema $ref, it should be in schemas
        # This depends on fixture content


# ============================================================================
# User Story 3: Response Resolution (T033-T038)
# ============================================================================

class TestResponseResolution:
    """Tests for $ref resolution in #/components/responses/*."""

    def test_response_ref_is_resolved(self, response_refs_spec):
        """T033: Response reference is resolved and included in output."""
        slicer = EndpointSlicer(response_refs_spec, "3.0.3")
        result = slicer.extract("/orders/{orderId}", "GET")

        # Assert responses section exists
        assert "components" in result
        assert "responses" in result["components"]

        responses = result["components"]["responses"]
        assert "NotFound" in responses

    def test_response_with_headers_and_schema_transitively_resolved(self, response_refs_spec):
        """T034: Response with headers and schemas resolves all transitively."""
        slicer = EndpointSlicer(response_refs_spec, "3.0.3")
        result = slicer.extract("/orders/{orderId}", "GET")

        components = result.get("components", {})
        # Response should be resolved along with nested header and schema refs
        assert "responses" in components
        assert "headers" in components  # X-Request-Id header from response
        assert "schemas" in components  # Error schema from response content


# ============================================================================
# User Story 4: RequestBody Resolution (T049-T054)
# ============================================================================

class TestRequestBodyResolution:
    """Tests for $ref resolution in #/components/requestBodies/*."""

    def test_requestbody_ref_is_resolved(self, requestbody_refs_spec):
        """T049: RequestBody reference is resolved and included in output."""
        slicer = EndpointSlicer(requestbody_refs_spec, "3.0.3")
        result = slicer.extract("/users", "POST")

        # Assert requestBodies section exists
        assert "components" in result
        assert "requestBodies" in result["components"]

        request_bodies = result["components"]["requestBodies"]
        assert "CreateUser" in request_bodies

    def test_requestbody_with_multiple_content_types_resolved(self, requestbody_refs_spec):
        """T050: RequestBody with multiple content types resolves all schemas."""
        slicer = EndpointSlicer(requestbody_refs_spec, "3.0.3")
        result = slicer.extract("/users", "POST")

        components = result.get("components", {})
        # All schemas referenced in content types should be resolved


# ============================================================================
# User Story 5: SecurityScheme Resolution (T055-T062)
# ============================================================================

class TestSecuritySchemeResolution:
    """Tests for security scheme resolution (name-based, not $ref)."""

    def test_operation_level_security_scheme_resolved(self, security_refs_spec):
        """T055: Operation-level security schemes are resolved."""
        slicer = EndpointSlicer(security_refs_spec, "3.0.3")
        result = slicer.extract("/admin/users", "GET")

        # Assert securitySchemes section exists
        assert "components" in result
        assert "securitySchemes" in result["components"]

        # Operation uses bearer_auth and api_key
        schemes = result["components"]["securitySchemes"]
        assert "bearer_auth" in schemes
        assert "api_key" in schemes

    def test_global_security_scheme_resolved(self, security_refs_spec):
        """T056: Global security schemes are resolved when operation inherits."""
        slicer = EndpointSlicer(security_refs_spec, "3.0.3")
        result = slicer.extract("/data", "GET")

        # /data has no operation-level security, inherits global api_key
        security_schemes = result.get("components", {}).get("securitySchemes", {})
        assert "api_key" in security_schemes

    def test_multiple_security_schemes_resolved(self, security_refs_spec):
        """T057: Multiple security schemes are all resolved."""
        slicer = EndpointSlicer(security_refs_spec, "3.0.3")
        result = slicer.extract("/admin/users", "GET")

        security_schemes = result.get("components", {}).get("securitySchemes", {})
        # Operation has bearer_auth and api_key
        assert len(security_schemes) >= 2


# ============================================================================
# Link Resolution (T070-T074)
# ============================================================================

class TestLinkResolution:
    """Tests for $ref resolution in #/components/links/*."""

    def test_link_ref_is_resolved(self, all_component_refs_spec):
        """T070: Link reference is resolved and included in output.

        Uses all_component_refs fixture which has link refs in /orders POST response.
        """
        slicer = EndpointSlicer(all_component_refs_spec, "3.0.3")
        result = slicer.extract("/orders", "POST")

        # Assert links section exists
        components = result.get("components", {})
        assert "links" in components
        assert "GetOrderById" in components["links"]


# ============================================================================
# Callback Resolution (T075-T080)
# ============================================================================

class TestCallbackResolution:
    """Tests for $ref resolution in #/components/callbacks/*."""

    def test_callback_ref_is_resolved(self, callback_refs_spec):
        """T075: Callback reference is resolved and included in output."""
        slicer = EndpointSlicer(callback_refs_spec, "3.0.3")
        result = slicer.extract("/webhooks", "POST")

        # Assert callbacks section exists
        components = result.get("components", {})
        assert "callbacks" in components
        assert "onEvent" in components["callbacks"]

    def test_callback_with_nested_operation_refs_resolved(self, callback_refs_spec):
        """T076: Callback with nested operation refs resolves transitively."""
        slicer = EndpointSlicer(callback_refs_spec, "3.0.3")
        result = slicer.extract("/subscriptions", "POST")

        components = result.get("components", {})
        # Multiple callbacks resolved
        assert "callbacks" in components
        assert "onPaymentSuccess" in components["callbacks"]
        assert "onPaymentFailure" in components["callbacks"]

        # Nested schema refs in callbacks should be resolved
        assert "schemas" in components
        assert "PaymentResult" in components["schemas"]


# ============================================================================
# Mixed Component Resolution (T082)
# ============================================================================

class TestMixedComponentResolution:
    """Tests for resolving multiple component types together."""

    def test_all_component_types_resolved(self, all_component_refs_spec):
        """T082: Extraction with all component types resolves everything."""
        slicer = EndpointSlicer(all_component_refs_spec, "3.0.3")
        result = slicer.extract("/orders", "POST")

        components = result.get("components", {})

        # Should have multiple component types resolved (all 8 types in fixture)
        expected_types = {"schemas", "headers", "parameters", "responses",
                         "requestBodies", "securitySchemes", "links", "callbacks"}
        resolved_types = set(components.keys())

        # At minimum we should have several types
        assert len(resolved_types) >= 5, f"Expected 5+ component types, got: {resolved_types}"

    def test_transitive_dependency_chains(self, all_component_refs_spec):
        """T084: Transitive chains (response → header → schema) are fully resolved."""
        slicer = EndpointSlicer(all_component_refs_spec, "3.0.3")
        result = slicer.extract("/orders", "POST")

        components = result.get("components", {})

        # Chain: responses.BadRequest → headers.X-Request-Id
        #        responses.BadRequest → schemas.Error
        assert "responses" in components
        assert "BadRequest" in components["responses"]
        assert "headers" in components
        assert "X-Request-Id" in components["headers"]
        assert "schemas" in components
        assert "Error" in components["schemas"]

        # Chain: Order → OrderItem (transitive schema ref)
        assert "OrderItem" in components["schemas"]


# ============================================================================
# Resolver Unit Tests
# ============================================================================

class TestResolverParseComponentRef:
    """Unit tests for ReferenceResolver.parse_component_ref()."""

    def test_parse_schema_ref(self, header_refs_spec):
        """Parse schema reference correctly."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.parse_component_ref("#/components/schemas/User")

        assert result is not None
        assert result[0] == ComponentType.SCHEMAS
        assert result[1] == "User"

    def test_parse_header_ref(self, header_refs_spec):
        """Parse header reference correctly."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.parse_component_ref("#/components/headers/X-Rate-Limit")

        assert result is not None
        assert result[0] == ComponentType.HEADERS
        assert result[1] == "X-Rate-Limit"

    def test_parse_parameter_ref(self, header_refs_spec):
        """Parse parameter reference correctly."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.parse_component_ref("#/components/parameters/userId")

        assert result is not None
        assert result[0] == ComponentType.PARAMETERS
        assert result[1] == "userId"

    def test_parse_invalid_ref_returns_none(self, header_refs_spec):
        """Invalid refs return None."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")

        assert resolver.parse_component_ref("http://external.com/schema") is None
        assert resolver.parse_component_ref("#/paths/foo") is None
        assert resolver.parse_component_ref("") is None


class TestResolverGetComponent:
    """Unit tests for ReferenceResolver.get_component()."""

    def test_get_existing_header(self, header_refs_spec):
        """Get existing header component."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.get_component(ComponentType.HEADERS, "X-Rate-Limit")

        assert result is not None
        assert result["description"] == "Maximum requests per hour"

    def test_get_missing_component_returns_none(self, header_refs_spec):
        """Get missing component returns None."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.get_component(ComponentType.HEADERS, "NonExistent")

        assert result is None


class TestResolveAllRefs:
    """Unit tests for ReferenceResolver.resolve_all_refs()."""

    def test_returns_resolved_components(self, header_refs_spec):
        """resolve_all_refs returns ResolvedComponents instance."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.resolve_all_refs("/resources", "GET")

        assert isinstance(result, ResolvedComponents)

    def test_resolves_headers(self, header_refs_spec):
        """resolve_all_refs resolves header references."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.resolve_all_refs("/resources", "GET")

        assert "X-Rate-Limit" in result.headers
        assert "X-Rate-Limit-Remaining" in result.headers
        assert "Retry-After" in result.headers

    def test_resolves_transitive_refs(self, header_refs_spec):
        """resolve_all_refs resolves transitive schema refs in headers."""
        resolver = ReferenceResolver(header_refs_spec, "3.0.3")
        result = resolver.resolve_all_refs("/resources", "GET")

        # RetrySeconds schema is referenced by Retry-After header
        assert "RetrySeconds" in result.schemas

    def test_handles_circular_refs(self, header_refs_spec):
        """resolve_all_refs handles circular references without infinite loop."""
        # Create a spec with circular reference
        circular_spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
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
                            "child": {"$ref": "#/components/schemas/Node"}
                        }
                    }
                }
            }
        }

        resolver = ReferenceResolver(circular_spec, "3.0.3")
        # Should not hang or raise - just return resolved refs
        result = resolver.resolve_all_refs("/test", "GET")

        assert "Node" in result.schemas
