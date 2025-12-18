"""Custom exceptions for user-friendly error handling.

All exception messages follow Principle I (Black Box): no code, JSON, YAML,
or technical jargon exposed to users. All messages in plain language.
"""


class InvalidOASError(Exception):
    """Raised when OAS file is invalid.

    User-facing message: "The OpenAPI file format is not recognized."
    This maps to file structure validation failure or unsupported format.
    """

    USER_MESSAGE = "The OpenAPI file format is not recognized. Please check that the file is a valid OpenAPI specification."


class MissingReferenceError(Exception):
    """Raised when a referenced component is missing.

    User-facing message: "Some components referenced in the file cannot be found."
    This indicates incomplete schema definitions or broken references.
    """

    USER_MESSAGE = "Some components referenced in the file cannot be found. Please verify all required schemas and parameters are defined."


class ConversionError(Exception):
    """Raised when version conversion fails.

    User-facing message: "The file could not be converted to the requested format."
    This happens when conversion between OpenAPI version families is not possible.
    """

    USER_MESSAGE = "The file could not be converted to the requested format. Some features in this file are not compatible with the target version."


class ValidationError(Exception):
    """Raised when validation fails.

    User-facing message: "The file validation failed."
    This is a catch-all for validation errors across all 7 validation phases.
    """

    USER_MESSAGE = "The file validation failed. Please review the file and try again."
