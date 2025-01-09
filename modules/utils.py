from fastapi import HTTPException
from typing import Any


def check_for_exception(parameter: str | Any, status_code: int, detail: str | None = None) -> None:
    if isinstance(parameter, str):
        exception = HTTPException(status_code=status_code,
                                  detail=parameter)
        if detail:
            exception.detail = detail
        raise exception


def raise_exception(status_code: int, detail: str) -> None:
    raise HTTPException(status_code=status_code,
                        detail=detail)
