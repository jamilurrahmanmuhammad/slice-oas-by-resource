"""Data models for OAS processing."""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict


class OASVersion(str, Enum):
    """OpenAPI version family."""
    VERSION_3_0 = "3.0.x"
    VERSION_3_1 = "3.1.x"


class ReferenceType(str, Enum):
    """Types of OpenAPI references."""
    SCHEMA = "schema"
    PARAMETER = "parameter"
    HEADER = "header"
    SECURITY = "security"
    RESPONSE = "response"


class ComponentType(str, Enum):
    """All 8 OpenAPI 3.x component types.

    Per OpenAPI 3.x specification, these are the valid component types
    that can be referenced via $ref: "#/components/{type}/{name}".
    """
    SCHEMAS = "schemas"
    HEADERS = "headers"
    PARAMETERS = "parameters"
    RESPONSES = "responses"
    REQUEST_BODIES = "requestBodies"
    SECURITY_SCHEMES = "securitySchemes"
    LINKS = "links"
    CALLBACKS = "callbacks"

    @classmethod
    def from_ref_path(cls, ref_path: str) -> Optional['ComponentType']:
        """Parse component type from a $ref path.

        Args:
            ref_path: Reference path (e.g., "#/components/schemas/User")

        Returns:
            ComponentType if valid, None otherwise
        """
        if not ref_path.startswith("#/components/"):
            return None
        parts = ref_path.split("/")
        if len(parts) < 4:
            return None
        type_str = parts[2]
        try:
            return cls(type_str)
        except ValueError:
            return None

    @property
    def python_attr_name(self) -> str:
        """Get the Python attribute name (snake_case)."""
        mapping = {
            ComponentType.SCHEMAS: "schemas",
            ComponentType.HEADERS: "headers",
            ComponentType.PARAMETERS: "parameters",
            ComponentType.RESPONSES: "responses",
            ComponentType.REQUEST_BODIES: "request_bodies",
            ComponentType.SECURITY_SCHEMES: "security_schemes",
            ComponentType.LINKS: "links",
            ComponentType.CALLBACKS: "callbacks",
        }
        return mapping[self]


class ValidationPhase(int, Enum):
    """7-phase validation checkpoint."""
    FILE_STRUCTURE = 1
    OPERATION_INTEGRITY = 2
    RESPONSE_INTEGRITY = 3
    REFERENCE_RESOLUTION = 4
    COMPONENT_COMPLETENESS = 5
    PAYLOAD_EQUIVALENCE = 6
    VERSION_VALIDATION = 7


class OASDocument(BaseModel):
    """OpenAPI specification document model."""
    model_config = ConfigDict(use_enum_values=False)

    file_path: Optional[str] = None
    version: Optional[OASVersion] = None
    format: str = Field(default="yaml", description="JSON or YAML")
    content: Dict[str, Any] = Field(default_factory=dict)
    endpoints: List['Resource'] = Field(default_factory=list)


class Resource(BaseModel):
    """API endpoint (path + method) model."""
    model_config = ConfigDict(use_enum_values=False)

    path: str
    method: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    security: List[Dict[str, List[str]]] = Field(default_factory=list)
    operation: Dict[str, Any] = Field(default_factory=dict)
    deprecated: bool = False


class Reference(BaseModel):
    """OAS $ref entry model."""
    model_config = ConfigDict(use_enum_values=False)

    ref_string: str  # e.g., "#/components/schemas/User"
    ref_type: ReferenceType
    source_location: str  # e.g., "responses.200.content.application/json.schema"
    target: Optional['ResolvedComponent'] = None

    def is_external(self) -> bool:
        """Check if reference points outside the file."""
        return not self.ref_string.startswith("#/")


class ResolvedComponent(BaseModel):
    """Resolved component after reference resolution."""
    model_config = ConfigDict(use_enum_values=False)

    component_type: str  # schema, parameter, header, security
    component_name: str
    content: Dict[str, Any] = Field(default_factory=dict)
    transitive_refs: List[Reference] = Field(default_factory=list)

    def collect_dependencies(self) -> List['ResolvedComponent']:
        """Recursively collect all referenced components."""
        dependencies = []
        for ref in self.transitive_refs:
            if ref.target:
                dependencies.append(ref.target)
                dependencies.extend(ref.target.collect_dependencies())
        return dependencies


@dataclass
class ComponentReference:
    """Represents a parsed $ref pointer to an OpenAPI component.

    Attributes:
        ref_string: Original $ref value (e.g., "#/components/schemas/User")
        component_type: Type of component (one of 8 valid types)
        component_name: Name of the component
        resolved: Whether successfully resolved
    """
    ref_string: str
    component_type: ComponentType
    component_name: str
    resolved: bool = False

    @classmethod
    def from_ref_string(cls, ref_string: str) -> Optional['ComponentReference']:
        """Parse a $ref string into a ComponentReference.

        Args:
            ref_string: Reference string (e.g., "#/components/headers/X-Rate-Limit")

        Returns:
            ComponentReference if valid internal component ref, None otherwise
        """
        if not ref_string.startswith("#/components/"):
            return None

        parts = ref_string.split("/")
        if len(parts) < 4:
            return None

        type_str = parts[2]
        name = "/".join(parts[3:])  # Handle names with slashes

        component_type = ComponentType.from_ref_path(ref_string)
        if component_type is None:
            return None

        return cls(
            ref_string=ref_string,
            component_type=component_type,
            component_name=name,
            resolved=False
        )


@dataclass
class ResolvedComponents:
    """Collection of all resolved components organized by type.

    Tracks resolved components across all 8 OpenAPI component types,
    enabling the slicer to copy all dependencies to the output.
    """
    schemas: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    responses: Dict[str, Any] = field(default_factory=dict)
    request_bodies: Dict[str, Any] = field(default_factory=dict)
    security_schemes: Dict[str, Any] = field(default_factory=dict)
    links: Dict[str, Any] = field(default_factory=dict)
    callbacks: Dict[str, Any] = field(default_factory=dict)

    def add(self, component_type: ComponentType, name: str, definition: Dict[str, Any]) -> None:
        """Add a resolved component.

        Args:
            component_type: Type of component
            name: Component name
            definition: Component definition (deepcopied)
        """
        attr_name = component_type.python_attr_name
        getattr(self, attr_name)[name] = definition

    def has(self, component_type: ComponentType, name: str) -> bool:
        """Check if component already resolved.

        Args:
            component_type: Type of component
            name: Component name

        Returns:
            True if component exists in resolved set
        """
        attr_name = component_type.python_attr_name
        return name in getattr(self, attr_name)

    def get(self, component_type: ComponentType, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve resolved component.

        Args:
            component_type: Type of component
            name: Component name

        Returns:
            Component definition or None if not found
        """
        attr_name = component_type.python_attr_name
        return getattr(self, attr_name).get(name)

    def to_components_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert to OpenAPI components structure.

        Returns:
            Dict suitable for output["components"], only including non-empty sections
        """
        result = {}
        # Map Python attr names to OAS keys
        mapping = [
            ("schemas", "schemas"),
            ("headers", "headers"),
            ("parameters", "parameters"),
            ("responses", "responses"),
            ("request_bodies", "requestBodies"),
            ("security_schemes", "securitySchemes"),
            ("links", "links"),
            ("callbacks", "callbacks"),
        ]
        for attr_name, oas_key in mapping:
            components = getattr(self, attr_name)
            if components:
                result[oas_key] = components
        return result

    def is_empty(self) -> bool:
        """Check if no components resolved."""
        return not any([
            self.schemas,
            self.headers,
            self.parameters,
            self.responses,
            self.request_bodies,
            self.security_schemes,
            self.links,
            self.callbacks,
        ])

    def total_count(self) -> int:
        """Total number of resolved components across all types."""
        return sum([
            len(self.schemas),
            len(self.headers),
            len(self.parameters),
            len(self.responses),
            len(self.request_bodies),
            len(self.security_schemes),
            len(self.links),
            len(self.callbacks),
        ])


class ValidationResult(BaseModel):
    """Result of a single validation phase."""
    model_config = ConfigDict(use_enum_values=False)

    phase: ValidationPhase
    passed: bool
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    def to_user_message(self) -> str:
        """Convert technical details to plain language for users."""
        if self.passed:
            return f"Phase {self.phase.value} validation passed"

        # User-friendly error messages (Principle I: Black Box)
        # No technical terms like JSON, YAML, schema, etc.
        messages = {
            ValidationPhase.FILE_STRUCTURE: "The file format is invalid. Please check that it's a valid OpenAPI specification file.",
            ValidationPhase.OPERATION_INTEGRITY: "The endpoint definition is incomplete. Please verify the operation is properly defined.",
            ValidationPhase.RESPONSE_INTEGRITY: "The response definition has issues. Please check response codes and content types.",
            ValidationPhase.REFERENCE_RESOLUTION: "Some components referenced in the endpoint cannot be found. Please verify all required definitions exist in the file.",
            ValidationPhase.COMPONENT_COMPLETENESS: "Some required components are missing from the output. This is likely a tool issue—please contact support.",
            ValidationPhase.PAYLOAD_EQUIVALENCE: "The extracted endpoint doesn't match the original. Please try again.",
            ValidationPhase.VERSION_VALIDATION: "The output format doesn't match the requested OpenAPI version. Please try again.",
        }
        return messages.get(self.phase, self.error_message or "Validation failed.")


class CSVIndexEntry(BaseModel):
    """CSV index entry for tracking sliced resources."""
    model_config = ConfigDict(use_enum_values=False)

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None
    tags: str = Field(default="")  # Comma-separated
    filename: str
    file_size_kb: float
    schema_count: int
    parameter_count: int
    response_codes: str = Field(default="")  # Comma-separated
    security_required: bool
    deprecated: bool
    created_at: str  # ISO 8601
    output_oas_version: str  # 3.0.x or 3.1.x

    def to_csv_row(self) -> List[str]:
        """Format as RFC 4180 CSV row.

        Returns raw values - csv.writer handles RFC 4180 escaping automatically.
        """
        return [
            self.path,
            self.method,
            self.summary or "",
            self.description or "",
            self.operation_id or "",
            self.tags,
            self.filename,
            str(self.file_size_kb),
            str(self.schema_count),
            str(self.parameter_count),
            self.response_codes,
            "yes" if self.security_required else "no",
            "yes" if self.deprecated else "no",
            self.created_at,
            self.output_oas_version,
        ]


class TransformationRule(BaseModel):
    """Rule for version conversion between OAS families."""
    model_config = ConfigDict(use_enum_values=False)

    pattern: str  # e.g., "nullable" for matching in schemas
    action: str  # "replace", "remove", "add"
    applies_to: str  # "3.0->3.1" or "3.1->3.0"
    target_syntax: Optional[str] = None  # e.g., "type array" for nullable->type replacement


class VersionConverter(BaseModel):
    """Converter for 3.0 <-> 3.1 transformations."""
    model_config = ConfigDict(use_enum_values=False)

    source_version: OASVersion
    target_version: OASVersion
    transformation_rules: List[TransformationRule] = Field(default_factory=list)

    def can_convert(self, doc: Dict[str, Any]) -> bool:
        """Check if document can be converted to target version."""
        # Check for unconvertible structures
        if self.target_version == OASVersion.VERSION_3_0:
            # Check for JSON Schema conditionals (if/then/else)
            for schema in doc.get('components', {}).get('schemas', {}).values():
                if isinstance(schema, dict):
                    if any(k in schema for k in ['if', 'then', 'else']):
                        return False
        return True

    def convert(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformation rules to convert document."""
        result = doc.copy()
        # Transformation rules applied during implementation
        return result


@dataclass
class BatchExtractionRequest:
    """Request parameters for batch endpoint extraction."""
    input_file: Path
    output_dir: Path
    filter_pattern: Optional[str] = None
    filter_type: str = "glob"
    output_version: str = "auto"
    concurrency: int = 4
    output_format: str = "yaml"
    generate_csv: bool = True
    dry_run: bool = False
    strict_mode: bool = False  # For version conversion: fail on unconvertible constructs
    preserve_examples: bool = True  # For version conversion: keep all examples


@dataclass
class BatchExtractionResult:
    """Result of batch endpoint extraction."""
    total_endpoints: int
    extracted_count: int
    failed_count: int
    validation_pass_rate: float
    elapsed_time: float
    csv_index_path: Optional[Path] = None
    failed_endpoints: List[Tuple[str, str, str]] = field(default_factory=list)
    output_files: List[Path] = field(default_factory=list)


@dataclass
class VersionConversionRequest:
    """Request parameters for version conversion (3.0 ↔ 3.1)."""
    source_version: str  # "3.0.x" or "3.1.x"
    target_version: str  # "3.0.x" or "3.1.x"
    transformation_rules: List[Dict[str, Any]] = field(default_factory=list)
    strict_mode: bool = False  # Fail on unconvertible structures
    preserve_examples: bool = True
    input_document: Optional[Dict[str, Any]] = None


@dataclass
class ConversionResult:
    """Result of version conversion."""
    success: bool
    source_version: str
    target_version: str
    converted_document: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    elapsed_time: float = 0.0


# Update forward references
OASDocument.model_rebuild()
Reference.model_rebuild()
ResolvedComponent.model_rebuild()
VersionConverter.model_rebuild()
