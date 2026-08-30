"""
  " SPDX-License-Identifier: AGPL-3.0-or-later
  "
  " Litbrown Creator Assistant
  " Automation Software for Magic: the Gathering Online (TM) Content Creators
  " Copyright (C) 2026 Reid Litbrown
  "
  " This program is free software: you can redistribute it and/or modify
  " it under the terms of the GNU Affero General Public License as published
  " by the Free Software Foundation, either version 3 of the License, or
  " (at your option) any later version.
  "
  " This program is distributed in the hope that it will be useful,
  " but WITHOUT ANY WARRANTY; without even the implied warranty of
  " MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  " GNU Affero General Public License for more details.
  "
  " You should have received a copy of the GNU Affero General Public License
  " along with this program.  If not, see <https://www.gnu.org/licenses/>.
  "
  """

import json
import threading

from loguru import logger

from PySide6.QtWebSockets import *

from ...Config import *

from ..LCAWorkerObject import *

class LCAProjectStateWebsocketWorkerObject (LCAWorkerObject):

	on_listen = Signal(bool)
	
	__slug: str
	__wss: QWebSocketServer
	__clients: list[QWebSocket]
	__clients_mutex: threading.Lock

	def __init__ (self, slug: str):
		self.__slug = slug
		self.__clients = []
		self.__clients_mutex = threading.Lock()
		super().__init__()

	@Slot()
	def slot_construct (self) -> None:
		self.__wss = QWebSocketServer(Config().network.websocket_name, QWebSocketServer.SslMode.NonSecureMode)
		self.__wss.newConnection.connect(self.slot_new_connection)
		self.on_listen.emit(self.__wss.listen(port = Config().network.websocket_port))

	@Slot()
	def slot_new_connection (self) -> None:
		client = self.__wss.nextPendingConnection()
		logger.info(f'Received new websocket connection: {client}')
		client.textMessageReceived.connect(self.slot_text_message_received)
		with self.__clients_mutex:
			self.__clients.append(client)

	@Slot(dict)
	def slot_project_state_updated (self, state: dict) -> None:
		with self.__clients_mutex:
			for client in self.__clients:
				client.sendTextMessage(json.dumps(state))

	@Slot(str)
	def slot_text_message_received (self, message: str) -> None:
		logger.debug(f'[ws] {self.sender()}: {message}')

	@Slot()
	def slot_destruct (self) -> None:
		self.__wss.close()
		self.__wss = None

