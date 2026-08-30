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

from PySide6.QtCore import *

from ..Config import *

class LCATaskThread (QThread):
	
	complete = Signal(bool)
	error    = Signal(Exception)
	result   = Signal(object)
	update   = Signal(object)
	progress = Signal(float)

	def __init__ (self, **kwargs):
		super().__init__()
		self.__kwargs = QObject()
		self.__kwargs.kwargs = kwargs

	def run (self) -> None:
		success = True
		try:
			result = self._run(**self.__kwargs.kwargs)
		except Exception as e:
			success = False
			logger.exception(e)
			self.error.emit(e)
		else:
			self.result.emit(result)
		finally:
			self.complete.emit(success)

	def _run (self) -> object:
		raise NotImplementedError

	def _emit_update (self, update: object) -> None:
		self.update.emit(update)

	def _emit_progress (self, progress: float) -> None:
		if progress < 0:
			progress = 0.0
		if progress > 1:
			progress = 1.0
		self.progress.emit(float(progress))

