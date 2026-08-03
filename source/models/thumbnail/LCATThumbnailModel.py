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

import threading
import typing

from loguru import logger
import pydantic

from PySide6.QtCore import *

# Model ########################################################################

class LCATThumbnailModel (pydantic.BaseModel, validate_assignment = True, extra = 'forbid'):
	user: dict = pydantic.Field(default_factory = lambda : {})
	method: str = 'multicast'
	format: str = 'video'
	series_id: str | None = None
	variant_id: str | None = None
	entry_number: int | None = None

# Implementation ###############################################################

	class _SignalsObject (QObject):
		changed = Signal()

	_signals: _SignalsObject = pydantic.PrivateAttr(default_factory = _SignalsObject)
	_mutex: threading.Lock = pydantic.PrivateAttr(default_factory = threading.Lock)

	def __enter__ (self):
		self._mutex.acquire()
		logger.debug(self._mutex)

	def __exit__ (self, exc_type, exc_val, exc_tb):
		self._mutex.release()
		self._signals.changed.emit()
		return False

	def signals (self) -> _SignalsObject:
		return self._signals

