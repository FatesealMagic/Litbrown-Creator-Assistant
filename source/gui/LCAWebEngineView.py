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
from PySide6.QtWebEngineWidgets import *

from ..common.LCAFileOverwriter import *

class LCAWebEngineView (QWebEngineView):

	def save_screenshot (self, filename: str) -> None:
		bytearray = QByteArray()
		buffer = QBuffer(bytearray)
		buffer.open(QIODevice.OpenModeFlag.WriteOnly)
		self.grab().save(buffer, 'PNG')
		buffer.close()
		with LCAFileOverwriter(filename, binary = True) as f:
			f.write(bytes(bytearray))

		
		
		
		
		#pixmap = self.grab()
		#pixmap.save(filename)
		'''
		image = QImage(self.size(), QImage.Format_ARGB32)
		painter = QPainter(image)
		self.render(painter, QPoint())
		painter.end()
		image.save(filename)#'''

