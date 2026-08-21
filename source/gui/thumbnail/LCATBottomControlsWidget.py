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

import typing

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Config import *
from ...I18n import *
from ...Assets import *
from ...Util import *

from ..LCAComboBox import *
from ..LCATableModel import *
from ..LCAToggleButtonGroupWidget import *
from ..LCASeparator import *
from ...common.LCAProjectWatcher import *
from ...models.LCAProjectFileModel import *
from ...models.thumbnail.LCATThumbnailModel import *

class LCATBottomControlsWidget (LCAWidget):
	
	__BUTTONS_STYLESHEET = 'QPushButton { font-size: 13pt; }'

	__model: LCATableModel[LCATThumbnailModel]
	__save_callback: typing.Callable[[], []]
	__mapper: QDataWidgetMapper
	
	def __init__ (self,
		model: LCATableModel[LCATThumbnailModel],
		save_callback: typing.Callable[[], []],
	*args, **kwargs):
		self.__model = model
		self.__save_callback = save_callback
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		self.__mapper = QDataWidgetMapper(self)
		self.__mapper.setModel(self.__model)
		layout = QHBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		if method_btns := LCAToggleButtonGroupWidget(rows = 2):
			method_btns.setStyleSheet(self.__BUTTONS_STYLESHEET)
			method_btns.addButton(I18n(self).methods.channel,   'channel')
			method_btns.addButton(I18n(self).methods.series,    'series')
			method_btns.addButton(I18n(self).methods.variant,   'variant')
			method_btns.addButton(I18n(self).methods.multicast, 'multicast')
			method_btns.set_value(self.__model.data((0, 'method')))
			self.__mapper.addMapping(method_btns, self.__model.get_column_index('method'))
			method_btns.changed.connect(lambda _ : self.__mapper.submit())
			method_btns.changed.connect(self.__refresh_bottom_controls)
		layout.addWidget(method_btns)
		layout.addWidget(LCASeparator.vertical())
		if format_btns := LCAToggleButtonGroupWidget(rows = 2):
			format_btns.setStyleSheet(self.__BUTTONS_STYLESHEET)
			format_btns.addButton(I18n(self).formats.stream, 'stream')
			format_btns.addButton(I18n(self).formats.video,  'video')
			self.__mapper.addMapping(format_btns, self.__model.get_column_index('format'))
			format_btns.changed.connect(lambda _ : self.__mapper.submit())
			format_btns.changed.connect(self.__refresh_bottom_controls)
		layout.addWidget(format_btns)
		if multicast_cbo := LCAComboBox():
			self.__multicast_cbo = multicast_cbo
			multicast_cbo.setPlaceholderText(I18n(self).placeholders.multicast)
			multicast_cbo.currentDataChanged.connect(self.__update_series_entry_values)
			multicast_cbo.currentDataChanged.connect(self.__update_save_button)
			multicast_cbo.currentDataChanged.connect(self.__mapper.submit)
		layout.addWidget(multicast_cbo)
		if series_cbo := LCAComboBox():
			self.__series_cbo = series_cbo
			self.__mapper.addMapping(series_cbo, self.__model.get_column_index('series_id'))
			series_cbo.setPlaceholderText(I18n(self).placeholders.series)
			series_cbo.currentDataChanged.connect(self.__refresh_variant_cbo)
			series_cbo.currentDataChanged.connect(self.__update_multicast_cbo_value)
			series_cbo.currentDataChanged.connect(self.__update_save_button)
			series_cbo.currentDataChanged.connect(self.__mapper.submit)
		layout.addWidget(series_cbo)
		if variant_cbo := LCAComboBox():
			self.__variant_cbo = variant_cbo
			self.__mapper.addMapping(variant_cbo, self.__model.get_column_index('variant_id'))
			variant_cbo.setPlaceholderText(I18n(self).placeholders.variant)
			variant_cbo.currentDataChanged.connect(self.__update_save_button)
			variant_cbo.currentDataChanged.connect(self.__mapper.submit)
		layout.addWidget(variant_cbo)
		if entry_spin := QSpinBox():
			self.__entry_spin = entry_spin
			self.__mapper.addMapping(entry_spin, self.__model.get_column_index('entry_number'))
			entry_spin.setMinimum(1)
			entry_spin.setMaximum(9999)
			entry_spin.valueChanged.connect(self.__update_multicast_cbo_value)
			entry_spin.valueChanged.connect(lambda _ : self.__mapper.submit())
		layout.addWidget(entry_spin)
		layout.addStretch()
		if save_btn := QPushButton(I18n(self).save):
			self.__save_btn = save_btn
			save_btn.setProperty('css_class', 'big')
			save_btn.setIcon(Assets.QIcon('icons/save.png'))
			save_btn.setIconSize(QSize(32, 32))
			save_btn.clicked.connect(self.__save_callback)
		layout.addWidget(save_btn)
		layout.addSpacing(layout.spacing())
		self.__mapper.setCurrentIndex(0)
		self.__project_watcher = LCAProjectWatcher()
		self.__project_watcher.directoryChanged.connect(self.__refresh_bottom_controls)
		self.__project_watcher.fileChanged.connect(self.__refresh_bottom_controls)
		logger.debug(self.__project_watcher.files())
		logger.debug(self.__project_watcher.directories())
		Settings().signals().changed.connect(self.__refresh_bottom_controls)
		self.__refresh_bottom_controls()
		with QSignalBlocker(self.__multicast_cbo):
			self.__multicast_cbo.setCurrentIndex(-1)
		with QSignalBlocker(self.__series_cbo):
			self.__series_cbo.setCurrentIndex(-1)
		self.__update_save_button()

	def __refresh_bottom_controls (self, _ = None) -> None:
		self.__hideshow_bottom_controls()
		self.__refresh_multicast_cbo()
		self.__refresh_series_cbo()
		self.__refresh_variant_cbo()
		self.__refresh_entry_spin()
		self.__update_save_button()
		self.__mapper.submit()

	def __hideshow_bottom_controls (self, _ = None) -> None:
		for widget, methods in [
			(self.__multicast_cbo, ['multicast']),
			(self.__series_cbo,    ['series', 'variant', 'multicast']),
			(self.__variant_cbo,   ['variant']),
			(self.__entry_spin,    ['multicast']),
		]:
			widget.show() if self.__model.data((0, 'method')) in methods else widget.hide()

	def __refresh_multicast_cbo (self, _ = None) -> None:
		previous_series_id = self.__series_cbo.currentData()
		previous_entry_number = self.__entry_spin.value()
		with QSignalBlocker(self.__multicast_cbo):
			self.__multicast_cbo.clear()
			for series_id, entry_number in LCAProjectFileModel.get_existing_slugs_split():
				try:
					series = Settings().series_from_id(series_id)
					self.__multicast_cbo.addItem(
						f'{series.name} #{entry_number}',
						LCAProjectFileModel.slug(series_id, entry_number),
					)
				except ValueError:
					continue
			if previous_series_id:
				self.__multicast_cbo.setData(LCAProjectFileModel.slug(previous_series_id, previous_entry_number))

	def __refresh_series_cbo (self, _ = None) -> None:
		old_series_id = self.__series_cbo.currentData()
		with QSignalBlocker(self.__series_cbo):
			self.__series_cbo.clear()
			for series in Settings().series:
				self.__series_cbo.addItem(series.name, series.id)
			self.__series_cbo.setData(old_series_id)

	def __refresh_variant_cbo (self, _ = None) -> None:
		old_variant_id = self.__variant_cbo.currentData()
		with QSignalBlocker(self.__variant_cbo):
			self.__variant_cbo.clear()
			try:
				series = Settings().series_from_id(self.__series_cbo.currentData())
				for variant in series.variants:
					self.__variant_cbo.addItem(variant.name, variant.id)
			except ValueError:
				pass
			self.__variant_cbo.setData(old_variant_id)

	def __refresh_entry_spin (self, _ = None) -> None:
		pass

	def __update_save_button (self, _ = None) -> None:
		enabled = False
		match self.__model.data((0, 'method')):
			case 'channel':
				enabled = True
			case 'series':
				enabled = (self.__series_cbo.currentIndex() != -1)
			case 'variant':
				enabled = (self.__series_cbo.currentIndex() != -1 and self.__variant_cbo.currentIndex() != -1)
			case 'multicast':
				enabled = (self.__series_cbo.currentIndex() != -1)
		self.__save_btn.setEnabled(enabled)

	def __update_series_entry_values (self, _ = None) -> None:
		series_id, entry_number = LCAProjectFileModel.split_slug(self.__multicast_cbo.currentData())
		with QSignalBlocker(self.__series_cbo):
			self.__series_cbo.setData(series_id)
		with QSignalBlocker(self.__entry_spin):
			self.__entry_spin.setValue(entry_number)

	def __update_multicast_cbo_value (self, _ = None) -> None:
		with QSignalBlocker(self.__multicast_cbo):
			self.__multicast_cbo.setData(LCAProjectFileModel.slug(self.__series_cbo.currentData(), self.__entry_spin.value()))

