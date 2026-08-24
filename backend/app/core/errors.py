from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class PayPilotBaseException(Exception):
    """Base exception for PayPilot domain errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class GuardianBlockedError(PayPilotBaseException):
    """Raised when an action is blocked by Guardian policy."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class ApprovalRequiredError(PayPilotBaseException):
    """Raised when an action requires explicit merchant approval before execution."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, details=details)


class DuplicateExecutionError(PayPilotBaseException):
    """Raised when an idempotent execution conflict occurs."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, details=details)


class OpportunityNotFoundError(PayPilotBaseException):
    """Raised when an opportunity cannot be located."""

    def __init__(self, opportunity_id: str):
        super().__init__(f"Opportunity with ID '{opportunity_id}' not found.", status_code=status.HTTP_404_NOT_FOUND)


class ActionNotFoundError(PayPilotBaseException):
    """Raised when an action cannot be located."""

    def __init__(self, action_id: str):
        super().__init__(f"Action with ID '{action_id}' not found.", status_code=status.HTTP_404_NOT_FOUND)


class CustomerNotFoundError(PayPilotBaseException):
    """Raised when a customer cannot be located."""

    def __init__(self, customer_id: str):
        super().__init__(f"Customer with ID '{customer_id}' not found.", status_code=status.HTTP_404_NOT_FOUND)


class PolicyViolationError(PayPilotBaseException):
    """Raised when a general policy check fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


def register_error_handlers(app: FastAPI) -> None:
    """Registers domain exception handlers for the FastAPI app."""

    @app.exception_handler(PayPilotBaseException)
    async def paypilot_exception_handler(request: Request, exc: PayPilotBaseException):
        logger.warning(f"Domain exception on {request.url.path}: {exc.message} ({exc.details})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "error_type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "error_type": "InternalServerError",
                "message": "An unexpected internal server error occurred.",
            },
        )
