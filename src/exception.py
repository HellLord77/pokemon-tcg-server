import fastapi

import description


class ExceptionEX(Exception):
    def __init__(self, message: str, code: int):
        self.message = message
        self.code = code


BadRequestException = ExceptionEX(
    description.BAD_REQUEST, fastapi.status.HTTP_400_BAD_REQUEST
)
NotFoundException = ExceptionEX(
    description.NOT_FOUND, fastapi.status.HTTP_404_NOT_FOUND
)
ServerErrorException = ExceptionEX(
    description.SERVER_ERROR, fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR
)
