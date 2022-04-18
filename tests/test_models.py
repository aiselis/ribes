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

import pytest

from pydantic import BaseModel, ValidationError

from ribes.models import JsonRpcRequest
from utils import does_not_raise


class ExampleModel(BaseModel):
    x: int = 1
    y: int = 2
    z: int = 4


@pytest.mark.parametrize(
    "params,id,expectation",
    [
        ([1, "2", {'x': 1, 'y': 2, 'z': 0.9}], 1, does_not_raise()),
        ([1, "2", {'x': 1, 'y': 2, 'z': 0.9}], None, does_not_raise()),
        ({'x': 1, 'y': 2, 'z': 0.9}, None, does_not_raise()),
        ([ExampleModel(), ExampleModel()], 4, does_not_raise()),
        (1, 1, pytest.raises(ValidationError)),
    ])
def test_jsonrpc_request_serialization(params, id, expectation):
    with expectation:
        request = JsonRpcRequest(method='method', params=params, id=id)
        serialized = request.dict(exclude_none=True)
        assert isinstance(serialized, dict)
