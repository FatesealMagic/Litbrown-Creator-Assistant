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

from ..Assets import *

from .LCAWidget import *

class LCACarouselWidget (LCAWidget):
	
	changed = Signal(object)
	
	__datas: list[object]
	__widgets = list[QWidget]
	
	def _setup_layout (self) -> None:
		self.__datas = []
		self.__widgets = []
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		if group_widget := QGroupBox():
			group_layout = QHBoxLayout(group_widget)
			group_layout.setContentsMargins(0, 0, 0, 0)
			if decrement_btn := QPushButton():
				decrement_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
				decrement_btn.setProperty('css_class', 'decrement')
				decrement_btn.setIcon(Assets.QIcon('style/leftarrow.svg'))
				decrement_btn.clicked.connect(self.__evt_decrement_clicked)
			group_layout.addWidget(decrement_btn)
			if stacked_widget := QStackedWidget():
				self.__stacked_widget = stacked_widget
				stacked_widget.currentChanged.connect(self.__evt_current_changed)
			group_layout.addWidget(stacked_widget)
			if increment_btn := QPushButton():
				increment_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
				increment_btn.setProperty('css_class', 'increment')
				increment_btn.setIcon(Assets.QIcon('style/rightarrow.svg'))
				increment_btn.clicked.connect(self.__evt_increment_clicked)
			group_layout.addWidget(increment_btn)
		layout.addWidget(group_widget)

	def addItem (self,
		widget: QWidget,
		data: object | None = None,
		/,
		margins: bool = True,
		alignment: Qt.Alignment = Qt.AlignHCenter,
	) -> None:
		self.__datas.append(data)
		self.__widgets.append(widget)
		wrapper_widget = QWidget()
		wrapper_layout = QHBoxLayout(wrapper_widget)
		if not margins:
			wrapper_layout.setContentsMargins(0, 0, 0, 0)
		wrapper_layout.addWidget(widget, 1, alignment = alignment)
		self.__stacked_widget.addWidget(wrapper_widget)

	def clear (self) -> None:
		self.__datas = []
		self.__widgets = []
		with QSignalBlocker(self.__stacked_widget):
			while self.__stacked_widget.count():
				to_delete = self.__stacked_widget.widget(0)
				self.__stacked_widget.removeWidget(to_delete)
				to_delete.deleteLater()
		self.changed.emit(None)

	def widget (self, index: int) -> QWidget | None:
		return None if index == -1 else self.__widgets[index]

	def currentWidget (self) -> QWidget | None:
		return self.widget(self.__stacked_widget.currentIndex())

	def __evt_decrement_clicked (self) -> None:
		self.__stacked_widget.setCurrentIndex( (self.__stacked_widget.currentIndex() - 1) % self.__stacked_widget.count() )

	def __evt_increment_clicked (self) -> None:
		self.__stacked_widget.setCurrentIndex( (self.__stacked_widget.currentIndex() + 1) % self.__stacked_widget.count() )

	def __evt_current_changed (self, index: int) -> None:
		self.changed.emit(None if index == -1 else self.__datas[index])

	def set_value (self, value: object) -> None:
		if not len(self.__datas) and not value:
			return
		for i, data in enumerate(self.__datas):
			if data == value:
				self.__stacked_widget.setCurrentIndex(i)
				return
		raise ValueError(f'Could not locate new value: {value}')

	def get_value (self) -> object:
		i = self.__stacked_widget.currentIndex()
		if i == -1:
			return None
		return self.__datas[i]

	val = Property(
		object,
		fget = get_value,
		fset = set_value,
		notify = changed,
		user = True,
	)

