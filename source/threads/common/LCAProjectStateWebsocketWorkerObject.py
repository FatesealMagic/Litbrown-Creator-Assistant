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

from PySide6.QtCore import *
from PySide6.QtWebSockets import *

from ...Config import Config
from ...Settings import Settings

from ..LCAWorkerObject import LCAWorkerObject

class LCAProjectStateWebsocketWorkerObject (LCAWorkerObject):

	on_listen = Signal(bool)

	__slug: str
	__state_dict: dict
	__settings_dict: dict
	__wss: QWebSocketServer
	__clients: list[QWebSocket]
	__clients_mutex: threading.Lock

	def __init__ (self, slug: str, initial_state: dict):
		self.__slug = slug
		self.__state_dict = initial_state
		self.__settings_dict = Settings().model_dump(mode = 'json')
		self.__clients = []
		self.__clients_mutex = threading.Lock()
		super().__init__()

	@Slot()
	def slot_construct (self) -> None:
		self.__wss = QWebSocketServer(Config().network.websocket_name, QWebSocketServer.SslMode.NonSecureMode)
		self.__wss.newConnection.connect(self.slot_new_connection)
		Settings().signals().changed.connect(self.slot_settings_updated)
		self.on_listen.emit(self.__wss.listen(port = Config().network.websocket_port))

	@Slot()
	def slot_new_connection (self) -> None:
		client = self.__wss.nextPendingConnection()
		logger.info(f'Received new websocket connection: {client}')
		with self.__clients_mutex:
			self.__send_client_update(client)
			self.__clients.append(client)

	@Slot(dict)
	def slot_project_state_updated (self, state: dict) -> None:
		if state == self.__state_dict:
			return
		logger.debug('ws: project state updated')
		with self.__clients_mutex:
			self.__state_dict = state
			for client in self.__clients:
				self.__send_client_update(client)

	@Slot()
	def slot_settings_updated (self) -> None:
		logger.debug('ws: settings updated')
		with self.__clients_mutex:
			self.__settings_dict = Settings().model_dump(mode = 'json')
			for client in self.__clients:
				self.__send_client_update(client)

	def __send_client_update (self, client: QWebSocket) -> None:
		client.sendTextMessage(json.dumps({
			'state': self.__state_dict,
			'settings': self.__settings_dict,
		}))

	@Slot()
	def slot_destruct (self) -> None:
		self.__wss.close()
		self.__wss = None
		self.quit.emit()

