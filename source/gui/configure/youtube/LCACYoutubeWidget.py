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

import webbrowser

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtNetwork import *
from PySide6.QtWidgets import *

from ....Config import *
from ....I18n import *
from ....Settings import *

from ...LCAWidget import *
from ..LCACConnectButton import *
from ..LCACConnectionInfoDisplayWidget import *

class LCACYoutubeWidget (LCAWidget):
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		if info_lbl := QLabel(I18n(self).info):
			info_lbl.setWordWrap(True)
		layout.addWidget(info_lbl)
		layout.addWidget(LCACConnectionInfoDisplayWidget('youtube'))
		if connect_btn := LCACConnectButton('youtube'):
			connect_btn.clicked.connect(self.__start_oauth_flow)
		layout.addWidget(connect_btn)
		layout.addStretch(1)

	def __start_oauth_flow (self) -> None:
		with Settings():
			Settings().integrations.youtube.reset()
		logger.info(f'Starting Youtube oauth flow at URL {Config().integrations.remote.youtube.oauth_url}')
		webbrowser.open(Config().integrations.remote.youtube.oauth_url)

