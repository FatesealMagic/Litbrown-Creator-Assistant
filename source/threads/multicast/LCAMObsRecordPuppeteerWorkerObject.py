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

from loguru import logger

from ..LCAWorkerObject import *
from ...integrations.obs.LCAObsIntegration import *

class LCAMObsRecordPuppeteerWorkerObject (LCAWorkerObject):
	
	do_scene_change = Signal(str)
	do_scene_change_complete = Signal(str)
	
	on_connected = Signal(bool)
	on_scene_changed = Signal(str)

	__HEARTBEAT_INTERVAL = 500

	__instance: str
	__obs: LCAObsIntegration | None = None
	__timer: QTimer

	def __init__ (self, instance: str):
		self.__instance = instance
		super().__init__()
		self.do_scene_change.connect(self.slot_do_scene_change)

	@Slot()
	def slot_construct (self) -> None:
		self.__initiate_obs_connection()
		self.__register_callbacks()
		self.__start_heartbeat_timer()

	def __initiate_obs_connection (self) -> None:
		logger.info('Attempting OBS connection...')
		self.on_connected.emit(False)
		self.__obs = LCAObsIntegration(self.__instance)
		while True:
			try:
				self.__obs.connect()
				self.on_connected.emit(True)
				break
			except ConnectionRefusedError:
				self.on_connected.emit(False)
		logger.info('OBS connection successful')

	def __register_callbacks (self) -> None:
		self.__obs.evt_client.callback.register(self.on_current_program_scene_changed)

	def __start_heartbeat_timer (self) -> None:
		self.__timer = QTimer(self)
		self.__timer.setInterval(self.__HEARTBEAT_INTERVAL)
		self.__timer.timeout.connect(self.slot_timer)
		self.__timer.start()

	@Slot()
	def slot_destruct (self) -> None:
		self.__obs.disconnect()
		self.__obs = None

	@Slot()
	def slot_timer (self) -> None:
		try:
			self.__obs.req_client.get_stats()
		except Exception as e:
			logger.exception(e)
			self.__timer.stop()
			self.slot_destruct()
			self.slot_construct()

	@Slot(str)
	def slot_do_scene_change (self, scene_name: str) -> None:
		self.__obs.req_client.set_current_program_scene(scene_name)
		self.do_scene_change_complete.emit(scene_name)
		self.on_scene_changed.emit(scene_name)

	def on_current_program_scene_changed (self, data: dict) -> None:
		self.on_scene_changed.emit(data.scene_name)

