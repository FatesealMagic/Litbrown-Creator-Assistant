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

import json
import typing

from loguru import logger
import yaml

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import QApplication

class Assets:

	@classmethod
	def __resource_loader (cls, rsc: str) -> bytes:
		with open('assets/' + rsc, 'rb') as f:
			return f.read()

	@classmethod
	def binary (cls, key: str) -> bytes:
		return cls.__resource_loader(key)

	@classmethod
	def QIcon (cls, key: str) -> QIcon:
		pixmap = QPixmap()
		pixmap.loadFromData(cls.binary(key))
		return QIcon(pixmap)

	@classmethod
	def text (cls, key: str) -> str:
		return str(cls.binary(key), 'utf-8')

	@classmethod
	def json (cls, key: str) -> dict:
		return json.loads(cls.text(key))

	@classmethod
	def yaml (cls, key: str) -> dict:
		return yaml.safe_load(cls.text(key))

