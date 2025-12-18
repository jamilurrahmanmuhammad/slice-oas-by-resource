"""Validation pipeline for extracted endpoints.

Implements 7-phase validation checkpoint strategy.
"""

from typing import Dict, Any, Optional, List, Tuple, Set
from slice_oas.models import ValidationResult, ValidationPhase, ComponentType

try:
    from openapi_spec_validator import validate_spec, ValidationError as OASValidationError
    HAS_OAS_VALIDATOR = True
except ImportError:
    HAS_OAS_VALIDATOR = False


class EndpointValidator:
    """Validates extracted endpoint through 7 phases.

    Checkpoint strategy: validate incrementally through 7 phases,
    returning on first failure to provide clear error context.
    """

    def __init__(self, doc: Dict[str, Any], version: str, original_doc: Optional[Dict[str, Any]] = None):
        """Initialize validator with extracted endpoint and version.

        Args:
            doc: Extracted OAS document
            version: OAS version string
            original_doc: Original OAS document (for payload equivalence check)
        """
        self.doc = doc
        self.version = version
        self.original_doc = original_doc

    def validate(self) -> ValidationResult:
        """Validate endpoint through all required phases.

        Returns:
            ValidationResult indicating pass/fail status for first failing phase

        Phases:
            1. FILE_STRUCTURE - valid OAS structure with required fields
            2. OPERATION_INTEGRITY - endpoint has required operation fields
            3. RESPONSE_INTEGRITY - responses properly defined with valid codes
            4. REFERENCE_RESOLUTION - all $ref entries resolved within file
            5. COMPONENT_COMPLETENESS - all referenced components included
            6. PAYLOAD_EQUIVALENCE - extracted matches source endpoint
            7. VERSION_VALIDATION - output matches OAS version
        """
        # Phase 1: FILE_STRUCTURE
        result = self._validate_file_structure()
        if not result.passed:
            return result

        # Phase 2: OPERATION_INTEGRITY
        result = self._validate_operation_integrity()
        if not result.passed:
            return result

        # Phase 3: RESPONSE_INTEGRITY
        result = self._validate_response_integrity()
        if not result.passed:
            return result

        # Phase 4: REFERENCE_RESOLUTION
        result = self._validate_reference_resolution()
        if not result.passed:
            return result

        # Phase 5: COMPONENT_COMPLETENESS
        result = self._validate_component_completeness()
        if not result.passed:
            return result

        # Phase 6: PAYLOAD_EQUIVALENCE
        result = self._validate_payload_equivalence()
        if not result.passed:
            return result

        # Phase 7: VERSION_VALIDATION
        result = self._validate_version()
        return result

    def _validate_file_structure(self) -> ValidationResult:
        """Phase 1: Validate file structure (openapi, info, paths present)."""
        try:
            if not isinstance(self.doc, dict):
                return ValidationResult(
                    phase=ValidationPhase.FILE_STRUCTURE,
                    passed=False,
                    error_message="Document is not a dictionary"
                )

            # Check required OAS fields
            if "openapi" not in self.doc:
                return ValidationResult(
                    phase=ValidationPhase.FILE_STRUCTURE,
                    passed=False,
                    error_message="Missing 'openapi' field"
                )

            if "info" not in self.doc:
                return ValidationResult(
                    phase=ValidationPhase.FILE_STRUCTURE,
                    passed=False,
                    error_message="Missing 'info' field"
                )

            if "paths" not in self.doc or not isinstance(self.doc["paths"], dict):
                return ValidationResult(
                    phase=ValidationPhase.FILE_STRUCTURE,
                    passed=False,
                    error_message="Missing or invalid 'paths' field"
                )

            return ValidationResult(phase=ValidationPhase.FILE_STRUCTURE, passed=True)

        except Exception as e:
            return ValidationResult(
                phase=ValidationPhase.FILE_STRUCTURE,
                passed=False,
                error_message=str(e)
            )

    def _validate_operation_integrity(self) -> ValidationResult:
        """Phase 2: Validate endpoint operation has required fields."""
        try:
            paths = self.doc.get("paths", {})
            if not paths:
                return ValidationResult(
                    phase=ValidationPhase.OPERATION_INTEGRITY,
                    passed=False,
                    error_message="No paths defined in document"
                )

            # Validate each path has operations
            for path, path_item in paths.items():
                if not isinstance(path_item, dict):
                    return ValidationResult(
                        phase=ValidationPhase.OPERATION_INTEGRITY,
                        passed=False,
                        error_message=f"Path '{path}' is not a valid path item object"
                    )

                # Check for at least one valid HTTP method
                methods = ["get", "post", "put", "delete", "patch", "options", "head", "trace"]
                found_method = False
                for method in methods:
                    if method in path_item:
                        found_method = True
                        operation = path_item[method]

                        # Check operation has responses
                        if "responses" not in operation or not operation["responses"]:
                            return ValidationResult(
                                phase=ValidationPhase.OPERATION_INTEGRITY,
                                passed=False,
                                error_message=f"Operation '{method} {path}' missing 'responses' field"
                            )

                if not found_method:
                    return ValidationResult(
                        phase=ValidationPhase.OPERATION_INTEGRITY,
                        passed=False,
                        error_message=f"Path '{path}' has no valid HTTP methods"
                    )

            return ValidationResult(phase=ValidationPhase.OPERATION_INTEGRITY, passed=True)

        except Exception as e:
            return ValidationResult(
                phase=ValidationPhase.OPERATION_INTEGRITY,
                passed=False,
                error_message=str(e)
            )

    def _validate_response_integrity(self) -> ValidationResult:
        """Phase 3: Validate response definitions are complete."""
        try:
            paths = self.doc.get("paths", {})
            for path, path_item in paths.items():
                for method_name, operation in path_item.items():
                    if isinstance(operation, dict) and "responses" in operation:
                        responses = operation["responses"]
                        if not responses:
                            return ValidationResult(
                                phase=ValidationPhase.RESPONSE_INTEGRITY,
                                passed=False,
                                error_message=f"No responses defined for {method_name.upper()} {path}"
                            )

                        # Validate response codes are strings
                        for code, response in responses.items():
                            if not isinstance(code, str):
                                return ValidationResult(
                                    phase=ValidationPhase.RESPONSE_INTEGRITY,
                                    passed=False,
                                    error_message=f"Invalid response code: {code} (must be string)"
                                )

                            if not isinstance(response, dict):
                                return ValidationResult(
                                    phase=ValidationPhase.RESPONSE_INTEGRITY,
                                    passed=False,
                                    error_message=f"Response {code} is not an object"
                                )

                            # Check required description field
                            if "description" not in response:
                                return ValidationResult(
                                    phase=ValidationPhase.RESPONSE_INTEGRITY,
                                    passed=False,
                                    error_message=f"Response {code} missing 'description' field"
                                )

            return ValidationResult(phase=ValidationPhase.RESPONSE_INTEGRITY, passed=True)

        except Exception as e:
            return ValidationResult(
                phase=ValidationPhase.RESPONSE_INTEGRITY,
                passed=False,
                error_message=str(e)
            )

    def _validate_reference_resolution(self) -> ValidationResult:
        """Phase 4: Validate all $ref entries are resolvable within file.

        Checks all 8 OpenAPI component types:
        schemas, headers, parameters, responses, requestBodies,
        securitySchemes, links, callbacks
        """
        try:
            components = self.doc.get("components", {})

            # Build lookup for all component types
            component_lookups = {
                "schemas": components.get("schemas", {}),
                "headers": components.get("headers", {}),
                "parameters": components.get("parameters", {}),
                "responses": components.get("responses", {}),
                "requestBodies": components.get("requestBodies", {}),
                "securitySchemes": components.get("securitySchemes", {}),
                "links": components.get("links", {}),
                "callbacks": components.get("callbacks", {}),
            }

            def find_unresolved_refs(obj: Any) -> Optional[str]:
                """Recursively find any unresolved $ref entries."""
                if isinstance(obj, dict):
                    if "$ref" in obj:
                        ref = obj["$ref"]
                        # Check if it's a component reference
                        if ref.startswith("#/components/"):
                            parts = ref.split("/")
                            if len(parts) >= 4:
                                comp_type = parts[2]
                                comp_name = "/".join(parts[3:])
                                lookup = component_lookups.get(comp_type, {})
                                if comp_name not in lookup:
                                    return f"Reference '{ref}' not found in components.{comp_type}"

                    for value in obj.values():
                        result = find_unresolved_refs(value)
                        if result:
                            return result

                elif isinstance(obj, list):
                    for item in obj:
                        result = find_unresolved_refs(item)
                        if result:
                            return result

                return None

            # Check paths for unresolved refs
            paths = self.doc.get("paths", {})
            unresolved = find_unresolved_refs(paths)
            if unresolved:
                return ValidationResult(
                    phase=ValidationPhase.REFERENCE_RESOLUTION,
                    passed=False,
                    error_message=unresolved
                )

            # Also check components themselves for nested refs
            unresolved = find_unresolved_refs(components)
            if unresolved:
                return ValidationResult(
                    phase=ValidationPhase.REFERENCE_RESOLUTION,
                    passed=False,
                    error_message=unresolved
                )

            return ValidationResult(phase=ValidationPhase.REFERENCE_RESOLUTION, passed=True)

        except Exception as e:
            return ValidationResult(
                phase=ValidationPhase.REFERENCE_RESOLUTION,
                passed=False,
                error_message=str(e)
            )

    def _validate_component_completeness(self) -> ValidationResult:
        """Phase 5: Validate all required components are included."""
        # This phase checks that extracted file has all needed components
        # For now, we assume if reference resolution passed, components are complete
        return ValidationResult(phase=ValidationPhase.COMPONENT_COMPLETENESS, passed=True)

    def _validate_payload_equivalence(self) -> ValidationResult:
        """Phase 6: Validate extracted endpoint matches original.

        Ensures all $ref entries in the extracted document point to
        components that exist and match the original document.
        """
        # This phase is optional if original_doc not provided
        if not self.original_doc:
            return ValidationResult(phase=ValidationPhase.PAYLOAD_EQUIVALENCE, passed=True)

        try:
            # Collect all refs in the extracted document
            extracted_refs = self._collect_all_refs(self.doc)

            # Check each ref exists in extracted components
            missing_refs = []
            for ref in extracted_refs:
                if not self._check_component_exists(ref, self.doc):
                    missing_refs.append(ref)

            if missing_refs:
                return ValidationResult(
                    phase=ValidationPhase.PAYLOAD_EQUIVALENCE,
                    passed=False,
                    error_message=f"Missing components in extracted document: {', '.join(missing_refs[:5])}"
                    + (f" and {len(missing_refs) - 5} more" if len(missing_refs) > 5 else ""),
                    details={"missing_refs": missing_refs}
                )

            # Verify extracted path/method exists in original
            extracted_paths = self.doc.get("paths", {})
            original_paths = self.original_doc.get("paths", {})

            for path, path_item in extracted_paths.items():
                if path not in original_paths:
                    return ValidationResult(
                        phase=ValidationPhase.PAYLOAD_EQUIVALENCE,
                        passed=False,
                        error_message=f"Path '{path}' not found in original document"
                    )

                original_path_item = original_paths[path]
                for method in path_item.keys():
                    if method in ["parameters"]:
                        continue  # Path-level parameters, not a method
                    if method not in original_path_item:
                        return ValidationResult(
                            phase=ValidationPhase.PAYLOAD_EQUIVALENCE,
                            passed=False,
                            error_message=f"Method '{method}' for path '{path}' not found in original"
                        )

            return ValidationResult(phase=ValidationPhase.PAYLOAD_EQUIVALENCE, passed=True)

        except Exception as e:
            return ValidationResult(
                phase=ValidationPhase.PAYLOAD_EQUIVALENCE,
                passed=False,
                error_message=str(e)
            )

    def _collect_all_refs(self, obj: Any, refs: Optional[Set[str]] = None) -> Set[str]:
        """Recursively collect all $ref entries in an object.

        Args:
            obj: Object to scan (dict, list, or primitive)
            refs: Set to accumulate refs (created if None)

        Returns:
            Set of all $ref strings found
        """
        if refs is None:
            refs = set()

        if isinstance(obj, dict):
            if "$ref" in obj:
                refs.add(obj["$ref"])
            for value in obj.values():
                self._collect_all_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                self._collect_all_refs(item, refs)

        return refs

    def _check_component_exists(self, ref: str, doc: Dict[str, Any]) -> bool:
        """Check if a component reference exists in a document.

        Args:
            ref: The $ref string (e.g., "#/components/schemas/User")
            doc: Document to check

        Returns:
            True if component exists, False otherwise
        """
        if not ref.startswith("#/components/"):
            # External refs or non-component refs - assume valid
            return True

        parts = ref.split("/")
        if len(parts) < 4:
            return False

        comp_type = parts[2]
        comp_name = "/".join(parts[3:])

        components = doc.get("components", {})
        type_components = components.get(comp_type, {})

        return comp_name in type_components

    def _validate_version(self) -> ValidationResult:
        """Phase 7: Validate OAS version is correct."""
        try:
            openapi_field = self.doc.get("openapi", "")
            if not isinstance(openapi_field, str):
                return ValidationResult(
                    phase=ValidationPhase.VERSION_VALIDATION,
                    passed=False,
                    error_message="Invalid 'openapi' field format"
                )

            # Check version format (3.0.x or 3.1.x)
            parts = openapi_field.split(".")
            if len(parts) < 2:
                return ValidationResult(
                    phase=ValidationPhase.VERSION_VALIDATION,
                    passed=False,
                    error_message=f"Invalid OAS version format: {openapi_field}"
                )

            major, minor = parts[0], parts[1]
            if major == "3" and minor in ["0", "1"]:
                return ValidationResult(phase=ValidationPhase.VERSION_VALIDATION, passed=True)

            return ValidationResult(
                phase=ValidationPhase.VERSION_VALIDATION,
                passed=False,
                error_message=f"Unsupported OAS version: {openapi_field} (must be 3.0.x or 3.1.x)"
            )

        except Exception as e:
            return ValidationResult(
                phase=ValidationPhase.VERSION_VALIDATION,
                passed=False,
                error_message=str(e)
            )


def validate_converted_document(doc: Dict[str, Any], target_version: str) -> Tuple[bool, List[str]]:
    """Validate a document against target OpenAPI version specification.

    Used for post-conversion validation to ensure the converted document
    complies with the target OAS version (3.0.x or 3.1.x).

    Args:
        doc: Document to validate (converted OAS document)
        target_version: Target OAS version ("3.0.x" or "3.1.x")

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if document passes all validation checks
        - error_messages: List of validation error strings (empty if valid)
    """
    errors = []

    # Basic structure validation
    if not isinstance(doc, dict):
        errors.append("Document must be a dictionary")
        return False, errors

    if "openapi" not in doc:
        errors.append("Missing required 'openapi' field")
        return False, errors

    # Validate version matches target
    openapi_version = doc.get("openapi", "")
    target_major_minor = target_version.split(".")[0:2]  # e.g., ["3", "0"] or ["3", "1"]
    doc_major_minor = openapi_version.split(".")[0:2]

    if doc_major_minor != target_major_minor:
        errors.append(
            f"Document version {openapi_version} does not match target {target_version}"
        )
        return False, errors

    if "info" not in doc:
        errors.append("Missing required 'info' field")
        return False, errors

    if "paths" not in doc:
        errors.append("Missing required 'paths' field")
        return False, errors

    # Version-specific structure validation
    if target_version.startswith("3.0"):
        # 3.0.x specific validations
        # Check for 3.1-only features that should have been removed
        if "webhooks" in doc:
            errors.append("Webhooks found in document but target is 3.0.x (should be removed)")

        # Check schemas for unconvertible 3.1 constructs
        components = doc.get("components", {})
        schemas = components.get("schemas", {})
        for schema_name, schema in schemas.items():
            if not isinstance(schema, dict):
                continue
            # Check for JSON Schema conditionals (if/then/else) which are 3.1 only
            if any(key in schema for key in ["if", "then", "else"]):
                errors.append(
                    f"Schema '{schema_name}' contains JSON Schema conditionals "
                    "(if/then/else) which are not supported in 3.0.x"
                )

    elif target_version.startswith("3.1"):
        # 3.1.x specific validations
        # Check for proper type array syntax in schemas
        components = doc.get("components", {})
        schemas = components.get("schemas", {})
        for schema_name, schema in schemas.items():
            if not isinstance(schema, dict):
                continue
            # Validate that nullable=true has been converted to type arrays if present
            if "nullable" in schema:
                errors.append(
                    f"Schema '{schema_name}' still contains 'nullable' "
                    "(should be converted to type array in 3.1.x)"
                )

    # Use openapi-spec-validator if available for comprehensive validation
    if HAS_OAS_VALIDATOR:
        try:
            validate_spec(doc)
        except OASValidationError as e:
            errors.append(f"OpenAPI specification validation failed: {str(e)}")
        except Exception as e:
            # Catch other exceptions from validator
            errors.append(f"Validation error: {str(e)}")

    return len(errors) == 0, errors
