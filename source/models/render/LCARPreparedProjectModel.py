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

import pydantic

from ..LCAProjectFileModel import LCAProjectFileModel
from ..LCAProjectStateModel import LCAProjectStateModel

class LCARPreparedProjectModel (pydantic.BaseModel, validate_assignment = True, extra = 'forbid'):
	project: LCAProjectFileModel
	states: dict[int, LCAProjectStateModel] = {}

	class _MarkersModel (pydantic.BaseModel, validate_assignment = True, extra = 'forbid'):
		mistakes: list[typing.Annotated[int, 'microseconds']] = []
		mutes: list[tuple[typing.Annotated[int, 'Mute start, microseconds'], typing.Annotated[int, 'Mute end, microseconds']]] = []
		clips: list[typing.Annotated[int, 'microseconds']] = []
	markers: _MarkersModel = _MarkersModel()

