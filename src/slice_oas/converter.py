"""Version converter for OpenAPI 3.0.x ↔ 3.1.x transformations."""

import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from copy import deepcopy

from .models import VersionConversionRequest, ConversionResult
from .validator import validate_converted_document


class VersionConverter:
    """Converter for bidirectional OpenAPI version transformations (3.0 ↔ 3.1)."""

    def __init__(self, request: VersionConversionRequest):
        """Initialize converter with request parameters."""
        self.request = request
        self.rules = request.transformation_rules or self._load_rules()
        self.strict_mode = request.strict_mode
        self.preserve_examples = request.preserve_examples

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load transformation rules from JSON configuration."""
        rules_path = Path(__file__).parent / "transformation_rules.json"
        if not rules_path.exists():
            return []

        try:
            with open(rules_path, 'r') as f:
                config = json.load(f)

            # Select rules based on conversion direction
            if self.request.source_version == "3.0.x" and self.request.target_version == "3.1.x":
                rules = config.get("rules_30_to_31", [])
            elif self.request.source_version == "3.1.x" and self.request.target_version == "3.0.x":
                rules = config.get("rules_31_to_30", [])
            else:
                return []

            # Sort rules by priority for deterministic ordering
            return sorted(rules, key=lambda r: (r.get("priority", 999), r.get("id", "")))
        except Exception as e:
            raise RuntimeError(f"Failed to load transformation rules: {str(e)}")

    def convert(self, document: Dict[str, Any]) -> ConversionResult:
        """Convert OpenAPI document from source version to target version."""
        start_time = time.time()
        warnings = []
        errors = []

        try:
            # Validate source document version
            if not self._validate_source_version(document):
                return ConversionResult(
                    success=False,
                    source_version=self.request.source_version,
                    target_version=self.request.target_version,
                    errors=["Source document version mismatch"],
                    elapsed_time=time.time() - start_time
                )

            # Deep copy document to avoid modifying original
            converted_doc = deepcopy(document)

            # Apply transformation rules
            if self.request.source_version == "3.0.x" and self.request.target_version == "3.1.x":
                converted_doc, rule_warnings, rule_errors = self._convert_30_to_31(converted_doc)
            elif self.request.source_version == "3.1.x" and self.request.target_version == "3.0.x":
                converted_doc, rule_warnings, rule_errors = self._convert_31_to_30(converted_doc)
            else:
                return ConversionResult(
                    success=False,
                    source_version=self.request.source_version,
                    target_version=self.request.target_version,
                    errors=["Unsupported conversion direction"],
                    elapsed_time=time.time() - start_time
                )

            warnings.extend(rule_warnings)
            errors.extend(rule_errors)

            # Fail if strict mode and errors occurred
            if self.strict_mode and errors:
                return ConversionResult(
                    success=False,
                    source_version=self.request.source_version,
                    target_version=self.request.target_version,
                    errors=errors,
                    warnings=warnings,
                    elapsed_time=time.time() - start_time
                )

            # Update version in converted document
            self._update_version(converted_doc, self.request.target_version)

            # Validate converted document
            validation_errors = self._validate_target_version(converted_doc)
            if validation_errors:
                errors.extend(validation_errors)
                if self.strict_mode:
                    return ConversionResult(
                        success=False,
                        source_version=self.request.source_version,
                        target_version=self.request.target_version,
                        errors=errors,
                        warnings=warnings,
                        elapsed_time=time.time() - start_time
                    )

            return ConversionResult(
                success=True,
                source_version=self.request.source_version,
                target_version=self.request.target_version,
                converted_document=converted_doc,
                warnings=warnings,
                errors=errors,
                elapsed_time=time.time() - start_time
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                source_version=self.request.source_version,
                target_version=self.request.target_version,
                errors=[f"Conversion failed: {str(e)}"],
                elapsed_time=time.time() - start_time
            )

    def _convert_30_to_31(self, doc: Dict[str, Any]) -> tuple:
        """Convert OpenAPI 3.0.x document to 3.1.x."""
        warnings = []
        errors = []

        # Apply transformation rules
        self._apply_nullable_to_type_array(doc)
        self._apply_discriminator_property_to_mapping(doc)

        return doc, warnings, errors

    def _convert_31_to_30(self, doc: Dict[str, Any]) -> tuple:
        """Convert OpenAPI 3.1.x document to 3.0.x."""
        warnings = []
        errors = []

        # Apply transformation rules
        self._apply_type_array_to_nullable(doc)
        self._apply_discriminator_mapping_to_property(doc)

        # Remove 3.1-only features
        if "webhooks" in doc:
            del doc["webhooks"]
            warnings.append("Webhooks removed (not supported in 3.0.x)")

        removed = self._remove_mutual_tls(doc)
        if removed:
            warnings.append("mutualTLS security scheme removed (not supported in 3.0.x)")

        moved = self._move_license_identifier(doc)
        if moved:
            warnings.append("license.identifier moved to license.name")

        # Check for unconvertible features
        has_conditionals = self._check_json_schema_conditionals(doc)
        if has_conditionals:
            if self.strict_mode:
                errors.append("JSON Schema conditionals (if/then/else) not supported in 3.0.x")
            else:
                warnings.append("JSON Schema conditionals found; may not convert properly to 3.0.x")

        return doc, warnings, errors

    def _apply_nullable_to_type_array(self, doc: Dict[str, Any]) -> None:
        """Convert nullable: true to type: [type, 'null']."""
        def process_schema(schema: Dict[str, Any]) -> None:
            if not isinstance(schema, dict):
                return

            if schema.get("nullable") is True:
                current_type = schema.get("type", "object")
                if isinstance(current_type, str):
                    schema["type"] = [current_type, "null"]
                elif isinstance(current_type, list) and "null" not in current_type:
                    schema["type"] = current_type + ["null"]
                if "nullable" in schema:
                    del schema["nullable"]

            # Recursively process nested schemas
            for key in ["properties", "items", "allOf", "oneOf", "anyOf"]:
                if key == "properties" and isinstance(schema.get(key), dict):
                    for prop in schema[key].values():
                        process_schema(prop)
                elif key in schema:
                    if isinstance(schema[key], dict):
                        process_schema(schema[key])
                    elif isinstance(schema[key], list):
                        for item in schema[key]:
                            process_schema(item)

        if "components" in doc and "schemas" in doc["components"]:
            for schema in doc["components"]["schemas"].values():
                process_schema(schema)

        if "paths" in doc:
            for path_item in doc.get("paths", {}).values():
                if isinstance(path_item, dict):
                    for operation in path_item.values():
                        if isinstance(operation, dict):
                            for parameter in operation.get("parameters", []):
                                if "schema" in parameter:
                                    process_schema(parameter["schema"])

    def _apply_type_array_to_nullable(self, doc: Dict[str, Any]) -> None:
        """Convert type: [type, 'null'] to nullable: true."""
        def process_schema(schema: Dict[str, Any]) -> None:
            if not isinstance(schema, dict):
                return

            if isinstance(schema.get("type"), list) and "null" in schema["type"]:
                non_null_types = [t for t in schema["type"] if t != "null"]
                if non_null_types:
                    schema["type"] = non_null_types[0]
                schema["nullable"] = True

            for key in ["properties", "items", "allOf", "oneOf", "anyOf"]:
                if key == "properties" and isinstance(schema.get(key), dict):
                    for prop in schema[key].values():
                        process_schema(prop)
                elif key in schema:
                    if isinstance(schema[key], dict):
                        process_schema(schema[key])
                    elif isinstance(schema[key], list):
                        for item in schema[key]:
                            process_schema(item)

        if "components" in doc and "schemas" in doc["components"]:
            for schema in doc["components"]["schemas"].values():
                process_schema(schema)

        if "paths" in doc:
            for path_item in doc.get("paths", {}).values():
                if isinstance(path_item, dict):
                    for operation in path_item.values():
                        if isinstance(operation, dict):
                            for parameter in operation.get("parameters", []):
                                if "schema" in parameter:
                                    process_schema(parameter["schema"])

    def _apply_discriminator_property_to_mapping(self, doc: Dict[str, Any]) -> None:
        """Convert discriminator.propertyName to discriminator.mapping."""
        if "components" not in doc or "schemas" not in doc["components"]:
            return

        for schema in doc["components"]["schemas"].values():
            if isinstance(schema, dict) and "discriminator" in schema:
                discriminator = schema["discriminator"]
                if isinstance(discriminator, dict) and "propertyName" in discriminator:
                    mapping = {}
                    if "oneOf" in schema:
                        for item in schema["oneOf"]:
                            if "$ref" in item:
                                ref_parts = item["$ref"].split("/")
                                schema_name = ref_parts[-1] if ref_parts else ""
                                mapping[schema_name] = item["$ref"]
                    if mapping:
                        discriminator["mapping"] = mapping

    def _apply_discriminator_mapping_to_property(self, doc: Dict[str, Any]) -> None:
        """Convert discriminator.mapping to discriminator.propertyName."""
        if "components" not in doc or "schemas" not in doc["components"]:
            return

        for schema in doc["components"]["schemas"].values():
            if isinstance(schema, dict) and "discriminator" in schema:
                discriminator = schema["discriminator"]
                if isinstance(discriminator, dict) and "mapping" in discriminator:
                    property_name = discriminator.get("propertyName", "type")
                    if "propertyName" not in discriminator:
                        discriminator["propertyName"] = property_name
                    if "mapping" in discriminator:
                        del discriminator["mapping"]

    def _remove_mutual_tls(self, doc: Dict[str, Any]) -> bool:
        """Remove mutualTLS security schemes."""
        removed = False
        if "components" in doc and "securitySchemes" in doc["components"]:
            schemes = doc["components"]["securitySchemes"]
            to_remove = [k for k, v in schemes.items() if isinstance(v, dict) and v.get("type") == "mutualTLS"]
            for scheme_name in to_remove:
                del schemes[scheme_name]
                removed = True
        return removed

    def _move_license_identifier(self, doc: Dict[str, Any]) -> bool:
        """Move license.identifier to license.name."""
        moved = False
        if "info" in doc and isinstance(doc["info"], dict):
            if "license" in doc["info"] and isinstance(doc["info"]["license"], dict):
                license_obj = doc["info"]["license"]
                if "identifier" in license_obj:
                    if "name" not in license_obj:
                        license_obj["name"] = license_obj["identifier"]
                    del license_obj["identifier"]
                    moved = True
        return moved

    def _check_json_schema_conditionals(self, doc: Dict[str, Any]) -> bool:
        """Check for JSON Schema conditionals (if/then/else)."""
        conditional_keywords = {"if", "then", "else"}

        def has_conditionals(schema: Any) -> bool:
            if isinstance(schema, dict):
                if any(k in schema for k in conditional_keywords):
                    return True
                for value in schema.values():
                    if has_conditionals(value):
                        return True
            elif isinstance(schema, list):
                for item in schema:
                    if has_conditionals(item):
                        return True
            return False

        if "components" in doc and "schemas" in doc["components"]:
            for schema in doc["components"]["schemas"].values():
                if has_conditionals(schema):
                    return True
        return False

    def _validate_source_version(self, document: Dict[str, Any]) -> bool:
        """Validate that document version matches source version."""
        openapi_version = document.get("openapi", "")
        if self.request.source_version == "3.0.x":
            return openapi_version.startswith("3.0.")
        elif self.request.source_version == "3.1.x":
            return openapi_version.startswith("3.1.")
        return False

    def _update_version(self, document: Dict[str, Any], target_version: str) -> None:
        """Update openapi version field in document."""
        if target_version == "3.0.x":
            document["openapi"] = "3.0.0"
        elif target_version == "3.1.x":
            document["openapi"] = "3.1.0"

    def _validate_target_version(self, document: Dict[str, Any]) -> List[str]:
        """Validate converted document against target version requirements.

        Uses comprehensive validation from validate_converted_document() to ensure
        the converted document complies with the target OAS version specification.
        """
        # Use comprehensive validation from validator module
        is_valid, validation_errors = validate_converted_document(document, self.request.target_version)
        return validation_errors


def convert_version(doc: dict, target_version: str) -> dict:
    """Convert between OAS versions (backward compatibility)."""
    # Detect source version
    openapi = doc.get("openapi", "3.0.0")
    source_version = "3.0.x" if openapi.startswith("3.0.") else "3.1.x"

    request = VersionConversionRequest(
        source_version=source_version,
        target_version=target_version
    )
    converter = VersionConverter(request)
    result = converter.convert(doc)

    return result.converted_document if result.success else doc
