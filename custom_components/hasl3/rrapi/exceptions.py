class RRAPI_Error(Exception):
    """Base class for SL exceptions."""

    def __init__(self, code, message, details):
        self._code = code
        self._message = message
        self._details = details

    def __str__(self):
        return f"RRAPI_Error {self._code}: {self._message}"

    @property
    def details(self):
        return self._details

    @property
    def message(self):
        return self._message

    @property
    def code(self):
        return self._code


class RRAPI_API_Error(RRAPI_Error):
    """An API-level exception occurred."""

    def __str__(self):
        return f"RRAPI_API_Error {self._code}: {self._message}"


class RRAPI_HTTP_Error(RRAPI_Error):
    """An HTTP-level exception occurred."""

    def __str__(self):
        return f"RRAPI_HTTP_Error {self._code}: {self._message}"
