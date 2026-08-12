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

from PySide6.QtWidgets import *

class LCASeparator (QWidget):

	__shape: QFrame.Shape

	def __init__ (self, shape: QFrame.Shape):
		self.__shape = shape

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setContentsMargins(
			layout.spacing() if self.__shape == QFrame.VLine else 0,
			layout.spacing() if self.__shape == QFrame.HLine else 0,
			layout.spacing() if self.__shape == QFrame.VLine else 0,
			layout.spacing() if self.__shape == QFrame.HLine else 0,
		)
		if sep := QFrame():
			sep.setFrameShape(self.__shape)
			sep.setFrameShadow(QFrame.Sunken)
		layout.addWidget(sep)

	@classmethod
	def horizontal (cls) -> typing.Self:
		return cls(QFrame.HLine)

	@classmethod
	def vertical (cls) -> typing.Self:
		return cls(QFrame.VLine)

