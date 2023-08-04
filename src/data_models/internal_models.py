import enum
from typing import Any

import numpy as np
import pydantic


class PreprocessOutput(pydantic.BaseModel):
    class Config:
        # Necessary for numpy array annotations
        arbitrary_types_allowed = True

    inputs: dict[str, np.ndarray]
    outputs: list[str]
    # Overwrite the model used for inference. If None, take the model defined by the service class.
    triton_model_name: str = None


class RequestEndpointType(enum.Enum):
    HTTP = "HTTP"
    WEBSOCKET = "WEBSOCKET"


class ServiceInput(pydantic.BaseModel):
    text: str
    parameters: dict


class ServiceOutputBase(pydantic.BaseModel):
    api_result: Any


class Service1V1Output(ServiceOutputBase):
    api_result: list[dict]
