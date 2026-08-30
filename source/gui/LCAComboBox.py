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
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class LCAComboBox (QComboBox):

	currentDataChanged = Signal(object)

	def __init__ (self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.currentIndexChanged.connect(self.__emit_data_changed)
		self.setItemDelegate(QStyledItemDelegate(self))
		self.setView(QListView())

	def __emit_data_changed (self) -> None:
		self.currentDataChanged.emit(self.currentData())

	def currentData (self) -> object:
		return super().currentData()

	def setData (self, data: object) -> None:
		self.setCurrentIndex(self.findData(data))

	val = Property(
		object,
		fget = currentData,
		fset = setData,
		notify = currentDataChanged,
		user = True,
	)

