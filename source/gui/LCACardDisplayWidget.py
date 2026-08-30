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
from PySide6.QtNetwork import *
from PySide6.QtWidgets import *

from ..Assets import *

from .LCAWidget import *
from ..models.LCAScryfallCardModel import *

class LCACardDisplayWidget (LCAWidget):
	
	card: LCAScryfallCardModel

	def __init__ (self, card: LCAScryfallCardModel, face: int = 0, *args, **kwargs):
		self.card = card
		super().__init__(*args, **kwargs)
	
	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		self.__label = QLabel()
		self.__label.setScaledContents(True)
		self.__label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.__label)
		dlmanager = QNetworkAccessManager(self)
		dlmanager.finished.connect( self.__evt_download_finished )
		dlmanager.get(QNetworkRequest(
			self.card.card_faces[self.card.lca_selected_face].image_uris['png']
				if not self.card.image_uris else self.card.image_uris['png']
		))

	def __evt_download_finished (self, reply: QNetworkReply) -> None:
		if reply.error() != QNetworkReply.NoError:
			logger.warning(f'Error getting card image: {self.card.image_uris['png']}')
			return
		pixmap = QPixmap()
		pixmap.loadFromData(reply.readAll())
		self.__label.setPixmap(pixmap)

