import enum

import pydantic
from pydantic import ConfigDict
from dataclasses import dataclass
from typing import Any
import numpy as np


class PreprocessOutput(pydantic.BaseModel):
    class Config:
        # Necessary for numpy array annotations
        arbitrary_types_allowed = True

    inputs: dict[str, np.ndarray]
    outputs: list[str]
    model_name: str = None


class RequestEndpointType(enum.Enum):
    HTTP = "HTTP"
    WEBSOCKET = "WEBSOCKET"


class ServiceOutputBase(pydantic.BaseModel):
    api_result: Any


class Service1V1Output(ServiceOutputBase):
    api_result: list[dict]
