from typing import Any, Optional
from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "success") -> JSONResponse:
    return JSONResponse(content={"code": 0, "message": message, "data": data})


def error(code: int = 1, message: str = "error", data: Any = None, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        content={"code": code, "message": message, "data": data},
        status_code=status_code,
    )


def paginated(items: list, total: int, page: int = 1, page_size: int = 20) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }