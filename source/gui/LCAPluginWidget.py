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
import pydantic

from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .LCAWidget import *
from ..common.LCAPluginManager import LCAPluginManager
from ..common.LCAProjectState import LCAProjectState

class LCAPluginWidget (QDockWidget):

	def _initial_project_state_data (self) -> pydantic.BaseModel | None:
		raise NotImplementedError

	def _setup_layout (self) -> None:
		raise NotImplementedError

	_import_path: str
	
	@property
	def import_path (self) -> str:
		return self._import_path

	def __init__ (self, *,
		parent: QWidget | None = None,
		import_path: str,
		title: str,
	):
		self._import_path = import_path
		super().__init__(parent)
		if self._get_project_state_data() is None:
			self._set_project_state_data(self._initial_project_state_data())
		self._setup_layout()
		self.setObjectName(f'plugin.{import_path}')
		self.setWindowTitle(title)

	def closeEvent (self, event: QCloseEvent) -> None:
		logger.debug(f'Unloading plugin {self._import_path}')
		self.__remove_project_state_data()
		LCAPluginManager.unload_plugin(self._import_path)
		self.deleteLater()

	def _get_project_state_data (self) -> pydantic.BaseModel | None:
		return LCAProjectState().model.plugins.get(self.import_path, None)

	def _set_project_state_data (self, new_state: pydantic.BaseModel | None) -> None:
		if LCAProjectState().model.plugins.get(self.import_path, 'notfound') != new_state:
			with LCAProjectState() as state:
				state.model.plugins[self.import_path] = new_state

	def __remove_project_state_data (self) -> None:
		if LCAProjectState().model.plugins.get(self.import_path, 'notfound') == 'notfound':
			return
		with LCAProjectState() as state:
			del state.model.plugins[self.import_path]

