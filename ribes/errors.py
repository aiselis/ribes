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

class BaseJsonRpcError(Exception):
    """ Base JsonRpc error """

    code: int
    message: str

    def __init__(self, id=None):
        self.id = id
        super(BaseJsonRpcError, self).__init__(self.message)


class ParseError(BaseJsonRpcError):
    code = -32700
    message = 'Parse error'


class InvalidRequestError(BaseJsonRpcError):
    code = -32600
    message = 'Invalid Request'


class MethodNotFoundError(BaseJsonRpcError):
    code = -32601
    message = 'Method not found'


class InvalidParamsError(BaseJsonRpcError):
    code = -32602
    message = 'Invalid params'


class InternalError(BaseJsonRpcError):
    code = -32603
    message = 'Internal error'


class ErrorMap:
    _map = dict([
        (ParseError.code, ParseError),
        (InvalidRequestError.code, InvalidRequestError),
        (MethodNotFoundError.code, MethodNotFoundError),
        (InvalidParamsError.code, InvalidParamsError),
        (InternalError.code, InternalError),
    ])

    @staticmethod
    def get(code: int):
        return ErrorMap._map[code]

