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
import uuid

import pydantic

class LCAScryfallCardFaceModel (pydantic.BaseModel, validate_assignment = True):

	object:    typing.Literal['card_face'] = 'card_face'
	oracle_id: uuid.UUID | None = None

	name:            str
	mana_cost:       str
	cmc:             float | None = None
	color_indicator: list[str] | None = None
	colors:          list[str] | None = None

	layout: str | None = None
	
	loyalty:     str | None = None
	defense:     str | None = None
	power:       str | None = None
	toughness:   str | None = None
	type_line:   str | None = None
	oracle_text: str | None = None

	artist:          str | None = None
	artist_id:       uuid.UUID | None = None
	illustration_id: uuid.UUID | None = None
	watermark:       str | None = None

	flavor_text:       str | None = None
	printed_name:      str | None = None
	printed_text:      str | None = None
	printed_type_line: str | None = None

	image_uris: dict[str, str] | None = None

