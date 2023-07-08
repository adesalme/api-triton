from typing import Optional, Any

import pydantic
from pydantic import ValidationError, validator
from pydantic import BaseModel, ValidationError, Field
from starlette.responses import JSONResponse
from data_models import internal_models
import service_registry


class APISubmission(pydantic.BaseModel):
    text: str
    services: list[str] = Field(example=["Service1:v1.0.0-beta+build"])

    @validator('services')
    def validate_services(cls, v, values, **kwargs):
        try:
            output = []
            for el in v:
                output.append(service_registry.from_fully_qualified(el))
            return output
        except NotImplementedError:
            raise ValidationError(f"Service {el} does not exist.")


class APIResponse(pydantic.BaseModel):
    service_results: Optional[dict[str, Any]] = Field(example={
        'Service1:v1.0.0': [{'test': [1, 2, 3]}]
    })


class APIResponseWebsocket(APIResponse):
    # Normally, the HTTP status code signals success or failure. For websockets, we have to transport them in the response.
    success: bool = True
    detail: Optional[str] = None
    code: Optional[int] = None

    @staticmethod
    def from_err(err):
        return APIResponseWebsocket(success=False, service_results=None, detail=err.detail, code=err.status_code)
