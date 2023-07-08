import os
import time

from data_models.internal_models import RequestEndpointType


def TRITON_URL():
    return "localhost:8000"


def HTTP_TIMEOUT():
    return 25


def WEBSOCKET_TIMEOUT():
    return 60


def calc_overall_timeout(req_enum: RequestEndpointType):
    if req_enum == RequestEndpointType.HTTP:
        return HTTP_TIMEOUT()
    elif req_enum == RequestEndpointType.WEBSOCKET:
        return WEBSOCKET_TIMEOUT()
