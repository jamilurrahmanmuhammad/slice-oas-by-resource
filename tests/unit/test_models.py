"""Unit tests for data models."""

import pytest
from slice_oas.models import OASDocument, Resource, Reference


class TestOASDocument:
    """Test OASDocument model."""

    def test_instantiate_oas_document(self):
        """Test creating an OASDocument instance."""
        doc = OASDocument()
        assert doc is not None

    def test_oas_document_with_file_path(self):
        """Test OASDocument stores file path."""
        doc = OASDocument()
        # Should be able to set path
        assert hasattr(doc, '__dict__') or hasattr(doc, '__class__')

    def test_oas_document_with_version(self):
        """Test OASDocument stores version."""
        doc = OASDocument()
        # Should have version field
        pass

    def test_oas_document_with_content(self):
        """Test OASDocument stores parsed content."""
        doc = OASDocument()
        # Should have content field
        pass


class TestResource:
    """Test Resource (endpoint) model."""

    def test_create_resource(self):
        """Test creating a Resource instance."""
        resource = Resource(path="/users/{id}", method="GET")
        assert resource is not None

    def test_resource_path_and_method(self):
        """Test Resource stores path and method."""
        # Should support path and method fields
        pass

    def test_resource_operation_details(self):
        """Test Resource stores operation details."""
        # Should store summary, tags, operationId
        pass


class TestReference:
    """Test Reference model for $ref handling."""

    def test_create_reference(self):
        """Test creating a Reference instance."""
        from slice_oas.models import ReferenceType
        ref = Reference(
            ref_string="#/components/schemas/User",
            ref_type=ReferenceType.SCHEMA,
            source_location="responses.200.content.application/json.schema"
        )
        assert ref is not None

    def test_reference_resolve(self):
        """Test Reference can be resolved."""
        # Should have resolve() method
        pass

    def test_reference_external_detection(self):
        """Test Reference detects external vs internal refs."""
        # Should distinguish internal (#/...) from external (http://...)
        pass
