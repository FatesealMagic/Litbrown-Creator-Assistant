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

import inspect # TODO
import re

from loguru import logger

from ...Config import *
from ...Assets import *
from ...Settings import *

from ..LCAThread import *
from ...integrations.moxfield.LCAMoxfieldIntegration import *
from ...models.LCAProjectFileModel import *
from ...models.LCADecklistModel import *

class LCADeckFetcherThread (LCAThread):
	
	def _run (self, project: LCAProjectFileModel, deck_index: int, save_project: bool = True) -> LCADecklistModel:
		for handler, regex in (
			(self.__moxfield, r'^https:\/\/moxfield\.com\/decks\/(?P<id>[a-zA-Z0-9_-]{22})\/?$'),
		):
			if match := re.match(regex, project.decklists[deck_index].url):
				decklist = handler(match)
				with (project if save_project else project.mutex()):
					project.decklists[deck_index] = decklist
				return decklist

	def __moxfield (self, match: re.Match) -> LCADecklistModel:
		with LCAMoxfieldIntegration() as moxfield:
			return moxfield.get_decklist(match.group(1))

