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

import sys

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Assets import Assets
from ...Config import Config
from ...I18n import I18n
from ...Settings import Settings
from ...Util import Util

from ..LCAMainWindow import LCAMainWindow
from ..LCAPopupMessage import LCAPopupMessage
from ..LCASideTabWidget import LCASideTabWidget
from ...models.LCAProjectFileModel import LCAProjectFileModel

class LCARMainWindow (LCAMainWindow):

	__TAB_NAMES = ('prepare', 'edit', 'render')

	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.error(I18n(self).errors.need_slug)
			sys.exit()
		self.setWindowIcon(Assets.QIcon('icons/render.ico'))
		self.__project = LCAProjectFileModel.from_slug(sys.argv[2])
		self.setWindowTitle(f'{I18n(self).title} | {Settings().series_from_id(self.__project.series_id).name} #{self.__project.entry_number}')
		self.resize(600, 400)

	def _setup_layout (self) -> None:
		central_widget = LCASideTabWidget(orientation = Qt.Orientation.Horizontal, enabled = False, headers = False)
		for tab in self.__TAB_NAMES:
			central_widget.addWidget(
				getattr(self, f'__build_{tab}_tab')(),
				I18n(self).tabs[tab].name,
			)
		central_widget.setCurrentIndex(0)
		self.setCentralWidget(central_widget)

	def __build_prepare_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.addStretch(1)
		if proceed_btn := QPushButton(' ' + I18n(self).tabs.prepare.proceed):
			proceed_btn.setProperty('css_class', 'big')
			proceed_btn.setIcon(Assets.QIcon('icons/advance.png'))
		layout.addWidget(proceed_btn)
		return widget

	def __build_edit_tab (self) -> QWidget:
		return QLabel('edit')

	def __build_render_tab (self) -> QWidget:
		return QLabel('render')

