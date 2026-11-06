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

import enum

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..Assets import Assets
from ..I18n import I18n

from .LCAComboBox import LCAComboBox
from .LCAWidget import LCAWidget

class LCAListCreatorWidget (LCAWidget):

	class Mode (enum.Enum):
		TEXT = 'text'
		COMBO = 'combo'

	__data_to_label: dict[str, str]
	__text_input: QLineEdit
	__combo_input: LCAComboBox
	__list_widget: QListWidget

	changed = Signal(list) # list[str]

	def __init__ (self,
		mode: Mode = Mode.TEXT,
		data_to_label: dict | None = None,
		*args, **kwargs,
	):
		self.__mode = mode
		self.__data_to_label = data_to_label or {}
		super().__init__()

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		if top_widget := QWidget():
			top_layout = QHBoxLayout(top_widget)
			top_layout.setContentsMargins(0, 0, 0, 0)
			if self.__mode is self.Mode.TEXT:
				if text_input := QLineEdit():
					self.__text_input = text_input
					text_input.returnPressed.connect(self.__evt_add_item)
				top_layout.addWidget(text_input, 1)
				if add_btn := QPushButton():
					add_btn.setIcon(Assets.QIcon('icons/plus.png'))
					add_btn.clicked.connect(self.__evt_add_item)
				top_layout.addWidget(add_btn, 0)
			elif self.__mode is self.Mode.COMBO:
				if combo_input := LCAComboBox():
					self.__combo_input = combo_input
					combo_input.setPlaceholderText(I18n(self).combo_placeholder)
					combo_input.currentIndexChanged.connect(self.__evt_add_item)
					self.set_possible_selections(self.__data_to_label)
				top_layout.addWidget(combo_input, 1)
			if del_btn := QPushButton():
				del_btn.setIcon(Assets.QIcon('icons/close.png'))
				del_btn.clicked.connect(self.__evt_del_item)
			top_layout.addWidget(del_btn, 0)
		layout.addWidget(top_widget)
		if list_widget := QListWidget():
			self.__list_widget = list_widget
			list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
			list_widget.setDropIndicatorShown(True)
			list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
			list_widget.itemActivated.connect(self.__evt_del_item)
			list_widget.model().rowsMoved.connect(lambda *_ : self.changed.emit(self.get_value()))
		layout.addWidget(list_widget)

	def set_possible_selections (self,
		data_to_label: dict[str, str],
		/,
	) -> None:
		self.__data_to_label = data_to_label
		with QSignalBlocker(self.__combo_input):
			self.__combo_input.clear()
			for data, label in data_to_label.items():
				self.__combo_input.addItem(label, data)
			self.__combo_input.setCurrentIndex(-1)

	def get_value (self) -> list[str]:
		val = [ self.__list_widget.item(i).data(Qt.UserRole) for i in range(self.__list_widget.count()) ]
		logger.debug(val)
		return val

	def set_value (self, values: list[str]) -> None:
		if self.get_value() == values:
			return
		self.__list_widget.clear()
		for val in values:
			if self.__mode is self.Mode.TEXT:
				label = val
			elif self.__mode is self.Mode.COMBO:
				label = self.__data_to_label.get(val, None)
				if label is None:
					continue
			item = QListWidgetItem(label)
			item.setData(Qt.UserRole, val)
			self.__list_widget.addItem(item)
		self.changed.emit(val)

	def __evt_add_item (self, *_) -> None:
		if self.__mode is self.Mode.TEXT:
			text = self.__text_input.text()
			if not text:
				return
			item = QListWidgetItem(text)
			item.setData(Qt.UserRole, text)
			self.__list_widget.addItem(item)
			self.__text_input.clear()
		elif self.__mode is self.Mode.COMBO:
			if self.__combo_input.currentIndex() == -1:
				return
			item = QListWidgetItem(self.__combo_input.currentText())
			item.setData(Qt.UserRole, self.__combo_input.currentData())
			self.__list_widget.addItem(item)
			with QSignalBlocker(self.__combo_input):
				self.__combo_input.setCurrentIndex(-1)
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

