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
import pydantic

from .LCAProjectFileModel import *

class LCAProjectStateModel (pydantic.BaseModel, validate_assignment = True):

	project: LCAProjectFileModel

	segment_id: str | None = None
	segment_number: int = 0
	active: bool = False
	start_timestamps: dict[	typing.Annotated[str, 'segment_id-segment_number'], float ] = pydantic.Field( default_factory = dict )
	mistake_count: int = 0
	muted: bool = False

	class _Mtgo (pydantic.BaseModel, validate_assignment = True):
		
		class _Match (pydantic.BaseModel, validate_assignment = True):
			id: int
			best_of: int = 3
			
			class _Game (pydantic.BaseModel, validate_assignment = True):
				id: int
				players: list[str]
				winners: list[str] | None = None
				losers: list[str] | None = None
			games: list[_Game] = []

		matches: list[LCAMtgoMatchModel] = []

		#state: LCAMtgoStateModel = LCAMtgoStateModel() # TODO

	mtgo: _Mtgo = _Mtgo()

	class _Core (pydantic.BaseModel, validate_assignment = True):
		pass
	core: _Core = _Core()

	class _Plugins (pydantic.BaseModel, validate_assignment = True, extra = 'allow'):
		pass
	plugins: _Plugins = _Plugins()

