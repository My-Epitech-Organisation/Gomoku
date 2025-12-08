from enum import Enum
from typing import Any

import constants


class ResponseType(Enum):
    OK = "OK"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"
    MOVE = "MOVE"


class Response:
    def __init__(self, type: ResponseType, data: Any | None = None):
        self.type = type
        self.data = data

    def to_output(self) -> str:
        if self.data is None:
            return self.type.value
        return f"{self.type.value} {self.data}"


class OkResponse(Response):
    def __init__(self):
        super().__init__(ResponseType.OK)


class ErrorResponse(Response):
    def __init__(self, message: str):
        super().__init__(ResponseType.ERROR, message)


class UnknownResponse(Response):
    def __init__(self, message: str | None = None):
        super().__init__(ResponseType.UNKNOWN, message)


class MoveResponse(Response):
    def __init__(self, x: int, y: int):
        super().__init__(ResponseType.MOVE, f"{x},{y}")
        self.x = x
        self.y = y


class AboutResponse(Response):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        author: str | None = None,
        country: str | None = None,
        www: str | None = None,
        email: str | None = None,
    ):
        name = name or constants.BRAIN_NAME
        version = version or constants.BRAIN_VERSION
        author = author or constants.BRAIN_AUTHOR
        country = country or constants.BRAIN_COUNTRY
        info_parts = [f'name="{name}"', f'version="{version}"', f'author="{author}"']
        if country:
            info_parts.append(f'country="{country}"')
        if www:
            info_parts.append(f'www="{www}"')
        if email:
            info_parts.append(f'email="{email}"')
        super().__init__(ResponseType.OK, ", ".join(info_parts))
