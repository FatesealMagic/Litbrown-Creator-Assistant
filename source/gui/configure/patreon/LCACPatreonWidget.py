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

from ..LCACConnectButton import *
from ..LCACConnectionInfoDisplayWidget import *
from ...LCALabel import *
from ...LCAWidget import *
from ....threads.configure.LCACPatreonRefreshTiersTaskThread import *

class LCACPatreonWidget (LCAWidget):
	
	__refresh_tiers_thread: LCACPatreonRefreshTiersTaskThread
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		layout.addWidget(LCALabel(I18n(self).info))
		layout.addWidget(LCACConnectionInfoDisplayWidget('patreon'))
		if connect_btn := LCACConnectButton('patreon'):
			connect_btn.clicked.connect(self.__start_oauth_flow)
		layout.addWidget(connect_btn)
		if refreshtiers_btn := QPushButton(I18n(self).refresh_tiers):
			refreshtiers_btn.setStyleSheet('QPushButton { font-size: 14pt; font-weight: bold; padding: 0.25em; }')
			refreshtiers_btn.clicked.connect(self.__refresh_tiers)
		layout.addWidget(refreshtiers_btn)
		layout.addStretch(1)

	def __start_oauth_flow (self) -> None:
		with Settings():
			Settings().integrations.patreon.reset()
		logger.info(f'Starting Patreon oauth flow at URL {Config().integrations.remote.patreon.oauth_url}')
		webbrowser.open(Config().integrations.remote.patreon.oauth_url)

	def __refresh_tiers (self) -> None:
		self.__refresh_tiers_thread = LCACPatreonRefreshTiersTaskThread()
		self.__refresh_tiers_thread.start()

