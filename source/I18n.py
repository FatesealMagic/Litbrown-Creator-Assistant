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
import munch
import yaml

class I18n (munch.Munch):
	
	__i18n: munch.Munch
	
	def __init__ (self, key: typing.Type | object):
		if type(key).__name__ in ('type', 'ObjectType', 'ModelMetaclass'):
			super().__init__(self.__i18n[key.__name__])
		else:
			super().__init__(self.__i18n[type(key).__name__])

	@classmethod
	def load (cls, i18n_object: dict) -> None:
		cls.__i18n = munch.munchify(i18n_object)

