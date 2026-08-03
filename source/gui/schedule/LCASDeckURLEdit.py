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

from ...I18n import *

from ..LCAWidget import *
from ...models.LCADecklistModel import *

class LCASDeckURLEdit (LCAWidget):
	
	changed = Signal(list)
	
	__row1_widget: QWidget
	__url_inputs: list[QLineEdit]

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		self.__row1_widget = QWidget()
		row1_layout = QHBoxLayout(self.__row1_widget)
		row1_layout.setContentsMargins(0, 0, 0, 0)
		add_btn = QPushButton(I18n(self).url_add)
		add_btn.clicked.connect(self.__add_url_input)
		row1_layout.addWidget(add_btn)
		layout.addWidget(self.__row1_widget)
		self.__url_inputs = []

	def get_value (self) -> list[LCADecklistModel]:
		return [ LCADecklistModel(url = url_input.text()) for url_input in self.__url_inputs ]

	def set_value (self, value: list[LCADecklistModel]) -> None:
		value = value or []
		if value == self.get_value():
			return
		for old_val, new_val in zip(self.get_value(), value):
			if old_val.url != new_val.url:
				break
		else:
			if len(self.get_value()) == len(value):
				return
		while len(value) > len(self.__url_inputs):
			self.__add_url_input()
		while len(value) < len(self.__url_inputs):
			self.__remove_url_input()
		for i, val in enumerate(value):
			self.__url_inputs[i].setText(val.url)
		self.changed.emit(value)

	def __add_url_input (self) -> None:
		url_input = QLineEdit()
		url_input.setPlaceholderText(I18n(self).url_placeholder)
		url_input.editingFinished.connect(self.__evt_editing_finished)
		if len(self.__url_inputs):
			self.layout().addWidget(url_input)
		else:
			self.__row1_widget.layout().addWidget(url_input)
		self.__url_inputs.append(url_input)
		self.__evt_editing_finished()

	def __remove_url_input (self) -> None:
		url_input = self.__url_inputs.pop()
		if len(self.__url_inputs):
			self.layout().removeWidget(url_input)
		else:
			self.__row1_widget.layout().removeWidget(url_input)
		url_input.deleteLater()

	def __evt_editing_finished (self, text: str | None = None) -> None:
		self.changed.emit(self.get_value())

	val = Property(
		list,
		fget = get_value,
		fset = set_value,
		notify = changed,
		user = True,
	)

