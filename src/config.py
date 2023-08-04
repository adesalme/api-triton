from data_models.internal_models import RequestEndpointType


def triton_url() -> str:
    return "localhost:8000"


def version_separator() -> str:
    return ':'


def per_service_timeout() -> int:
    return 10


def http_timeout() -> int:
    return 25


def websocket_timeout() -> int:
    return 60


def calc_overall_timeout(req_enum: RequestEndpointType) -> int:
    if req_enum == RequestEndpointType.HTTP:
        return http_timeout()
    elif req_enum == RequestEndpointType.WEBSOCKET:
        return websocket_timeout()
