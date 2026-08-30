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

import datetime

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..Config import *
from ..I18n import *
from ..Assets import *
from ..Settings import *
from ..Util import *

from .LCAWidget import *

class LCADateAndTimePickerWidget (LCAWidget):

	changed = Signal(str)
	
	__orientation: Qt.Orientation
	__date_edit: QDateEdit
	__time_edit: QTimeEdit
	
	def __init__ (self,
		orientation: Qt.Orientation = Qt.Orientation.Horizontal,
	*args, **kwargs):
		self.__orientation = orientation
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		layout = (QHBoxLayout if self.__orientation == Qt.Orientation.Horizontal else QVBoxLayout)(self)
		layout.setContentsMargins(0, 0, 0, 0)
		if date_edit := QDateEdit():
			self.__date_edit = date_edit
			date_edit.setCalendarPopup(True)
			date_edit.setDate(QDate.currentDate())
			date_edit.dateChanged.connect(self.__emit_changed)
		layout.addWidget(date_edit)
		if time_edit := QTimeEdit():
			self.__time_edit = time_edit
			time_edit.setDisplayFormat(Settings().tools.general.time_display_format)
			time_edit.timeChanged.connect(self.__emit_changed)
		layout.addWidget(time_edit)

	def __emit_changed (self) -> None:
		self.changed.emit(self.get_value())

	def get_value (self) -> str:
		return datetime.datetime.combine(
			self.__date_edit.date().toPython(),
			self.__time_edit.time().toPython(),
			datetime.datetime.now().astimezone().tzinfo
		).isoformat()

	def set_value (self, val: str) -> None:
		# TODO does this actually work? Can I setDateTime on these edits?
		logger.debug(val)
		qdatetime = QDateTime.fromString(val, Qt.DateFormat.ISODate)
		self.__date_edit.setDateTime(qdatetime)
		self.__time_edit.setDateTime(qdatetime)

	val = Property(
		datetime.datetime,
		fget = get_value,
		fset = set_value,
		notify = changed,
		user = True,
	)

