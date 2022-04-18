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

import asyncio
import json
import logging
import uuid
from typing import MutableMapping

from aio_pika import Message
from aio_pika.abc import AbstractExchange

from ribes.errors import ErrorMap
from ribes.models import JsonRpcRequest, JsonRpcResponse


class RemoteCaller:
    logger = logging.getLogger(__name__)

    def __init__(self,
                 name: str,
                 ignore_result: bool,
                 loop: asyncio.AbstractEventLoop,
                 futures: MutableMapping[str, asyncio.Future],
                 exchange: AbstractExchange,
                 callback: str,
                 ):
        self._name = name
        self._ignore_result = ignore_result
        self._loop = loop
        self._futures = futures
        self._exchange = exchange
        self._callback = callback
        self._id = None if ignore_result else 1

    async def __call__(self, *args, **kwargs):
        params = args if args else kwargs
        correlation_id = str(uuid.uuid4())
        future = self._loop.create_future()
        self._futures[correlation_id] = future
        if self._ignore_result:
            request = JsonRpcRequest(method=self._name, params=params)
        else:
            request = JsonRpcRequest(method=self._name, params=params, id=self._id)
            self._id += 1
        await self._exchange.publish(
            Message(
                request.json(exclude_none=True).encode(),
                content_type="application/json",
                correlation_id=correlation_id,
                reply_to=self._callback,
            ),
            routing_key=self._name,
        )
        if not self._ignore_result:
            result = json.loads(await future)
            if 'error' in result.keys():
                raise ErrorMap.get(result['error']['code'])()
            if not self._ignore_result:
                return JsonRpcResponse(**result).result
