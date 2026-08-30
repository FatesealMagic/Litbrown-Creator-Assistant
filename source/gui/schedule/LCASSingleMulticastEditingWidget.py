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

from ...Config import *
from ...I18n import *
from ...Settings import *
from ..LCAWidget import *
from ..LCAFilePickerWidget import *
from .LCASDeckURLEdit import *
from ..LCAComboBox import *
from ..LCATableModel import *
from ..LCADateAndTimePickerWidget import *
from ...models.LCAProjectFileModel import *

class LCASSingleMulticastEditingWidget (LCAWidget):
	
	__model: LCATableModel[LCAProjectFileModel]
	__model_row: int
	__series: Settings().SeriesModel
	__entry_number: int
	
	__variant_combo: LCAComboBox

	def __init__ (self,
		model: LCATableModel[LCAProjectFileModel],
		model_row: int,
	*args, **kwargs):
		self.__model = model
		self.__model_row = model_row
		self.__series = Settings().series_from_id(self.__model.data(self.__model.index(
			model_row, self.__model.get_column_index('series_id')
		)))
		self.__entry_number = self.__model.data(self.__model.index( model_row, self.__model.get_column_index('entry_number')))
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		mapper = QDataWidgetMapper(self)
		mapper.setModel(self.__model)
		mapper.setCurrentIndex(self.__model_row)
		if basicinfo_widget := QWidget():
			basicinfo_layout = QHBoxLayout(basicinfo_widget)
			basicinfo_layout.setContentsMargins(0, 0, 0, 0)
			basicinfo_layout.addWidget(QLabel( f'<html><h3>{self.__series.name} {self.__entry_number}</h3></html>' ))
			basicinfo_layout.addStretch()
			if self.__series.variants:
				basicinfo_layout.addWidget(QLabel(I18n(self).variant_lbl))
				if variant_combo := LCAComboBox():
					self.__variant_combo = variant_combo
					for variant in self.__series.variants:
						variant_combo.addItem(variant.name, variant.id)
					variant_combo.currentIndexChanged.connect(self.__evt_variant_combo_index_changed)
					mapper.addMapping(variant_combo, self.__model.get_column_index('variant_id'))
				basicinfo_layout.addWidget(variant_combo)
			basicinfo_layout.addSpacing(basicinfo_layout.spacing())
			basicinfo_layout.addWidget(QLabel(I18n(self).mtgformat_lbl))
			if mtgformat_combo := QComboBox():
				self.__mtgformat_combo = mtgformat_combo
				mtgformat_combo.setEditable(True)
				mtgformat_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
				for fmt in Config().mtg.formats:
					mtgformat_combo.addItem(fmt) if fmt else mtgformat_combo.insertSeparator(mtgformat_combo.count())
				mtgformat_combo.setCurrentText('')
				mapper.addMapping(mtgformat_combo, self.__model.get_column_index('mtg_format'))
			basicinfo_layout.addWidget(mtgformat_combo)
		layout.addWidget(basicinfo_widget)
		if streaminfo_widget := QWidget():
			streaminfo_layout = QHBoxLayout(streaminfo_widget)
			streaminfo_layout.setContentsMargins(0, 0, 0, 0)
			if member_combo := LCAComboBox():
				for member_name, member_id in [
					( I18n(self).recordonly_stream, '~nostream' ),
					( I18n(self).public_stream, '~public' ),
				]:
					member_combo.addItem(member_name, member_id)
				for tier in reversed(Settings().membership_tiers):
					member_combo.addItem(tier.name, tier.id)
				mapper.addMapping(member_combo, self.__model.get_column_index('stream.membertier_id'))
				member_combo.setCurrentIndex(member_combo.findData(self.__series.stream.publish_to_membership_id))
				member_combo.currentDataChanged.connect(self.__evt_member_combo_data_changed)
			streaminfo_layout.addWidget(member_combo)
			if dateandtime_widget := LCADateAndTimePickerWidget():
				self.__dateandtime_widget = dateandtime_widget
				dateandtime_widget.changed.connect(mapper.submit)
				mapper.addMapping(dateandtime_widget, self.__model.get_column_index('stream.start'))
			streaminfo_layout.addWidget(dateandtime_widget)
		layout.addWidget(streaminfo_widget)
		if titlehook_txt := QLineEdit():
			self.__titlehook_txt = titlehook_txt
			titlehook_txt.setPlaceholderText(I18n(self).titlehook_placeholder)
			mapper.addMapping(titlehook_txt, self.__model.get_column_index('stream.title_hook'))
		layout.addWidget(titlehook_txt)
		if deschook_txt := QLineEdit():
			self.__deschook_txt = deschook_txt
			deschook_txt.setPlaceholderText(I18n(self).deschook_placeholder)
			mapper.addMapping(deschook_txt, self.__model.get_column_index('stream.description_hook'))
		layout.addWidget(deschook_txt)
		self.__evt_member_combo_data_changed(member_combo.currentData())
		if url_txt := LCASDeckURLEdit():
			mapper.addMapping(url_txt, self.__model.get_column_index('decklists'))
			url_txt.changed.connect(mapper.submit)
		layout.addWidget(url_txt)
		if self.__series.variants:
			self.__evt_variant_combo_index_changed(variant_combo.currentIndex())
		mapper.submit()

	def __evt_variant_combo_index_changed (self, index: int) -> None:
		logger.debug(index)
		self.__mtgformat_combo.setCurrentText(self.__series.variants[index].mtgformat)

	def __evt_member_combo_data_changed (self, membertier_id: str) -> None:
		for widget in (
			self.__dateandtime_widget,
			self.__titlehook_txt,
			self.__deschook_txt,
		):
			widget.hide() if (not membertier_id or membertier_id == '~nostream') else widget.show()

