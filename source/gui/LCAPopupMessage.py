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
from ..Assets import *

class LCAPopupMessage (QMessageBox):

	def __init__ (self,
		/, *,
		icon: QMessageBox.Icon,
		title_key: str,
		text: str,
		buttons: QMessageBox.StandardButton,
	):
		super().__init__(icon, I18n(self)[title_key], text.strip(), buttons)
		self.setFont(QApplication.font())
		self.setWindowIcon(Assets.QIcon('icons/assistant.ico'))

	@classmethod
	def info (cls,
		text: str,
		buttons = QMessageBox.StandardButton.NoButton,
	) -> QMessageBox.StandardButton:
		return cls(
			icon = QMessageBox.Icon.Information,
			title_key = 'info_title',
			text = text,
			buttons = buttons,
		).exec()

	@classmethod
	def warning (cls,
		text: str,
		buttons = QMessageBox.StandardButton.NoButton,
	) -> QMessageBox.StandardButton:
		return cls(
			icon = QMessageBox.Icon.Warning,
			title_key = 'warning_title',
			text = text,
			buttons = buttons,
		).exec()

	@classmethod
	def error (cls,
		text: str,
		buttons = QMessageBox.StandardButton.NoButton,
	) -> QMessageBox.StandardButton:
		return cls(
			icon = QMessageBox.Icon.Critical,
			title_key = 'error_title',
			text = text,
			buttons = buttons,
		).exec()

	@classmethod
	def noauth (cls) -> bool:
		return cls.show_error(I18n(cls).noauth_text)

