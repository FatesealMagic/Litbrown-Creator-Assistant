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

from ..Assets import Assets

from .LCAWidget import *

class LCAListCreatorWidget (LCAWidget):

	__text_input: str
	__list_widget: QListWidget

	changed = Signal(list) # list[str]

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		if top_widget := QWidget():
			top_layout = QHBoxLayout(top_widget)
			top_layout.setContentsMargins(0, 0, 0, 0)
			if text_input := QLineEdit():
				self.__text_input = text_input
				text_input.returnPressed.connect(self.__evt_add_item)
			top_layout.addWidget(text_input)
			if add_btn := QPushButton():
				add_btn.setIcon(Assets.QIcon('icons/plus.png'))
				add_btn.clicked.connect(self.__evt_add_item)
			top_layout.addWidget(add_btn)
			if del_btn := QPushButton():
				del_btn.setIcon(Assets.QIcon('icons/close.png'))
				del_btn.clicked.connect(self.__evt_del_item)
			top_layout.addWidget(del_btn)
		layout.addWidget(top_widget)
		if list_widget := QListWidget():
			self.__list_widget = list_widget
			list_widget.setSortingEnabled(True)
			list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
			list_widget.setDropIndicatorShown(True)
			list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
			list_widget.itemActivated.connect(self.__evt_del_item)
			list_widget.model().rowsMoved.connect(lambda *_ : self.changed.emit(self.get_value()))
		layout.addWidget(list_widget)

	def get_value (self) -> list[str]:
		return [ self.__list_widget.item(i).text() for i in range(self.__list_widget.count()) ]

	def set_value (self, val: list[str]) -> None:
		if self.get_value() == val:
			return
		self.__list_widget.clear()
		for item in val:
			self.__list_widget.addItem(item)
		self.changed.emit(val)

	def __evt_add_item (self) -> None:
		self.__list_widget.addItem(self.__text_input.text())
		self.__text_input.clear()
		self.changed.emit(self.get_value())

	def __evt_del_item (self, *_) -> None:
		if self.__list_widget.currentRow() == -1:
			return
		item = self.__list_widget.takeItem(self.__list_widget.currentRow())
		del item
		self.changed.emit(self.get_value())

	val = Property(
		list,
		fget = get_value,
		fset = set_value,
		notify = changed,
		user = True,
	)

