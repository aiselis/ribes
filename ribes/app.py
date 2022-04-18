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
import logging

from functools import cached_property
from typing import MutableMapping, Any, Callable

from aio_pika import Message, connect
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractConnection,
    AbstractChannel,
    AbstractExchange,
    AbstractQueue,
    ExchangeType
)

from ribes.caller import RemoteCaller
from ribes.dispatcher import Dispatcher
from ribes.settings import RibesSettings


class Ribes:
    logger = logging.getLogger(__name__)

    settings: RibesSettings

    _connection: AbstractConnection = None
    _channel: AbstractChannel = None
    _exchange: AbstractExchange = None

    _callback_queue: AbstractQueue = None
    _futures: MutableMapping[str, asyncio.Future] = {}

    @cached_property
    def _loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.get_running_loop()

    @cached_property
    def _dispatcher(self) -> Dispatcher:
        return Dispatcher()

    def __init__(self, name: str):
        self.settings = RibesSettings()
        self.settings.exchange = name

    async def connect(self) -> None:
        if self._connection:
            return
        self.logger.info(f'Connection to {self.settings.broker_url}')
        self._connection = await connect(self.settings.broker_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(self.settings.exchange, durable=True,
                                                              type=ExchangeType.TOPIC)

    async def on_request_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False):
            assert message.reply_to is not None
            request = message.body.decode()
            if response := await self._dispatcher.dispatch(request):
                await self._exchange.publish(
                    Message(body=response.encode(), correlation_id=message.correlation_id),
                    routing_key=message.reply_to,
                )

    async def on_response_message(self, message: AbstractIncomingMessage):
        if message.correlation_id is None:
            self.logger.error(f"Bad message {message!r}")
            return
        future: asyncio.Future = self._futures.pop(message.correlation_id)
        future.set_result(message.body.decode())

    async def start_listener(self):
        await self.connect()
        self.logger.info(f'Ribes Listener started')
        for routing_key, queue_name in self.settings.routes.items():
            queue = await self._channel.declare_queue(queue_name, durable=True)
            await queue.bind(self._exchange, routing_key=routing_key)
            await queue.consume(self.on_request_message)

    async def start_caller(self):
        await self.connect()
        self.logger.info(f'Ribes Caller started')
        self._callback_queue = await self._channel.declare_queue(exclusive=True)
        await self._callback_queue.bind(self._exchange, self._callback_queue.name)
        await self._callback_queue.consume(self.on_response_message)

    def caller(self, name: str, ignore_result=False) -> RemoteCaller:
        return RemoteCaller(name, ignore_result, self._loop, self._futures, self._exchange, self._callback_queue.name)

    def register(self, name: str) -> Callable[..., Any]:
        def decorator(func) -> Callable[..., Any]:
            nonlocal name, self
            self._dispatcher.register(name, func)
            return func

        return decorator
