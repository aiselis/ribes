#
#    Copyright 2022 Alessio Pinna <alessio.pinna@aiselis.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import datetime
import inspect
import json
import logging
from typing import Optional

import dateutil.parser
from pydantic import ValidationError
from pydantic.main import BaseModel

from ribes.errors import ParseError, BaseJsonRpcError, InvalidParamsError, InternalError
from ribes.models import JsonRpcRequest, JsonRpcResponse, JsonRpcError, ErrorStatus


class Dispatcher:
    logger = logging.getLogger(__name__)
    method_registry = {}

    @staticmethod
    def dict_to_parameters(signature: inspect.Signature, *args, **kwargs) -> dict:
        result = {}
        try:
            for index, (param_name, param_info) in enumerate(signature.parameters.items()):
                value = args[index] if index < len(args) else kwargs[param_name]
                if issubclass(param_info.annotation, BaseModel):
                    result[param_name] = param_info.annotation(**value)
                elif param_info.annotation is datetime.datetime:
                    result[param_name] = dateutil.parser.isoparser().isoparse(value)
                elif param_info.annotation is inspect.Signature.empty:
                    result[param_name] = value
                else:
                    result[param_name] = param_info.annotation(value)
            return result
        except KeyError:
            raise InvalidParamsError()

    def to_jsonrpc_error(self, error) -> str:
        id = getattr(error, 'id', None)
        code = getattr(error, 'code', InternalError.code)
        message = getattr(error, 'message', InternalError.message)
        self.logger.error(f'Generated error {code} : {message}')
        if not isinstance(error, BaseJsonRpcError):
            self.logger.error(f'Exception: {error}')
        return JsonRpcError(error=ErrorStatus(code=code, message=message), id=id).json(exclude_none=True)

    def register(self, name: str, func):
        self.method_registry[name] = (func, inspect.signature(func), inspect.iscoroutinefunction(func))

    async def dispatch(self, request: str) -> Optional[str]:
        try:
            jsonrpc_request = JsonRpcRequest(**json.loads(request))
            self.logger.info(f'Request to method {jsonrpc_request.method}')
            method, method_signature, method_coro = self.method_registry[jsonrpc_request.method]
            if isinstance(jsonrpc_request.params, list):
                params = Dispatcher.dict_to_parameters(method_signature, *jsonrpc_request.params)
            else:
                params = self.dict_to_parameters(method_signature, **jsonrpc_request.params)
            response = (await method(**params)) if method_coro else method(**params)
            if jsonrpc_request.id:
                return JsonRpcResponse(result=response, id=jsonrpc_request.id).json(exclude_none=True)
        except ValidationError:
            return self.to_jsonrpc_error(ParseError())
        except Exception as error:
            return self.to_jsonrpc_error(error)
