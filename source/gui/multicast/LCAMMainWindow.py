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

import base64
import sys

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtWidgets import *

from ...Assets import *
from ...Config import *
from ...I18n import *
from ...Settings import *
from ...Util import *

from .LCAMSegmentTrackerWidget import *
from ..LCAMainWindow import *
from ..LCAPopupMessage import *
from ...models.LCAProjectFileModel import *

class LCAMMainWindow (LCAMainWindow):
	
	__project: LCAProjectFileModel
	
	__status_lbl: QLabel
	
	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.info(I18n(self).errors.need_slug)
			sys.exit()
		self.__project = LCAProjectFileModel.load(sys.argv[2])
		self.setWindowIcon(Assets.QIcon('icons/multicast.ico'))
		self.setWindowTitle(I18n(self).title)
		if profile := Settings().tools.multicast.profile.get(self.__project.series_id, None):
			self.restoreGeometry(profile.geometry)
			self.restoreState(profile.state)

	def _setup_layout (self) -> None:
		self.setCentralWidget(LCAMSegmentTrackerWidget(self.__project))
		self.__setup_status_bar()

	def __setup_status_bar (self) -> None:
		self.statusBar().setSizeGripEnabled(False)
		self.__status_lbl = QLabel()
		self.statusBar().addPermanentWidget(self.__status_lbl)
		self.__set_status_message('Couldn\'t connect to any OBS instance wow this is super long')
		#self.statusBar().addPermanentWidget(QLabel(''))

	def closeEvent (self, event: QCloseEvent) -> None:
		logger.debug(self.saveGeometry())
		logger.debug(self.saveState())
		with Settings():
			Settings().tools.multicast.profile[self.__project.series_id] = \
				Settings().ToolsModel.ToolsMulticastModel.ToolsMulticastProfileModel(
					geometry = base64.b64encode(bytes(self.saveGeometry())),
					state = base64.b64encode(bytes(self.saveState())),
				)
		event.accept()

	def __set_status_message (self, msg: str) -> None:
		self.__status_lbl.setText(f'{msg} ')

