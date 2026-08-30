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

import traceback

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..Config import *
from ..I18n import *
from ..Util import *

from .LCAWidget import *

class LCAToggleButtonGroupWidget (LCAWidget):
	
	changed = Signal(object)
	
	__STYLESHEET = 'QPushButton:checked { border: 1px solid #f69; }'
	
	__layout_class: QLayout
	__columns: int
	__button_group: QButtonGroup

	def __init__ (self, parent = None, *, rows: int = 0, columns: int = 0):
		if not (rows ^ columns):
			raise ValueError('Only set one of rows or columns with QGridLayout')
		self.__columns = columns
		self.__rows = rows
		super().__init__(parent)
	
	def _setup_layout (self) -> None:
		layout = QGridLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		self.__button_group = QButtonGroup(self)
		self.__button_group.setExclusive(True)

	def addButton (self, label: str, value: object | None = None) -> None:
		if value is None:
			value = label
		button = QPushButton(label)
		button.setCheckable(True)
		button.lca_value = value
		if not self.layout().count():
			button.setChecked(True)
		button.clicked.connect(self.__evt_button_clicked)
		self.__button_group.addButton(button, self.layout().count() - 1)
		if self.__columns:
			row = self.layout().count() // self.__columns
			col = self.layout().count()  % self.__columns
		elif self.__rows:
			row = self.layout().count()  % self.__rows
			col = self.layout().count() // self.__rows
		self.layout().addWidget(button, row, col)

	def __evt_button_clicked (self) -> None:
		self.changed.emit(self.get_value())

	def get_value (self) -> object | None:
		checked_button = self.__button_group.checkedButton()
		if not checked_button:
			return None
		return checked_button.lca_value

	def set_value (self, value: object) -> None:
		if value == self.get_value():
			return
		for button in self.__button_group.buttons():
			button.setChecked(button.lca_value == value)
		self.changed.emit(self.get_value())

	val = Property(
		object,
		fget = get_value,
		fset = set_value,
		notify = changed,
		user = True,
	)

