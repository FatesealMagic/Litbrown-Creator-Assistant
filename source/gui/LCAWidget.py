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

from PySide6.QtWidgets import *

class LCAWidget (QWidget):

	def __init__ (self, parent: QWidget | None = None):
		super().__init__(parent)
		self._setup_layout()

	def _setup_layout (self) -> None:
		raise NotImplementedError

	def _build_hsep (self) -> QFrame:
		return self._build_sep(QFrame.HLine)

	def _build_vsep (self) -> QFrame:
		return self._build_sep(QFrame.VLine)

	def _build_sep (self, shape: QFrame.Shape) -> QFrame:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if shape == QFrame.VLine:
			layout.setContentsMargins(layout.spacing(), 0, layout.spacing(), 0)
		else:
			layout.setContentsMargins(0, layout.spacing(), 0, layout.spacing())
		sep = QFrame()
		sep.setFrameShape(shape)
		sep.setFrameShadow(QFrame.Sunken)
		layout.addWidget(sep)
		return widget

