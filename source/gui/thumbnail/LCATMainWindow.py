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

import pathlib

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtWidgets import *

from ...Config import *
from ...I18n import *
from ...Assets import *
from ...Util import *

from .LCATBottomControlsWidget import *
from .LCATSideControlsWidget import *
from ..LCAComboBox import *
from ..LCAMainWindow import *
from ..LCASideTabWidget import *
from ..LCATableModel import *
from ..LCAToggleButtonGroupWidget import *
from ..LCAWebEngineView import *
from ...models.LCAProjectFileModel import *
from ...models.thumbnail.LCATThumbnailModel import *

class LCATMainWindow (LCAMainWindow):
	
	__model: LCATableModel[LCATThumbnailModel]
	__mapper: QDataWidgetMapper
	
	def _initialize_window (self) -> None:
		self.setWindowIcon(Assets.QIcon('icons/thumbnail.ico'))
		self.setWindowTitle(I18n(self).title)
		self.setWindowState(Qt.WindowMaximized)
		self.__thumbnail_model = LCATThumbnailModel()
		self.__model = LCATableModel(LCATThumbnailModel, lambda : [self.__thumbnail_model], self.__thumbnail_model)
		self.__model.insertRows(0, 1)
		self.__thumbnail_model.signals().changed.connect( self.__evt_thumbnail_model_changed )

	def _setup_layout (self) -> None:
		widget = QWidget()
		layout = QHBoxLayout(widget)
		layout.setSpacing(layout.spacing() * 2)
		if main_widget := QWidget():
			main_layout = QVBoxLayout(main_widget)
			main_layout.setContentsMargins(0, 0, 0, 0)
			main_layout.setSpacing(main_layout.spacing() * 2)
			main_layout.addStretch()
			if viewer := LCAWebEngineView():
				self.__viewer = viewer
				viewer.setFixedSize(1280, 720)
				viewer.setUrl(f'http://127.0.0.1:42967/{Settings().tools.thumbnail.render_file}')
				viewer.loadFinished.connect(self.__evt_thumbnail_model_changed)
			main_layout.addWidget(viewer, 0)
			if bottomcontainer_widget := QWidget():
				bottomcontainer_widget.setProperty('css_class', 'accent_bordered')
				bottomcontainer_layout = QVBoxLayout(bottomcontainer_widget)
				bottomcontainer_layout.addWidget(LCATBottomControlsWidget(self.__model, self.__evt_save))
			main_layout.addWidget(bottomcontainer_widget, 0)
			main_layout.addStretch()
		layout.addWidget(main_widget, 0)
		if side_widget := QFrame():
			side_widget.setProperty('css_class', 'accent_bordered')
			side_layout = QVBoxLayout(side_widget)
			side_layout.addWidget(LCATSideControlsWidget(self.__model))
		layout.addWidget(side_widget, 1)
		self.setCentralWidget(widget)
		self.__evt_thumbnail_model_changed()

	def __evt_thumbnail_model_changed (self, _ = None) -> None:
		logger.debug(self.__thumbnail_model.model_dump_json())
		match self.__thumbnail_model.method:
			case 'channel':
				series = None
				variant = None
				project = None
			case 'series':
				series = Settings().series_from_id(
					self.__thumbnail_model.series_id
				).model_dump_json() if self.__thumbnail_model.series_id else None
				variant = None
				project = None
			case 'variant':
				series = Settings().series_from_id(
					self.__thumbnail_model.series_id
				).model_dump_json() if self.__thumbnail_model.series_id else None
				variant = Settings().series_variant_from_id(
					self.__thumbnail_model.series_id,
					self.__thumbnail_model.variant_id,
				).model_dump_json() if self.__thumbnail_model.variant_id else None
				project = None
			case 'multicast':
				raw_project = LCAProjectFileModel.load(self.__thumbnail_model.series_id, self.__thumbnail_model.entry_number)
				series = Settings().series_from_id(
					self.__thumbnail_model.series_id
				).model_dump_json() if self.__thumbnail_model.series_id else None
				variant = Settings().series_variant_from_id(
					self.__thumbnail_model.series_id,
					raw_project.variant_id,
				).model_dump_json() if self.__thumbnail_model.series_id and raw_project and raw_project.variant_id else None
				project = raw_project.model_dump_json() if raw_project else None
		self.__viewer.page().runJavaScript(f'''
			{Settings().tools.thumbnail.render_func}(
				controls = {self.__thumbnail_model.model_dump_json()},
				series = {series or 'null'},
				variant = {variant or 'null'},
				project = {project or 'null'}
			);
		''')

	def __evt_save (self) -> None:
		match self.__thumbnail_model.method:
			case 'channel':
				filename = ''
			case 'series':
				filename = f'{self.__thumbnail_model.series_id}/'
			case 'variant':
				filename = f'{self.__thumbnail_model.series_id}/{self.__thumbnail_model.variant_id}/'
			case 'multicast':
				slug = LCAProjectFileModel.create_slug(self.__thumbnail_model.series_id, self.__thumbnail_model.entry_number)
				filename = f'{slug}/{slug}-'
		fullpath = pathlib.Path(f'{Settings().tools.general.projects_location}/' +
			f'{filename}{I18n(self).filename.thumbnail}-{getattr(I18n(self).filename, self.__thumbnail_model.format)}.png')
		logger.info(f'Saving screenshot to: {fullpath}')
		fullpath.parent.mkdir(parents = True, exist_ok = True)
		self.__viewer.save_screenshot(str(pathlib.Path( fullpath )))

