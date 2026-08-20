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

import typing

from loguru import logger

from PySide6.QtCore import *

from ..common.LCASingleton import *
from ..models.LCAProjectFileModel import *
from ..models.LCAProjectStateModel import *
from ..threads.LCAWorkerThread import *
from ..threads.common.LCAProjectStateWebsocketWorkerObject import *

class LCAProjectState (metaclass = LCASingleton):
	
	class _LCAProjectStateSignals (QObject):
		updated = Signal(dict)

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
		self.__model = LCAProjectStateModel(project = project)
		self.__start_ws_server()

	def __start_ws_server (self) -> None:
		loop = QEventLoop()
		self.__thread = LCAWorkerThread(LCAProjectStateWebsocketWorkerObject(self.__project.get_slug()))
		self.__thread.worker.on_listen.connect(lambda success : loop.exit(0 if success else 1))
		self.__signals.updated.connect(self.__thread.worker.slot_project_state_updated)
		self.__thread.start()
		if ret := loop.exec():
			raise RuntimeError(f'Project state server already running {ret}')

	@property
	def updated (self) -> Signal:
		return self.__signals.updated

	@property
	def model (self) -> LCAProjectStateModel:
		return self.__model

	def shutdown (self) -> None:
		self.__thread.quit()
		self.__thread.wait()

	def __enter__ (self) -> None:
		self.__mutex.acquire()
		return self

	def __exit__ (self, exc_type, exc_val, exc_tb):
		self.__mutex.release()
		self.updated.emit(self.__model.model_dump(mode = 'json'))

