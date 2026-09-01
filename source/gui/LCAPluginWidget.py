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

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .LCAWidget import *
from ..common.LCAPluginManager import *

class LCAPluginWidget (QDockWidget):

	_import_path: str
	
	@property
	def import_path (self) -> str:
		return _import_path

	def __init__ (self, *,
		parent: QWidget | None = None,
		import_path: str,
		title: str,
	):
		self._import_path = import_path
		super().__init__(parent)
		self._setup_layout()
		self.setObjectName(f'plugin.{import_path}')
		self.setWindowTitle(title)

	def _setup_layout (self) -> None:
		raise NotImplementedError

	def closeEvent (self, event: QCloseEvent) -> None:
		logger.debug(f'Unloading plugin {self._import_path}')
		LCAPluginManager.unload_plugin(self._import_path)
		self.deleteLater()

