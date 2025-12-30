"""
Validation middleware for agents.

Provides input and output validation for agent requests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from pulser_agents.core.exceptions import AgentError
from pulser_agents.core.response import RunResult
from pulser_agents.middleware.base import Middleware, MiddlewareContext, NextHandler


class ValidationMiddlewareError(AgentError):
    """Validation failed."""

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.errors = errors or []


class InputValidator(ABC):
    """Base class for input validators."""

    @abstractmethod
    def validate(self, input_data: Any, ctx: MiddlewareContext) -> None:
        """
        Validate input data.

        Args:
            input_data: The input to validate
            ctx: Middleware context

        Raises:
            ValidationError: If validation fails
        """
        pass


class OutputValidator(ABC):
    """Base class for output validators."""

    @abstractmethod
    def validate(self, output: RunResult, ctx: MiddlewareContext) -> None:
        """
        Validate output data.

        Args:
            output: The result to validate
            ctx: Middleware context

        Raises:
            ValidationError: If validation fails
        """
        pass


class LengthValidator(InputValidator):
    """Validates input length."""

    def __init__(
        self,
        min_length: int = 1,
        max_length: int = 10000,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, input_data: Any, ctx: MiddlewareContext) -> None:
        text = input_data if isinstance(input_data, str) else str(input_data)
        length = len(text)

        if length < self.min_length:
            raise ValidationMiddlewareError(
                f"Input too short: {length} < {self.min_length}",
                errors=[{"field": "input", "error": "too_short"}],
            )

        if length > self.max_length:
            raise ValidationMiddlewareError(
                f"Input too long: {length} > {self.max_length}",
                errors=[{"field": "input", "error": "too_long"}],
            )


class ContentFilterValidator(InputValidator):
    """Filters prohibited content from input."""

    def __init__(
        self,
        blocked_terms: list[str] | None = None,
        case_sensitive: bool = False,
    ) -> None:
        self.blocked_terms = blocked_terms or []
        self.case_sensitive = case_sensitive

    def validate(self, input_data: Any, ctx: MiddlewareContext) -> None:
        text = input_data if isinstance(input_data, str) else str(input_data)

        if not self.case_sensitive:
            text = text.lower()
            blocked = [t.lower() for t in self.blocked_terms]
        else:
            blocked = self.blocked_terms

        for term in blocked:
            if term in text:
                raise ValidationMiddlewareError(
                    "Input contains prohibited content",
                    errors=[{"field": "input", "error": "prohibited_content"}],
                )


class PydanticValidator(OutputValidator):
    """Validates output against a Pydantic model."""

    def __init__(self, model: type[BaseModel]) -> None:
        self.model = model

    def validate(self, output: RunResult, ctx: MiddlewareContext) -> None:
        import json

        if not output.final_response:
            raise ValidationMiddlewareError(
                "No output to validate",
                errors=[{"field": "output", "error": "missing"}],
            )

        content = output.final_response.content

        try:
            # Try to parse as JSON
            data = json.loads(content)
            self.model.model_validate(data)
        except json.JSONDecodeError:
            raise ValidationMiddlewareError(
                "Output is not valid JSON",
                errors=[{"field": "output", "error": "invalid_json"}],
            )
        except Exception as e:
            raise ValidationMiddlewareError(
                f"Output validation failed: {e}",
                errors=[{"field": "output", "error": "validation_failed"}],
            )


class OutputLengthValidator(OutputValidator):
    """Validates output length."""

    def __init__(
        self,
        min_length: int = 1,
        max_length: int = 50000,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, output: RunResult, ctx: MiddlewareContext) -> None:
        if not output.final_response:
            return

        length = len(output.final_response.content)

        if length < self.min_length:
            raise ValidationMiddlewareError(
                f"Output too short: {length} < {self.min_length}",
                errors=[{"field": "output", "error": "too_short"}],
            )

        if length > self.max_length:
            raise ValidationMiddlewareError(
                f"Output too long: {length} > {self.max_length}",
                errors=[{"field": "output", "error": "too_long"}],
            )


class ValidationMiddleware(Middleware):
    """
    Middleware for input and output validation.

    Applies a chain of validators to requests and responses.

    Example:
        >>> middleware = ValidationMiddleware(
        ...     input_validators=[
        ...         LengthValidator(min_length=1, max_length=5000),
        ...         ContentFilterValidator(blocked_terms=["spam"]),
        ...     ],
        ...     output_validators=[
        ...         OutputLengthValidator(min_length=10),
        ...     ],
        ... )
        >>> chain.add(middleware)
    """

    def __init__(
        self,
        input_validators: list[InputValidator] | None = None,
        output_validators: list[OutputValidator] | None = None,
        raise_on_input_error: bool = True,
        raise_on_output_error: bool = False,
    ) -> None:
        """
        Initialize validation middleware.

        Args:
            input_validators: Validators for input
            output_validators: Validators for output
            raise_on_input_error: Raise on input validation failure
            raise_on_output_error: Raise on output validation failure
        """
        self.input_validators = input_validators or []
        self.output_validators = output_validators or []
        self.raise_on_input_error = raise_on_input_error
        self.raise_on_output_error = raise_on_output_error

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Validate input and output."""
        # Validate input
        input_errors: list[dict[str, Any]] = []
        for validator in self.input_validators:
            try:
                validator.validate(ctx.input_message, ctx)
            except ValidationMiddlewareError as e:
                input_errors.extend(e.errors)
                if self.raise_on_input_error:
                    raise

        ctx.set_metadata("input_validation_errors", input_errors)

        # Call next handler
        result = await next_handler(ctx)

        # Validate output
        output_errors: list[dict[str, Any]] = []
        for validator in self.output_validators:
            try:
                validator.validate(result, ctx)
            except ValidationMiddlewareError as e:
                output_errors.extend(e.errors)
                if self.raise_on_output_error:
                    raise

        ctx.set_metadata("output_validation_errors", output_errors)

        return result


class SchemaValidationMiddleware(Middleware):
    """
    Validates that output conforms to a JSON schema.

    Useful for structured output requirements.

    Example:
        >>> middleware = SchemaValidationMiddleware(
        ...     schema={
        ...         "type": "object",
        ...         "properties": {
        ...             "answer": {"type": "string"},
        ...             "confidence": {"type": "number"},
        ...         },
        ...         "required": ["answer"],
        ...     }
        ... )
    """

    def __init__(
        self,
        schema: dict[str, Any],
        raise_on_error: bool = False,
    ) -> None:
        """
        Initialize schema validation middleware.

        Args:
            schema: JSON schema to validate against
            raise_on_error: Whether to raise on validation failure
        """
        self.schema = schema
        self.raise_on_error = raise_on_error

    def _validate_schema(self, data: Any) -> list[str]:
        """Validate data against JSON schema."""
        try:
            import jsonschema
            jsonschema.validate(data, self.schema)
            return []
        except ImportError:
            # Fallback to basic type checking
            errors = []
            if "type" in self.schema:
                expected = self.schema["type"]
                actual_type = type(data).__name__
                type_map = {
                    "object": "dict",
                    "array": "list",
                    "string": "str",
                    "number": ("int", "float"),
                    "integer": "int",
                    "boolean": "bool",
                }
                expected_types = type_map.get(expected, expected)
                if isinstance(expected_types, tuple):
                    if actual_type not in expected_types:
                        errors.append(f"Expected {expected}, got {actual_type}")
                elif actual_type != expected_types:
                    errors.append(f"Expected {expected}, got {actual_type}")

            if "required" in self.schema and isinstance(data, dict):
                for field in self.schema["required"]:
                    if field not in data:
                        errors.append(f"Missing required field: {field}")

            return errors

        except Exception as e:
            return [str(e)]

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Validate output against schema."""
        import json

        result = await next_handler(ctx)

        if not result.final_response:
            return result

        content = result.final_response.content

        try:
            data = json.loads(content)
            errors = self._validate_schema(data)

            ctx.set_metadata("schema_validation_errors", errors)

            if errors and self.raise_on_error:
                raise ValidationMiddlewareError(
                    f"Schema validation failed: {errors}",
                    errors=[{"field": "output", "error": e} for e in errors],
                )

        except json.JSONDecodeError:
            ctx.set_metadata("schema_validation_errors", ["Invalid JSON"])
            if self.raise_on_error:
                raise ValidationMiddlewareError(
                    "Output is not valid JSON",
                    errors=[{"field": "output", "error": "invalid_json"}],
                )

        return result
