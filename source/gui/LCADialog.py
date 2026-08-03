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

from ..I18n import *

from .LCAMainWindow import *

class LCADialog (QDialog):

	def __init__ (self,
		parent: QWidget | None = None,
		title: str | None = None,
		modality: Qt.WindowModality = Qt.WindowModality.ApplicationModal,
	*args, **kwargs):
		super().__init__(parent or self.__determine_parent_window())
		self.setWindowTitle(title or I18n(self).dialog_title)
		self.setWindowModality(modality)
		self._setup_layout()

	def __determine_parent_window (self) -> LCAMainWindow | None:
		for widget in QApplication.topLevelWidgets():
			if isinstance(widget, LCAMainWindow):
				return widget
		return None

	def _setup_layout (self) -> None:
		raise NotImplementedError

	def _build_hsep (self) -> QFrame:
		return self._build_sep(QFrame.HLine)

	def _build_vsep (self) -> QFrame:
		return self._build_sep(QFrame.VLine)

	def _build_sep (self, shape: QFrame.Shape) -> QFrame:
		sep = QFrame()
		sep.setFrameShape(shape)
		sep.setFrameShadow(QFrame.Sunken)
		return sep

