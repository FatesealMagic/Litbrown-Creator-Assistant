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

import enum
import string

from loguru import logger

from ..I18n import *

class LCATextTemplate:
	
	class VariableGroup (enum.Enum):
		DECKLISTS = 'decklists'
		CHAPTERS  = 'chapters'
		CLIP      = 'clip'
		STREAM    = 'stream'
		VIDEO     = 'video'

	__template: string.Template
	
	def __init__ (self, template: str, variable_group: VariableGroup):
		self.__template = string.Template(template)
		self.__variable_group = variable_group
		logger.debug(self.__template)

	def dry_run (self) -> None:
		logger.debug(self.__template.substitute(**{ key: '' for key in self.variables() }))

	@classmethod
	def vars_for_group (cls, group: VariableGroup) -> tuple:
		return tuple(I18n(cls).variables[group.value].keys())

	def variables (self) -> tuple:
		return self.vars_for_group(self.__variable_group)

	@classmethod
	def vars_and_descriptions_for_group (cls, group: VariableGroup) -> dict:
		return dict(I18n(cls).variables[group.value])

	def substitute (self, mapping = {}, /, **kwargs) -> str:
		return self.__template.substitute(mapping, **kwargs)

