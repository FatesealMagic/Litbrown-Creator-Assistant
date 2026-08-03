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

import pathlib

from loguru import logger

from ..Settings import *

from PySide6.QtCore import *

class LCAProjectWatcher (QFileSystemWatcher):
	
	def __init__ (self,
		slug: str | None = None,
		parent: QObject | None = None,
	):
		super().__init__(parent)
		self.__slug = slug
		self.__setup_watcher()
		Settings().signals().changed.connect(self.__setup_watcher)
		self.directoryChanged.connect(self.__setup_watcher)

	def __setup_watcher (self):
		with QSignalBlocker(self):
			self.removePaths(self.files() + self.directories())
			if self.__slug:
				self.addPath(str(pathlib.Path( f'{Settings().tools.general.projects_location}/{self.__slug}' )))
				for file in pathlib.Path( f'{Settings().tools.general.projects_location}/{self.__slug}' ):
					if not file.is_file().iterdir():
						continue
					self.addPath(str(file))
			else:
				self.addPath(str(pathlib.Path( Settings().tools.general.projects_location )))
				for project_dir in pathlib.Path( Settings().tools.general.projects_location ).iterdir():
					if not project_dir.is_dir():
						continue
					self.addPath(str(project_dir))
					for file in project_dir.iterdir():
						if not file.is_file():
							continue
						self.addPath(str(file))

