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
import shutil
import tempfile
import typing

class LCAFileOverwriter:

	__filename: str
	__text: bool
	__encoding: str | None
	__file: typing.IO
	
	def __init__ (self,
		filename: str,
		/,
		text: bool = False,
		binary: bool = False,
		encoding: str | None = 'utf-8',
	):
		if not (text ^ binary):
			raise ValueError(f'Need one of text {text} or binary {binary} to be true, not both or neither')
		self.__filename = filename
		self.__text = text
		self.__encoding = encoding

	def __enter__ (self):
		self.__file = tempfile.NamedTemporaryFile(
			mode = 'w' if self.__text else 'wb',
			encoding = self.__encoding if self.__text else None,
			delete = False,
		)
		return self.__file

	def __exit__ (self, exc_type, exc_val, exc_tb):
		tempname = self.__file.name
		try:
			self.__file.close()
		except OsError:
			pass
		pathlib.Path(self.__filename).parent.mkdir(parents = True, exist_ok = True)
		shutil.move(tempname, self.__filename)

