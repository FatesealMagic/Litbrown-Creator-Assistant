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

import time

from loguru import logger

from ..LCAWorkerObject import *
from ...common.LCAProjectState import *
from ...models.LCAProjectStateModel import *
from ...integrations.obs.LCAObsIntegration import *

class LCAMObsRecordPuppeteerWorkerObject (LCAWorkerObject):
	
	on_connected = Signal(bool)
	on_scene_changed = Signal(str)
	on_active_toggled = Signal(bool)

	__HEARTBEAT_INTERVAL = 500

	__obs: LCAObsIntegration | None = None
	__timer: QTimer

	__old_state: dict | None = None

	def __init__ (self):
		super().__init__()

	@Slot()
	def slot_construct (self) -> None:
		self.__reset_old_state()
		self.__initiate_obs_connection()
		self.__hookup_slots()
		self.__register_callbacks()
		self.__start_heartbeat_timer()

	def __reset_old_state (self) -> dict:
		ret = self.__old_state
		self.__old_state = LCAProjectState().model.model_dump(mode = 'json')
		return ret

	def __initiate_obs_connection (self) -> None:
		logger.info('Attempting OBS connection...')
		self.on_connected.emit(False)
		self.__obs = LCAObsIntegration('record')
		while True:
			try:
				self.__obs.connect()
				self.on_connected.emit(True)
				break
			except ConnectionRefusedError:
				self.on_connected.emit(False)
		logger.info('OBS connection successful')

	def __hookup_slots (self) -> None:
		LCAProjectState().updated_model.connect(self.slot_state_updated)

	def __register_callbacks (self) -> None:
		pass

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

	@Slot(LCAProjectStateModel)
	def slot_state_updated (self, state: LCAProjectStateModel) -> None:
		old_state = self.__reset_old_state()
		if (
			state.segment_id and (
				(old_state['segment_id'] != state.segment_id) or
				(old_state['segment_number'] != state.segment_number)
			)
		):
			self.__handle_segment_updated(state)
		if old_state['active'] != state.active:
			self.__handle_active_toggle(state)

	def __handle_segment_updated (self, state: LCAProjectStateModel) -> None:
		scene_name = Settings().series_segment_from_id(state.project.series_id, state.segment_id).obs_scene_name
		if state.active:
			self.__stop_recording()
		self.__set_segment_recording_filename(state)
		self.__obs.req_client.set_current_program_scene(scene_name)
		if state.active:
			self.__start_recording()
			self.__update_recording_start_time(state)
		self.on_scene_changed.emit(scene_name)

	def __handle_active_toggle (self, state: LCAProjectStateModel) -> None:
		self.__stop_recording()
		if state.active:
			self.__set_segment_recording_filename(state)
			self.__start_recording()
			self.__update_recording_start_time(state)
		self.on_active_toggled.emit(state.active)

	def __stop_recording (self) -> None:
		try:
			self.__obs.req_client.stop_record()
		except obsws_python.error.OBSSDKRequestError:
			pass
		else:
			time.sleep(3) # Wait for OBS to actually stop recording

	def __start_recording (self) -> None:
		self.__obs.req_client.start_record()
		time.sleep(1) # Wait for OBS to create the output file

	def __set_segment_recording_filename (self, state: LCAProjectStateModel) -> None:
		target_recording_path = state.project.path_footage(
			segment_id = state.segment_id,
			segment_number = state.segment_number,
		).resolve()
		self.__obs.req_client.set_profile_parameter(
			'SimpleOutput',
			'FilePath',
			str(target_recording_path.parent),
		)
		self.__obs.req_client.set_profile_parameter(
			'AdvOut',
			'RecFilePath',
			str(target_recording_path.parent),
		)
		self.__obs.req_client.set_profile_parameter(
			'Output',
			'FilenameFormatting',
			str(target_recording_path.parts[-1]).split('.')[0],
		)

	def __update_recording_start_time (self, state: LCAProjectStateModel) -> None:
		req_start_ts = time.time()
		duration = self.__obs.req_client.get_record_status().output_duration / 1000.0
		req_end_ts = time.time()
		start_ts = req_start_ts + ((req_end_ts - req_start_ts) / 2) - duration
		with LCAProjectState():
			LCAProjectState().model.start_timestamps[f'{state.segment_id}-{state.segment_number}'] = start_ts

