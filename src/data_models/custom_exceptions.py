from fastapi import HTTPException


class CustomExceptionBase(HTTPException):
    pass


class TritonUnavailableError(CustomExceptionBase):
    def __init__(self):
        self.status_code = 500
        self.detail = "Internal error: GPU backend is unavailable. Try again later."


class ServiceTimeoutError(CustomExceptionBase):
    def __init__(self, service_name, timeout_duration):
        self.service_name = service_name
        self.timeout_duration = timeout_duration
        self.status_code = 500
        self.detail = f"Timeout encountered after {timeout_duration}s during processing of service {service_name}."


class GenericTimeoutError(CustomExceptionBase):
    def __init__(self, timeout_duration):
        self.timeout_duration = timeout_duration
        self.status_code = 500
        self.detail = f"Timeout after {timeout_duration}s: Processing took too long."


class ServiceDependencyError(CustomExceptionBase):
    def __init__(self):
        self.status_code = 500
        self.detail = "One or more dependencies of the service encountered a prior error."


class ServiceGenericError(CustomExceptionBase):
    def __init__(self):
        self.status_code = 500
        self.detail = "An unexpected problem occurred during the handling of the request."


class WebsocketValidationError(CustomExceptionBase):
    def __init__(self, kind):
        self.status_code = 400
        self.detail = f"An error occurred while parsing the request: {kind}"
