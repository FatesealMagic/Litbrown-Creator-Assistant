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

import functools
import json
import time
import traceback
import typing

from loguru import logger

from PySide6.QtCore import *

from ..common.LCASingleton import *
from ..models.LCAProjectFileModel import *
from ..models.LCAProjectStateModel import *
from ..threads.LCAWorkerThread import *
from ..threads.common.LCAProjectStateWebsocketWorkerObject import *

class LCAProjectState (metaclass = LCASingleton):

	frozen: bool = False
	
	class _LCAProjectStateSignals (QObject):
		updated_model = Signal(LCAProjectStateModel)
		updated_dict = Signal(dict)

	__project: LCAProjectFileModel
	__signals: _LCAProjectStateSignals
	__mutex: threading.Lock
	__model: LCAProjectStateModel
	__thread: LCAWorkerThread

	def __init__ (self, project: LCAProjectFileModel):
		logger.debug('in project state')
		self.__project = project
		self.__signals = self._LCAProjectStateSignals()
		self.__mutex = threading.Lock()
		self.__model = LCAProjectStateModel( **( self.__load_previous_state() | {
			'project': project,
			'active': False,
			'segment_id': None,
			'segment_number': 0,
			'last_modified_ts': int(time.time() * 1e6),
		} ) )
		self.__start_ws_server()

	def __load_previous_state (self) -> dict:
		state_paths = self.__project.path_state_all()
		if not state_paths:
			return {}
		return json.loads(self.__project.read_file(state_paths[-1], text = True))

	def __start_ws_server (self) -> None:
		loop = QEventLoop()
		self.__thread = LCAWorkerThread(LCAProjectStateWebsocketWorkerObject(self.__project.slug()))
		self.__thread.worker.on_listen.connect(lambda success : loop.exit(0 if success else 1))
		self.__signals.updated_dict.connect(self.__thread.worker.slot_project_state_updated)
		self.__thread.start()
		if ret := loop.exec():
			raise RuntimeError(f'Project state server already running {ret}')

	@property
	def updated_dict (self) -> Signal:
		return self.__signals.updated_dict

	@property
	def updated_model (self) -> Signal:
		return self.__signals.updated_model

	@property
	def model (self) -> LCAProjectStateModel:
		return self.__model

	def shutdown (self) -> None:
		self.frozen = True
		self.__thread.quit()
		self.__thread.wait()

	def __enter__ (self) -> None:
		self.__mutex.acquire()
		self.__model.last_modified_ts = int(1e6 * time.time())
		return self

	def __exit__ (self, exc_type, exc_val, exc_tb):
		if self.frozen:
			self.__mutex.release()
			return
		logger.debug('\n' + ''.join(traceback.format_stack()))
		model_dict = self.__model.model_dump(mode = 'json')
		if self.__model.active:
			self.__project.overwrite_file(
				self.__project.path_state(),
				json.dumps({k: v for k, v in model_dict.items() if k not in ('project',)}),
				text = True,
			)
		self.__mutex.release()
		self.updated_model.emit(self.__model)
		self.updated_dict.emit(model_dict)

	def in_context (method):
		@functools.wraps(method)
		def wrapper (self, *args, **kwargs):
			if not self.__mutex.locked():
				raise RuntimeError(f'Method not called within context manager: {method}')
			return method(self, *args, **kwargs)
		return wrapper

	@in_context
	def set_segment (self, segment_id: str | None, segment_number: int) -> None:
		self.__model.segment_id = segment_id
		self.__model.segment_number = segment_number
		if segment_id:
			segment_slug = LCAProjectFileModel.slug(segment_id, segment_number)
			self.__project.events.segments[segment_slug] = LCAProjectFileModel.EventsModel.SegmentModel()

	@property
	def muted (self) -> bool:
		return len(self.__project.events.mutes) and not self.__project.events.mutes[-1][1]

	@muted.setter
	@in_context
	def muted (self, val: bool) -> None:
		self.__model.muted = val
		if val and not self.muted:
			self.__project.events.mutes.append((self.__model.last_modified_ts, None))
		if not val and self.muted:
			self.__project.events.mutes[-1] = (self.__project.events.mutes[-1][0], self.__model.last_modified_ts)

	@in_context
	def mark_mistake (self) -> None:
		if self.__model.segment_id is None:
			return
		self.__model.mistake_count += 1
		self.__project.events.segments[LCAProjectFileModel.slug(
			self.__model.segment_id, self.__model.segment_number
		)].mistakes_ts.append(self.__model.last_modified_ts)

	@in_context
	def set_segment_start_ts (self, ts: int) -> None:
		self.__project.events.segments[LCAProjectFileModel.slug(
			self.__model.segment_id, self.__model.segment_number
		)].start_ts = ts