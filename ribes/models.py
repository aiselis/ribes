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

from typing import Union, Optional, List, Any, Dict

from pydantic import BaseModel, StrictInt, validator


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Union[List[Any], Dict[str, Any]]] = []
    id: Optional[StrictInt]

    class Config:
        validate_assignment = True

    @validator('params')
    def set_params(cls, params):
        return params or []


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Any
    id: StrictInt


class ErrorStatus(BaseModel):
    code: int
    message: str


class JsonRpcError(BaseModel):
    jsonrpc: str = "2.0"
    error: ErrorStatus
    id: Optional[StrictInt]
