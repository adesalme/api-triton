import asyncio
import enum

import aiohttp.client_exceptions
import numpy as np
import tritonclient.http.aio as thc
import tritonclient.utils as tri_utils

import config
import util
from data_models import custom_exceptions as ce


class TritonModelState(enum.Enum):
    READY = 'READY'
    UNAVAILABLE = 'UNAVAILABLE'


class TritonDispatcher(metaclass=util.Singleton):
    def __init__(self, client=thc.InferenceServerClient, **kwargs):
        _default_args = {'url': config.triton_url(), 'ssl': False, 'conn_limit': 10, 'conn_timeout': 5}
        self.effective_kargs = _default_args | kwargs
        self._client = client
        self._client_instance = None

    def _make_client(self):
        return self._client(**self.effective_kargs)

    @property
    def client(self):
        if self._client_instance is None:
            self._client_instance = self._make_client()
        return self._client_instance

    def set_client(self, client: thc.InferenceServerClient):
        self._client = client

    async def healthcheck(self):
        try:
            return await self.client.is_server_live() and await self.client.is_server_ready()
        except aiohttp.client_exceptions.ClientConnectorError:
            raise ce.TritonUnavailableError()

    async def get_remote_models(self, filter_by_state: list[TritonModelState] = (TritonModelState.READY,)):
        resp = await self.client.get_model_repository_index()
        models = []
        for el in resp:
            if el['state'] in list(map(lambda x: x.value, filter_by_state)):
                models.append(el['name'])
        return models

    def triton_inputs_from_array(self, inputs: dict[str, np.array]) -> list:
        tensors = []
        for name, tensor in inputs.items():
            # Add batch dim
            if tensor.shape[0] != 1 or len(tensor.shape) == 1:
                tensor = tensor.reshape(1, *tensor.shape)
            triton_dtype = tri_utils.np_to_triton_dtype(tensor.dtype)
            input_obj = thc.InferInput(
                name=name,
                datatype=triton_dtype,
                shape=list(tensor.shape)
            )
            if triton_dtype == 'BYTES':
                # TODO Handle Triton interface for strings
                raise NotImplementedError
            input_obj.set_data_from_numpy(tensor)
            tensors.append(input_obj)
        return tensors

    def format_triton_output(self, results, outputs) -> dict:
        output_dict = {}
        for o in outputs:
            output_dict[o] = results.as_numpy(o)
        return output_dict

    async def infer(self, model_name: str, inputs: dict[str, np.ndarray], outputs: list[str], retries=7) -> dict:
        triton_inputs = self.triton_inputs_from_array(inputs)
        try_counter = 0
        while try_counter < retries:
            try:
                results = await self.client.infer(
                    model_name,
                    inputs=triton_inputs,
                )
                return self.format_triton_output(results, outputs)
            except tri_utils.InferenceServerException as e:
                # Unknown model, maybe Triton is reindexing? Wait and try again.
                try_counter += 1
                await asyncio.sleep(1)
            except aiohttp.client_exceptions.ClientConnectionError:
                # Connection reset by peer, keep trying.
                try_counter += 1
                await asyncio.sleep(1)
        raise ce.TritonUnavailableError()
