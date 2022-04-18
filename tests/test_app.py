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
from unittest.mock import patch, AsyncMock

import pytest
from aio_pika.abc import AbstractIncomingMessage

import ribes.app
from ribes.dispatcher import Dispatcher


@patch.object(ribes.app, 'Dispatcher', spec=Dispatcher)
@patch.object(ribes.app, 'connect')
class TestRibes:

    app = ribes.app.Ribes("test")

    @pytest.mark.asyncio
    async def test_connect(self, mock_connect, mock_dispatcher):
        await self.app.connect()
        mock_connect.assert_called()
        mock_connect.return_value.channel.assert_called()
        mock_connect.return_value.channel.return_value.declare_exchange.assert_called()

    @pytest.mark.asyncio
    async def test_on_request_message(self, mock_connect, mock_dispatcher):
        mock_dispatcher.return_value.dispatch.return_value = 'Value'
        mock_message = AsyncMock(spec=AbstractIncomingMessage)
        mock_message.correlation_id = '12345'
        mock_message.reply_to = 'reply'
        mock_message.body = b'body'
        await self.app.on_request_message(mock_message)
        mock_dispatcher.return_value.dispatch.assert_called()

    @pytest.mark.asyncio
    async def test_on_response_message(self, mock_connect, mock_dispatcher):
        mock_message = AsyncMock(spec=AbstractIncomingMessage)
        mock_message.correlation_id = '12345'
        mock_message.body = b'body'
        getattr(self.app, '_futures')['12345'] = asyncio.Future()
        await self.app.on_response_message(mock_message)

