from contextlib import asynccontextmanager
from pprint import pprint

import fastapi
from fastapi import FastAPI, WebSocket
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from pydantic import ValidationError

import data_models.api_models as api_models
import data_models.custom_exceptions as ce
import service_dispatcher
import service_registry
import util
from data_models.internal_models import RequestEndpointType
import traceback


@asynccontextmanager
async def lifespan(a: FastAPI):
    service_registry.load_all()
    pprint(service_registry.get_registry())
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.middleware("http")
async def catch_unknown_exception(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except ce.CustomExceptionBase as e:
        return util.make_generic_error_response(e)
    except Exception as e:
        traceback.print_exception(e)
        # Not clean, but cannot raise HTTPException from here
        return util.make_generic_error_response(ce.ServiceGenericError())


@app.get('/v1/models')
async def get_models():
    return list(sorted(map(lambda x: x[1].api_name(), service_registry.get_registry().items())))


@app.post('/v1/inference', status_code=200)
async def inference(payload: api_models.APISubmission) -> api_models.APIResponse:
    services_output = await service_dispatcher.dispatch(payload, received_from=RequestEndpointType.HTTP)
    return api_models.APIResponse(service_results=services_output)


@app.websocket("/v1/inference/ws")
async def inference_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            request = api_models.APISubmission.parse_raw(data)
            services_output = await service_dispatcher.dispatch(request, received_from=RequestEndpointType.WEBSOCKET)
            await websocket.send_text(api_models.APIResponseWebsocket(service_results=services_output).json())
        except WebSocketDisconnect:
            break
        except ce.CustomExceptionBase as e:
            await websocket.send_text(api_models.APIResponseWebsocket.from_err(e).json())
        except ValidationError as e:
            await websocket.send_text(api_models.APIResponseWebsocket.from_err(ce.WebsocketValidationError(e.json())).json())
        except Exception:
            await websocket.send_text(api_models.APIResponseWebsocket.from_err(ce.ServiceGenericError()).json())


@app.get("/")
async def get():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8080/v1/inference/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
""")
