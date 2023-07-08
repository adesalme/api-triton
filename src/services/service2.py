import numpy as np

import services.service1
from data_models.internal_models import PreprocessOutput, Service1V1Output
from service_registry import MetaRegistry
from services.service_util import ServiceBase
import semver


class Service2V1(ServiceBase, metaclass=MetaRegistry):
    @classmethod
    def name(cls):
        return "Service2"

    @classmethod
    def version(cls):
        return semver.version.Version(major=1)

    @classmethod
    def triton_model_name(cls):
        return "simple_int8"

    @classmethod
    def preprocess(cls, payload, deps: dict):
        return [PreprocessOutput(inputs={'INPUT0': np.array(range(16), dtype=np.int8),
                                         'INPUT1': np.array(range(16), dtype=np.int8)},
                                 outputs=['OUTPUT0', 'OUTPUT1'])]

    @classmethod
    def postprocess(cls, payload, deps: dict, preprocess_results: list[PreprocessOutput], inference_result: list[dict]) -> Service1V1Output:
        output = []
        for el in inference_result:
            tmp_d = {}
            for k, v in el.items():
                tmp_d[k] = v.tolist()
            output.append(
                tmp_d
            )
        return Service1V1Output(api_result=output)

    @classmethod
    def dependencies(cls):
        return [services.service1.Service1V1]
