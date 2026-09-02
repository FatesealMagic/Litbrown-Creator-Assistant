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

from ..Config import *
from ..I18n import *
from ..Assets import *

from .LCALabel import *
from .LCAWidget import *

class LCAConnectionLabelWidget (LCAWidget):

	def __init__ (self,
		connection_name: str,
		*args, **kwargs
	):
		self.__connection_name = connection_name
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addStretch()
		if icon_lbl := LCALabel():
			icon_lbl.setPixmap(Assets.QIcon(f'external/icons/{self.__connection_name}.png').pixmap(QSize(32, 32)))
		layout.addWidget(icon_lbl, alignment = Qt.AlignmentFlag.AlignVCenter)
		layout.addSpacing(layout.spacing())
		if text_lbl := LCALabel(I18n(self)[self.__connection_name]):
			font = text_lbl.font()
			font.setPointSize(font.pointSize() * 2)
			font.setWeight(QFont.Weight.Bold)
			text_lbl.setFont(font)
		layout.addWidget(text_lbl, alignment = Qt.AlignmentFlag.AlignVCenter)
		layout.addStretch()

