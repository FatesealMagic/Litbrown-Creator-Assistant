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

import re

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..Config import *
from ..I18n import *
from ..Assets import *
from ..Settings import *
from ..Util import *

from .LCATabbedDataViewPanelWidget import *
from .LCATableModel import *
from .LCAWidget import *
from .LCAPopupMessage import *

class LCATabbedDataViewWidget (LCAWidget):

	__name_edit: QLineEdit
	__tab_widget: QTabWidget
	
	def __init__ (self,
		model: LCATableModel,
		widget_class: LCATabbedDataViewPanelWidget,
		datatype_name: str,
		name_column_id: str = 'name',
		id_column_id: str = 'id',
		margin: int | None = None,
		*args, **kwargs
	):
		self.model = model
		self.model.dataChanged.connect(self.__update_tab_names)
		self.__widget_class = widget_class
		self.__datatype_name = datatype_name
		self.__name_column_id = name_column_id
		self.__id_column_id = id_column_id
		self.__margin = margin
		super().__init__(*args, **kwargs)
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		if self.__margin is not None:
			layout.setContentsMargins(self.__margin, self.__margin, self.__margin, self.__margin)
		if mgmt_widget := QWidget():
			mgmt_layout = QHBoxLayout(mgmt_widget)
			mgmt_layout.setContentsMargins(0, 0, 0, 0)
			if name_edit := QLineEdit():
				self.__name_edit = name_edit
				name_edit.setPlaceholderText(I18n(self).name_hint)
				name_edit.returnPressed.connect(self.__new_tab)
			mgmt_layout.addWidget(name_edit, 2)
			if add_btn := QPushButton(Assets.QIcon('icons/plus.png'), f' {I18n(self).add_btn} {self.__datatype_name}'):
				add_btn.clicked.connect(self.__new_tab)
			mgmt_layout.addWidget(add_btn, 2)
			if del_btn := QPushButton(Assets.QIcon('icons/minus.png'), f' {I18n(self).del_btn}'):
				del_btn.clicked.connect(self.__del_tab)
			mgmt_layout.addWidget(del_btn, 1)
		layout.addWidget(mgmt_widget)
		if tab_widget := QTabWidget():
			self.__tab_widget = tab_widget
			tab_widget.setMovable(True)
			tab_widget.tabBar().tabMoved.connect(self.__evt_tab_moved)
			for i, entry in enumerate(self.model.get_data_reference()):
				self.__add_tab(i)
		layout.addWidget(tab_widget, 1)

	def __new_tab (self, _ = None) -> None:
		new_name = self.__name_edit.text()
		if not new_name:
			LCAPopupMessage.info(I18n(self).need_nonempty_name)
			return
		new_id = self.__name_to_id(new_name)
		logger.debug(new_id)
		for entry in self.model.get_data_reference():
			if entry.id == new_id:
				LCAPopupMessage.info(I18n(self).need_different_name)
				return
		self.__name_edit.setText('')
		new_row_index = self.model.rowCount()
		self.model.insertRows( new_row_index, 1, model_args = {'id': new_id, 'name': new_name} )
		logger.debug(self.model.get_data_reference())
		self.__add_tab(new_row_index)
		self.__tab_widget.setCurrentIndex(new_row_index)

	def __add_tab (self, index: int) -> None:
		self.__tab_widget.addTab(
			self.__widget_class(self.model, index),
			self.__get_tabname_of_index(index)
		)

	def __del_tab (self) -> None:
		index_to_delete = self.__tab_widget.currentIndex()
		if index_to_delete == -1:
			return
		if LCAPopupMessage.warning(
			I18n(self).warning_delete,
			QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
		) == QMessageBox.StandardButton.Cancel:
			return
		widget_to_delete = self.__tab_widget.widget(index_to_delete)
		widget_to_delete.blockSignals(True)
		self.__tab_widget.removeTab(index_to_delete)
		widget_to_delete.deleteLater()
		for i in range(self.__tab_widget.count()):
			self.__tab_widget.widget(i).set_model_row(i)
		self.model.removeRows( index_to_delete, 1 )

	def __get_tabname_of_index (self, index: int) -> str:
		return self.model.data(self.model.index(
			index, self.model.get_column_index(self.__name_column_id)
		)).replace('&', '&&')

	def __update_tab_names (self, topleft: QModelIndex, bottomright: QModelIndex, roles: list[int] = []):
		for i in range(self.model.rowCount()):
			self.__tab_widget.setTabText(i, self.__get_tabname_of_index(i))

	def __name_to_id (self, name: str) -> str:
		return re.sub(r'[\x00-\x1F\x7F<>:"/\\|?*. -]', '', name).lower()

	def __evt_tab_moved (self, from_index: int, to_index: int) -> None:
		self.model.moveRow(from_index, to_index)

