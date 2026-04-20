"""
backend/utils/response.py
Standard API response helpers.
All API responses follow: {"success": bool, "data": any, "message": str}
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
) -> dict:
    """Return a standard success response dict."""
    return {"success": True, "data": data, "message": message}


def error_response(
    message: str = "An error occurred",
    code: int = 400,
    data: Any = None,
) -> JSONResponse:
    """Return a standard error JSONResponse with the appropriate HTTP status."""
    return JSONResponse(
        status_code=code,
        content={"success": False, "data": data, "message": message},
    )


def paginated_response(
    items: list,
    total: int,
    page: int,
    limit: int,
    message: str = "Success",
) -> dict:
    """Wrap paginated results in the standard response format."""
    import math
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": math.ceil(total / limit) if limit > 0 else 0,
        },
        "message": message,
    }
