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

from asyncio import Future, AbstractEventLoop
from typing import MutableMapping
from unittest.mock import AsyncMock, Mock

import pytest
from aio_pika.abc import AbstractExchange

from ribes.caller import RemoteCaller
from ribes.errors import InvalidRequestError, BaseJsonRpcError
from ribes.models import JsonRpcResponse, JsonRpcError, ErrorStatus
from tests.utils import does_not_raise


@pytest.mark.parametrize(
    "ignore_result,expected_result,expected",
    [
        (True, None, does_not_raise()),
        (False, [1, "2"], does_not_raise()),
        (False, InvalidRequestError(), pytest.raises(InvalidRequestError))
    ]
)
@pytest.mark.asyncio
async def test_call(ignore_result, expected_result, expected):
    futures: MutableMapping[str, Future] = {}
    exchange = AsyncMock(spec=AbstractExchange)
    future = Future()
    id = None if ignore_result else 8
    if isinstance(expected_result, BaseJsonRpcError):
        status = ErrorStatus(code=expected_result.code, message=expected_result.message)
        future.set_result(JsonRpcError(id=id, error=status).json(exclude_none=True))
    elif expected_result:
        future.set_result(JsonRpcResponse(id=id, result=expected_result).json())
    else:
        future.set_result(None)
    loop = AsyncMock(spec=AbstractEventLoop)
    loop.create_future = Mock(return_value=future)
    with expected:
        caller = RemoteCaller("method", ignore_result, loop, futures, exchange, "callback")
        result = await caller(0, 1)
        assert expected_result == result
