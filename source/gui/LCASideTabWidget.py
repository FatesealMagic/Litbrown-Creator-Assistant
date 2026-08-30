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

from loguru import *

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ..I18n import *
from ..Assets import *
from ..Util import *

from .LCAWidget import *

class LCASideTabWidget (LCAWidget):
	
	__HORIZONTAL_LIST_STYLESHEET = '''
		QListView {
			border-top: 0;
			border-right: 0;
			border-bottom: 0;
			outline: 0;
		} QListWidget::item {
			border-left: 0;
			border-bottom: 0;
			padding: 0.5em 1.5em 0.5em 1em;
		}
		'''
	__VERTICAL_LIST_STYLESHEET = '''
		QListView {
			border-right: 0;
			border-bottom: 0;
			border-left: 0;
		} QListWidget::item {
			border-top: 0;
			border-right: 0;
			padding: 0.5em 0.5em 0.5em 0.5em;
		}
		'''
	__TITLE_STYLESHEET = 'font-weight: bold; font-size: 18pt;'
		
	__list_widget: QListWidget
	__orientation: Qt.Orientation
	__separator_widget: QFrame
	__stacked_widget: QStackedWidget
	
	def __init__ (self,
		orientation: Qt.Orientation = Qt.Orientation.Vertical,
		headers: bool = True,
		enabled: bool = True,
		margin: int | None = None,
		*args, **kwargs
	):
		self.__orientation = orientation
		self.__should_add_headers = headers
		self.__margin = margin
		super().__init__(*args, **kwargs)
		self.setProperty('orientation', orientation)
		self.__list_widget.setEnabled(enabled)

	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self) if self.__orientation == Qt.Orientation.Vertical else QVBoxLayout(self)
		layout.setSpacing(0)
		if self.__margin is not None:
			layout.setContentsMargins(self.__margin, self.__margin, self.__margin, self.__margin)
		layout.addWidget(self.__setup_list_widget(), 0)
		layout.addWidget(self.__setup_stacked_widget(), 1)

	def __setup_list_widget (self) -> QListWidget:
		self.__list_widget = QListWidget()
		if self.__orientation == Qt.Orientation.Vertical:
			self.__list_widget.setStyleSheet(self.__VERTICAL_LIST_STYLESHEET)
		else:
			self.__list_widget.setStyleSheet(self.__HORIZONTAL_LIST_STYLESHEET)
			self.__list_widget.setFlow(QListWidget.Flow.LeftToRight)
			self.__list_widget.setWrapping(False)
			self.__list_widget.setResizeMode(QListView.Adjust)
		self.__list_widget.setIconSize(QSize(24,24))
		self.__list_widget.currentRowChanged.connect(self.setCurrentIndex)
		return self.__list_widget

	def __setup_stacked_widget (self) -> QStackedWidget:
		self.__stacked_widget = QStackedWidget()
		return self.__stacked_widget

	def addWidget (self, widget: QWidget, title: str, icon: str | None = None) -> None:
		self.__add_list_widget(title, icon)
		self.__add_stacked_widget(widget, title, icon)

	def __add_list_widget (self, title: str, icon: str | None = None) -> None:
		item = QListWidgetItem(' ' + title)
		#widget = QLabel(' ' + title)
		if icon:
			qicon = Assets.QIcon(icon)
			qicon.addPixmap(qicon.pixmap(QSize(24,24)), QIcon.Selected)
			item.setIcon(qicon)
		self.__list_widget.addItem(item)
		#self.__list_widget.setItemWidget(item, widget)
		if self.__orientation == Qt.Orientation.Vertical:
			self.__list_widget.setFixedWidth(self.__list_widget.sizeHintForColumn(0) + 2 * self.__list_widget.frameWidth() + 20)
		else:
			self.__list_widget.setFixedHeight(self.__list_widget.sizeHintForRow(0) + 2 * self.__list_widget.frameWidth())

	def __add_stacked_widget (self, widget: QWidget, title: str, icon: str | None = None) -> None:
		if self.__should_add_headers:
			base_widget = QWidget()
			base_layout = QVBoxLayout(base_widget)
			base_layout.addSpacing(base_layout.spacing())
			title_widget = QWidget()
			title_layout = QHBoxLayout(title_widget)
			title_layout.setContentsMargins(0, 0, 0, 0)
			title_layout.addStretch(1)
			if icon:
				title_ico = QLabel()
				title_ico.setPixmap(Assets.QIcon(icon).pixmap(QSize(48,48)))
				title_layout.addWidget(title_ico)
				title_layout.addSpacing(title_layout.spacing())
			title_label = QLabel(title)
			title_label.setStyleSheet(self.__TITLE_STYLESHEET)
			title_layout.addWidget(title_label)
			title_layout.addStretch(1)
			base_layout.addWidget(title_widget, 0)
			base_layout.addSpacing(base_layout.spacing())
			if widget.layout():
				widget.layout().setContentsMargins(0, 0, 0, 0)
			base_layout.addWidget(widget, 1)
			self.__stacked_widget.addWidget(base_widget)
		else:
			self.__stacked_widget.addWidget(widget)

	def setCurrentIndex (self, index: int) -> None:
		self.__list_widget.setCurrentRow(index)
		#for i in range(self.__list_widget.count()):
		#	self.__list_widget.itemWidget(self.__list_widget.item(i)).setProperty('selected', '1' if i == index else '0')
		self.setProperty('css_class', '' if index else 'first_selected')
		self.__stacked_widget.setCurrentIndex(index)

