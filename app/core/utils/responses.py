"""
Unified Response Helpers - DRY utility for consistent error and success responses.

Eliminates duplicate alert/response code across routes.
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional, Any


def error_response(
    message: str,
    status: int = 400,
    title: Optional[str] = None,
    dismissible: bool = True
) -> Div:
    """
    Create a consistent error response.
    
    Args:
        message: Error message to display
        status: HTTP status code (for logging/context)
        title: Optional title for the error
        dismissible: Whether the alert can be dismissed
        
    Returns:
        Styled error alert component
        
    Example:
        >>> return error_response("Invalid email address")
    """
    return Alert(
        Div(
            Strong(title or "Error", cls="font-bold") if title else None,
            Span(message, cls="block sm:inline"),
            cls="flex items-center"
        ),
        cls="alert alert-error shadow-lg",
        role="alert"
    )


def success_response(
    message: str,
    title: Optional[str] = None,
    dismissible: bool = True
) -> Div:
    """
    Create a consistent success response.
    
    Args:
        message: Success message to display
        title: Optional title for the success message
        dismissible: Whether the alert can be dismissed
        
    Returns:
        Styled success alert component
        
    Example:
        >>> return success_response("Profile updated successfully")
    """
    return Alert(
        Div(
            Strong(title or "Success", cls="font-bold") if title else None,
            Span(message, cls="block sm:inline"),
            cls="flex items-center"
        ),
        cls="alert alert-success shadow-lg",
        role="alert"
    )


def warning_response(
    message: str,
    title: Optional[str] = None,
    dismissible: bool = True
) -> Div:
    """
    Create a consistent warning response.
    
    Args:
        message: Warning message to display
        title: Optional title for the warning
        dismissible: Whether the alert can be dismissed
        
    Returns:
        Styled warning alert component
    """
    return Alert(
        Div(
            Strong(title or "Warning", cls="font-bold") if title else None,
            Span(message, cls="block sm:inline"),
            cls="flex items-center"
        ),
        cls="alert alert-warning shadow-lg",
        role="alert"
    )


def info_response(
    message: str,
    title: Optional[str] = None,
    dismissible: bool = True
) -> Div:
    """
    Create a consistent info response.
    
    Args:
        message: Info message to display
        title: Optional title for the info message
        dismissible: Whether the alert can be dismissed
        
    Returns:
        Styled info alert component
    """
    return Alert(
        Div(
            Strong(title or "Info", cls="font-bold") if title else None,
            Span(message, cls="block sm:inline"),
            cls="flex items-center"
        ),
        cls="alert alert-info shadow-lg",
        role="alert"
    )


def validation_error_response(errors: dict) -> Div:
    """
    Create a response for validation errors.
    
    Args:
        errors: Dictionary of field names to error messages
        
    Returns:
        Styled validation error component
        
    Example:
        >>> errors = {"email": "Invalid format", "password": "Too short"}
        >>> return validation_error_response(errors)
    """
    return Alert(
        Div(
            Strong("Validation Errors", cls="font-bold block mb-2"),
            Ul(
                *[Li(f"{field}: {error}", cls="ml-4") for field, error in errors.items()],
                cls="list-disc"
            ),
            cls="flex flex-col"
        ),
        cls="alert alert-error shadow-lg",
        role="alert"
    )


def json_response(data: Any, status: int = 200) -> dict:
    """
    Create a consistent JSON API response.
    
    Args:
        data: Data to return
        status: HTTP status code
        
    Returns:
        Standardized JSON response
        
    Example:
        >>> return json_response({"user": user_data})
    """
    return {
        "success": status < 400,
        "status": status,
        "data": data
    }


def json_error_response(message: str, status: int = 400, errors: Optional[dict] = None) -> dict:
    """
    Create a consistent JSON error response.
    
    Args:
        message: Error message
        status: HTTP status code
        errors: Optional detailed errors
        
    Returns:
        Standardized JSON error response
        
    Example:
        >>> return json_error_response("Invalid request", status=400)
    """
    response = {
        "success": False,
        "status": status,
        "error": message
    }
    
    if errors:
        response["errors"] = errors
    
    return response


def loading_response(message: str = "Loading...") -> Div:
    """
    Create a loading indicator response.
    
    Args:
        message: Loading message to display
        
    Returns:
        Loading indicator component
    """
    return Div(
        Div(
            Span(cls="loading loading-spinner loading-lg"),
            Span(message, cls="ml-4"),
            cls="flex items-center justify-center"
        ),
        cls="p-8"
    )


def empty_state_response(
    title: str,
    message: str,
    action_text: Optional[str] = None,
    action_href: Optional[str] = None,
    icon: Optional[str] = None
) -> Div:
    """
    Create an empty state response.
    
    Args:
        title: Empty state title
        message: Empty state message
        action_text: Optional CTA button text
        action_href: Optional CTA button link
        icon: Optional icon name
        
    Returns:
        Empty state component
    """
    return Div(
        Div(
            UkIcon(icon or "inbox", width="64", height="64", cls="text-gray-400 mb-4") if icon else None,
            H3(title, cls="text-xl font-bold mb-2"),
            P(message, cls="text-gray-500 mb-4"),
            A(action_text, href=action_href, cls="btn btn-primary") if action_text and action_href else None,
            cls="flex flex-col items-center justify-center"
        ),
        cls="p-12 text-center"
    )
