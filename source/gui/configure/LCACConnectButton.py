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

from ...I18n import *
from ...Assets import *

from ..LCAWidget import *

class LCACConnectButton (QPushButton):
	
	def __init__ (self, connection: str, *args, **kwargs):
		super().__init__(f'  {I18n(self).label}', *args, **kwargs)
		logger.debug('making a button')
		self.setStyleSheet('QPushButton { font-size: 16pt; font-weight: bold; padding: 0.5em; }')
		self.setIcon(Assets.QIcon(f'external/icons/{connection}.png'))
		self.setIconSize(QSize(32, 32))

