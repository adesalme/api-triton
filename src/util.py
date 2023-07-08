from starlette.responses import JSONResponse


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def make_generic_error_response(err):
    return JSONResponse(status_code=err.status_code, content={'detail': err.detail})
