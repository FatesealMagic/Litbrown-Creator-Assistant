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
from PySide6.QtWidgets import *

from source.I18n import *

class ResultButton (QPushButton):
	
	POSSIBLE_VALUES = (None, True, False)
	
	__STYLESHEETS = {
		None:  '',
		True:  'background-color: #090;',
		False: 'background-color: #900;',
	}
	
	changed = Signal(object) # bool | None

	__value: bool | None = None

	def __init__ (self) -> None:
		super().__init__()
		self.clicked.connect(self.__evt_on_clicked)
		self.setText(I18n(self).labels['None'])

	def get_value (self) -> bool | None:
		return self.__value

	def set_value (self, val: bool | None) -> None:
		if self.__value == val:
			return
		self.__value = val
		self.setText(I18n(self).labels[str(val)])
		self.setStyleSheet('font-weight: bold;' + self.__STYLESHEETS[val])
		self.changed.emit(val)

	def __evt_on_clicked (self) -> None:
		index = self.POSSIBLE_VALUES.index(self.__value)
		index += 1
		index %= 3
		self.set_value(self.POSSIBLE_VALUES[index])

	val = Property(
		object,
		fget = get_value,
		fset = set_value,
		notify = changed,
		user = True,
	)
	
