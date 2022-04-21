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

import inspect
import json
from datetime import datetime
from uuid import UUID

import pytest
from pydantic import BaseModel

from ribes.dispatcher import Dispatcher
from ribes.errors import InvalidParamsError, ParseError
from ribes.models import JsonRpcResponse, JsonRpcError
from utils import does_not_raise


class ExampleModel(BaseModel):
    x: int = 10
    y: int = 10
    z: float = 0.5


@pytest.fixture
def function_factory():
    def _factory(func):
        def model(a: int, b: str, c: ExampleModel):
            pass

        def uuid(v: UUID):
            raise Exception("Generic")

        def date(d: datetime) -> int:
            return 6

        def generic(a, b, c):
            return ExampleModel()

        async def async_func(a: int, b: str):
            pass

        def fuzzy(a: int, b: str, c: ExampleModel):
            pass

        def no_parameter():
            pass

        return locals()[func]

    return _factory


@pytest.mark.parametrize(
    "func,args,kwargs,expectation",
    [
        ('model', [1, "2", {'x': 1, 'y': 2, 'z': 0.9}], {}, does_not_raise()),
        ('model', [], {'a': 1, 'b': "2", 'c': {'x': 1, 'y': 2, 'z': 0.9}}, does_not_raise()),
        ('model', [], {}, pytest.raises(InvalidParamsError)),
        ('uuid', ['1f4f3860-c530-4989-b185-fdecd0a00ccd'], {}, does_not_raise()),
        ('date', ["2020-01-10T04:54:54Z"], {}, does_not_raise()),
        ('generic', ['a', 1, .3], {}, does_not_raise())
    ]
)
def test_dict_to_parameters(function_factory, func, args, kwargs, expectation):
    with expectation:
        signature = inspect.signature(function_factory(func))
        result = Dispatcher.dict_to_parameters(signature, *args, **kwargs)
        assert isinstance(result, dict)
        for param_name, param_type in signature.parameters.items():
            assert isinstance(result[param_name],
                              param_type.annotation) or param_type.annotation == inspect.Signature.empty


@pytest.mark.parametrize(
    "error",
    [
        (Exception()),
        (ParseError(4)),
        (InvalidParamsError(8)),
    ]
)
def test_to_jsonrpc_error(error):
    dispatcher = Dispatcher()
    assert dispatcher.to_jsonrpc_error(error)


@pytest.mark.parametrize(
    "func",
    [
        "date",
        "generic",
        "async_func"
    ]
)
def test_register(function_factory, func):
    dispatcher = Dispatcher()
    dispatcher.register(func, function_factory(func))
    assert func in dispatcher.method_registry.keys()


@pytest.mark.parametrize(
    "func,id,args,expected",
    [
        ("date", 1, [datetime.now().isoformat()], JsonRpcResponse),
        ("date", 1, {'d': datetime.now().isoformat()}, JsonRpcResponse),
        ("uuid", 1, ['1f4f3860-c530-4989-b185-fdecd0a00ccd'], JsonRpcError),
        ("async_func", 1, ["3", 1], JsonRpcResponse),
        ("async_func", 1, "invalid", JsonRpcError),
        ("fuzzy", 1, ["3", 1], JsonRpcError),
        ("no_parameter", None, [], None),
    ]
)
@pytest.mark.asyncio
async def test_dispatch(function_factory, func, id, args, expected):
    request = {
        'jsonrpc': '2.0',
        'method': func,
        'params': args or None,
        'id': id
    }
    dispatcher = Dispatcher()
    dispatcher.register(func, function_factory(func))
    result = await dispatcher.dispatch(json.dumps(request))
    if expected:
        assert expected(**json.loads(result))
    else:
        assert not result
