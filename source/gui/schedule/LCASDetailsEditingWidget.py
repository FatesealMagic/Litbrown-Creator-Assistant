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

from ...Assets import *
from ...Config import *
from ...I18n import *
from ...Util import *

from ..LCACarouselWidget import *
from ..LCALabel import *
from ..LCATableModel import *
from ..LCAWidget import *
from ...common.LCAProjectWatcher import *
from ...models.LCAProjectFileModel import *

class LCASDetailsEditingWidget (LCAWidget):

	__thumbnail_source_lbls: list[LCALabel] = []
	__thumbnail_display_lbls: list[LCALabel] = []
	__model: LCATableModel[LCAProjectFileModel]
	__carousel_widget: LCACarouselWidget

	def __init__ (self, model: LCATableModel[LCAProjectFileModel], *args, **kwargs):
		self.__model = model
		self.__watcher = LCAProjectWatcher()
		self.__watcher.fileChanged.connect(self.__refresh_thumbnail_lbls)
		self.__watcher.directoryChanged.connect(self.__refresh_thumbnail_lbls)
		super().__init__(*args, **kwargs)
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		if carousel_widget := LCACarouselWidget():
			self.__carousel_widget = carousel_widget
		layout.addWidget(carousel_widget)

	def refresh (self) -> None:
		self.__thumbnail_source_lbls = []
		self.__thumbnail_display_lbls = []
		self.__carousel_widget.clear()
		for i, project in enumerate(self.__model.get_data_reference()):
			mapper = QDataWidgetMapper(self)
			mapper.setModel(self.__model)
			if widget := QWidget():
				layout = QVBoxLayout(widget)
				layout.setContentsMargins(0, 0, 0, 0)
				if source_widget := QWidget():
					source_layout = QHBoxLayout(source_widget)
					source_layout.setContentsMargins(0, 0, 0, 0)
					source_layout.addWidget(LCALabel(
						f'<html><h3>{Settings().series_from_id(project.series_id).name} {project.entry_number}</h3></html>'
					), alignment=Qt.AlignmentFlag.AlignVCenter)
					if thumbnail_launch_btn := QPushButton(' ' + I18n(self).thumbnail.launch):
						thumbnail_launch_btn.setStyleSheet('font-size: 13pt; font-weight: bold;')
						thumbnail_launch_btn.setIcon(Assets.QIcon('icons/thumbnail.ico'))
						thumbnail_launch_btn.clicked.connect(lambda : Util.launch_new_instance('thumbnail'))
					source_layout.addWidget(thumbnail_launch_btn)
					if thumbnail_source_lbl := LCALabel(I18n(self).thumbnail.source.none):
						self.__thumbnail_source_lbls.append(thumbnail_source_lbl)
						thumbnail_source_lbl.setAlignment(Qt.AlignRight)
					source_layout.addWidget(thumbnail_source_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
				layout.addWidget(source_widget)
				if thumbnail_display_lbl := LCALabel():
					self.__thumbnail_display_lbls.append(thumbnail_display_lbl)
					thumbnail_display_lbl.setFixedSize(QSize(640, 360))
					thumbnail_display_lbl.setScaledContents(True)
					thumbnail_display_lbl.setStyleSheet('background: black;')
				layout.addWidget(thumbnail_display_lbl)
				if title_input := QLineEdit():
					mapper.addMapping(title_input, self.__model.get_column_index('stream.full_title'))
				layout.addWidget(title_input)
				if desc_input := QPlainTextEdit():
					mapper.addMapping(desc_input, self.__model.get_column_index('stream.full_description'))
				layout.addWidget(desc_input)
			mapper.setCurrentIndex(i)
			self.__carousel_widget.addItem(widget)
		self.__refresh_thumbnail_lbls()

	def __refresh_thumbnail_lbls (self) -> None:
		for i, project in enumerate(self.__model.get_data_reference()):
			path, path_type = project.update_thumbnail_path('stream')
			logger.debug(path)
			logger.debug(path_type)
			if path:
				with open(path, 'rb') as f:
					logger.debug(len(f.read()))
			if path_type:
				pixmap = QPixmap(path)
				self.__thumbnail_display_lbls[i].setPixmap(pixmap)
				self.__thumbnail_source_lbls[i].setText(getattr(I18n(self).thumbnail.source, path_type))
			else:
				self.__thumbnail_display_lbls[i].clear()
				self.__thumbnail_source_lbls[i].setText(I18n(self).thumbnail.source.none)
				
