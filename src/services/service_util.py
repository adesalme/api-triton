import asyncio

from triton_dispatcher import TritonDispatcher
from data_models.internal_models import PreprocessOutput, ServiceOutputBase
import data_models.custom_exceptions as ce
import semver


class ServiceBase:
    INFERENCE_TIMEOUT = 10
    VERSION_SEPARATOR = ':'

    @classmethod
    def deps_satisfied(cls, deps: dict["ServiceBase", any]):
        for d in cls.dependencies():
            if d not in deps:
                return False
        return True

    @classmethod
    def name(cls):
        raise NotImplementedError

    @classmethod
    def version(cls) -> semver.version.Version:
        raise NotImplementedError

    @classmethod
    def version_str(cls):
        return "v" + str(cls.version())

    @classmethod
    def triton_model_name(cls):
        raise NotImplementedError

    @classmethod
    def api_name(cls):
        return cls.name() + cls.VERSION_SEPARATOR + cls.version_str()

    @classmethod
    def preprocess(cls, payload, deps: dict) -> list[PreprocessOutput]:
        raise NotImplementedError

    @classmethod
    def postprocess(cls, payload, deps: dict, preprocess_results: list[PreprocessOutput], inference_result: list[dict]) -> ServiceOutputBase:
        raise NotImplementedError

    @classmethod
    async def inference(cls, payload, deps: dict, timeout_duration=None):
        preprocess_result = cls.preprocess(payload, deps)
        inference_results = []
        triton = TritonDispatcher()
        # This is the per-service timeout, there is also an overall timeout in the dispatcher
        effective_timeout = timeout_duration or cls.INFERENCE_TIMEOUT
        try:
            async with asyncio.timeout(effective_timeout):
                for res in preprocess_result:
                    inference_results.append(await triton.infer(res.model_name or cls.triton_model_name(), inputs=res.inputs, outputs=res.outputs))
                return cls.postprocess(payload, deps, preprocess_result, inference_results)
        except TimeoutError:
            raise ce.ServiceTimeoutError(cls.api_name(), effective_timeout)

    @classmethod
    def dependencies(cls) -> set["ServiceBase"]:
        return set()
