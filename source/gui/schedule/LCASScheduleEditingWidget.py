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

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ..LCASeparator import *
from ..LCAWidget import *
from ..LCAPopupMessage import *
from .LCASSingleMulticastEditingWidget import *

from ...Assets import *
from ...Settings import *
from ...Util import *
from ...models.LCAProjectFileModel import *

class LCASScheduleEditingWidget (LCAWidget):
	
	__options_add_multicast_btn: QPushButton
	__multicasts_widget: QWidget
	__model: LCATableModel[LCAProjectFileModel]
	
	def __init__ (self, model: LCATableModel[LCAProjectFileModel], *args, **kwargs):
		self.__model = model
		super().__init__()
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		if options_widget := QWidget():
			options_layout = QHBoxLayout(options_widget)
			options_layout.setContentsMargins(0, 0, 0, 0)
			if series_combo := QComboBox():
				self.__series_combo = series_combo
				self.__series_combo.setPlaceholderText(I18n(self).series_hint)
				self.__build_series_combo()
				Settings().signals().changed.connect(self.__build_series_combo)
				self.__series_combo.currentIndexChanged.connect(self.__evt_series_changed)
			options_layout.addWidget(self.__series_combo, 1)
			if options_add_multicast_btn := QPushButton(I18n(self).add_multicast_btn):
				self.__options_add_multicast_btn = options_add_multicast_btn
				self.__options_add_multicast_btn.setIcon(Assets.QIcon('icons/plus.png'))
				self.__options_add_multicast_btn.clicked.connect(self.__evt_add_multicast)
			options_layout.addWidget(self.__options_add_multicast_btn, 1)
			if options_del_multicast_btn := QPushButton(I18n(self).del_multicast_btn):
				self.__options_del_multicast_btn = options_del_multicast_btn
				self.__options_del_multicast_btn.setIcon(Assets.QIcon('icons/minus.png'))
				self.__options_del_multicast_btn.clicked.connect(self.__evt_del_multicast)
			options_layout.addWidget(self.__options_del_multicast_btn, 1)
		layout.addWidget(options_widget)
		if multicasts_scrollarea := QScrollArea():
			multicasts_scrollarea.setWidgetResizable(True)
			multicasts_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
			multicasts_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
			if multicasts_widget := QWidget():
				self.__multicasts_widget = multicasts_widget
				multicasts_layout = QVBoxLayout(multicasts_widget)
				multicasts_layout.addStretch()
			multicasts_scrollarea.setWidget(multicasts_widget)
		layout.addWidget(multicasts_scrollarea, 1)

	def __build_series_combo (self) -> None:
		while self.__series_combo.count():
			self.__series_combo.removeItem(0)
		for series in Settings().series:
			if series.stream.enabled:
				self.__series_combo.addItem(series.name, series.id)

	def __evt_series_changed (self, index: int) -> None:
		self.__options_add_multicast_btn.setEnabled(True)
		self.__options_del_multicast_btn.setEnabled(True)

	def __evt_add_multicast (self) -> None:
		series_id = self.__series_combo.currentData()
		if not series_id:
			LCAPopupMessage.info(I18n(self).err_select_series)
			return
		logger.info(f'Adding multicast with series_id {series_id}')
		self.__model.insertRows(
			self.__model.rowCount(), 1,
			model_args = {
				'series_id': series_id,
				'entry_number': self.__determine_entry_number_for_series(series_id),
				'variant_id': Settings().series_from_id(series_id).variants[0].id \
					if Settings().series_from_id(series_id).variants else '',
			}
		)
		if self.__model.rowCount() > 1:
			self.__multicasts_widget.layout().insertWidget(self.__multicasts_widget.layout().count() - 1, LCASeparator.horizontal())
		self.__multicasts_widget.layout().insertWidget(
			self.__multicasts_widget.layout().count() - 1,
			LCASSingleMulticastEditingWidget( self.__model, self.__model.rowCount() - 1 )
		)

	def __determine_entry_number_for_series (self, series_id: str) -> int:
		entry_number = 1
		for existing_series_id, existing_entry_number in LCAProjectFileModel.find_all_ids():
			if existing_series_id == series_id and existing_entry_number >= entry_number:
				entry_number = 1 + existing_entry_number
		for i in range(self.__model.rowCount()):
			if self.__model.data(self.__model.createIndex(i, self.__model.get_column_index('series_id'))) == series_id:
				entry_number += 1
		return entry_number

	def __evt_del_multicast (self) -> None:
		if not self.__model.rowCount():
			return
		# Delete multicast info wiget, plus separator if there's more than one multicast before deletion
		for _ in range ( 1 if self.__model.rowCount() == 1 else 2 ):
			layoutitem = self.__multicasts_widget.layout().takeAt(self.__multicasts_widget.layout().count() - 2)
			if layoutitem and layoutitem.widget():
				layoutitem.widget().deleteLater()
		self.__model.removeRows(self.__model.rowCount() - 1, 1)

	def get_data (self) -> list[dict]:
		return self.__multicasts_widget.get_data()