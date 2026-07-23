"""
Request validation utilities for API endpoints.

Provides reusable validation functions for UUIDs, pagination, ordering, search, and query parameters.
"""

import uuid
from rest_framework.exceptions import ValidationError


def validate_uuid(value, field_name="id"):
    """
    Validate that a value is a valid UUID.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If the value is not a valid UUID
    """
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError):
        raise ValidationError({field_name: f"Invalid UUID format for {field_name}."})


def validate_pagination(page, page_size, max_page_size=100):
    """
    Validate pagination parameters.

    Args:
        page: Page number
        page_size: Page size
        max_page_size: Maximum allowed page size

    Raises:
        ValidationError: If pagination parameters are invalid
    """
    if page is not None:
        try:
            page = int(page)
            if page < 1:
                raise ValidationError(
                    {"page": "Page number must be a positive integer."}
                )
        except (ValueError, TypeError):
            raise ValidationError({"page": "Page number must be a valid integer."})

    if page_size is not None:
        try:
            page_size = int(page_size)
            if page_size < 1:
                raise ValidationError(
                    {"page_size": "Page size must be a positive integer."}
                )
            if page_size > max_page_size:
                raise ValidationError(
                    {"page_size": f"Page size cannot exceed {max_page_size}."}
                )
        except (ValueError, TypeError):
            raise ValidationError({"page_size": "Page size must be a valid integer."})


def validate_ordering(ordering, valid_fields):
    """
    Validate ordering parameter against allowed fields.

    Args:
        ordering: Ordering string (e.g., "created_at" or "-created_at")
        valid_fields: Set/list of valid field names

    Raises:
        ValidationError: If ordering field is invalid
    """
    if ordering:
        # Remove leading minus for validation
        field = ordering.lstrip("-")
        if field not in valid_fields:
            raise ValidationError(
                {
                    "ordering": f"Invalid ordering field. Valid values: {', '.join(sorted(valid_fields))}."
                }
            )


def validate_search_length(search, max_length=200):
    """
    Validate search parameter length.

    Args:
        search: Search string
        max_length: Maximum allowed length

    Raises:
        ValidationError: If search string is too long
    """
    if search and len(search) > max_length:
        raise ValidationError(
            {"search": f"Search query cannot exceed {max_length} characters."}
        )


def validate_boolean(value, field_name):
    """
    Validate that a value is a valid boolean string.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If the value is not a valid boolean
    """
    if value is not None:
        if isinstance(value, str):
            if value.lower() not in ["true", "false"]:
                raise ValidationError(
                    {
                        field_name: f"Invalid {field_name} value. Must be 'true' or 'false'."
                    }
                )
        elif not isinstance(value, bool):
            raise ValidationError(
                {field_name: f"Invalid {field_name} value. Must be a boolean."}
            )


def validate_choice(value, valid_choices, field_name):
    """
    Validate that a value is in the allowed choices.

    Args:
        value: The value to validate
        valid_choices: List/tuple of valid choices
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If the value is not in valid choices
    """
    if value is not None and value not in valid_choices:
        raise ValidationError(
            {
                field_name: f"Invalid {field_name}. Valid values: {', '.join(valid_choices)}."
            }
        )
