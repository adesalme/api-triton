from typing import Optional, Any

import pydantic
from pydantic import Field, field_validator

import service_registry
from data_models import internal_models
from services.service_util import ServiceBase


class APIParameterizedServiceRequest(pydantic.BaseModel):
    service: str
    parameters: dict = {}


class APISubmission(pydantic.BaseModel):
    text: str
    service_requests: pydantic.conlist(str | APIParameterizedServiceRequest, min_length=1) = Field(example=["Service1:v1.0.0-beta+build"])
    _service_to_request_mapping: dict[ServiceBase, APIParameterizedServiceRequest] = {}

    @field_validator('service_requests')
    def validate_services(cls, v, values, **kwargs):
        values.data['_service_to_request_mapping'] = {}
        try:
            output = []
            for el in v:
                if not isinstance(el, APIParameterizedServiceRequest):
                    el = APIParameterizedServiceRequest(service=el)
                service_class = service_registry.from_fully_qualified(el.service)
                values.data['_service_to_request_mapping'][service_class] = el
                output.append(el)
            return output
        except NotImplementedError:
            raise ValueError(f"Service {el.service} does not exist.")

    def services_as_class(self):
        return list(self._service_to_request_mapping.keys())

    def parameters_for_service(self, service_class: ServiceBase):
        return self._service_to_request_mapping[service_class].parameters

    def to_service_input(self, service: ServiceBase):
        return internal_models.ServiceInput(
            text=self.text,
            parameters=self.parameters_for_service(service)
        )


class APIResponse(pydantic.BaseModel):
    service_results: Optional[dict[str, Any]] = Field(example={
        'Service1:v1.0.0': [{'test': [1, 2, 3]}]
    })


class APIResponseWebsocket(APIResponse):
    # Normally, the HTTP status code signals success or failure. For websockets, we have to transport some info in the response.
    success: bool = True
    detail: Optional[str] = None
    code: Optional[int] = None

    @staticmethod
    def from_err(err):
        return APIResponseWebsocket(success=False, service_results=None, detail=err.detail, code=err.status_code)
