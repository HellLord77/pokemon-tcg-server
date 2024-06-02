import fastapi

import description


class ExceptionEX(Exception):
    def __init__(self, message: str, code: int):
        self.message = message
        self.code = code


BadRequestException = ExceptionEX(
    description.ERROR_400, fastapi.status.HTTP_400_BAD_REQUEST
)
NotFoundException = ExceptionEX(
    description.ERROR_404, fastapi.status.HTTP_404_NOT_FOUND
)
ServerErrorException = ExceptionEX(
    description.ERROR_500, fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR
)
