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

import datetime
import typing
import uuid

import pydantic

from .LCAScryfallCardFaceModel import *
from .LCAScryfallRelatedCardModel import *

# https://scryfall.com/docs/api/cards

class LCAScryfallCardModel (pydantic.BaseModel, validate_assignment = True):

	# Core Card Fields #########################################################

	object:              typing.Literal['card'] = 'card'
	id:                  uuid.UUID
	arena_id:            int | None = None
	mtgo_id:             int | None = None
	mtgo_foil_id:        int | None = None
	multiverse_ids:      list[int] | None = None
	resource_id:         str | None = None
	tcgplayer_id:        int | None = None
	tcgplayer_etched_id: int | None = None
	cardmarket_id:       int | None = None
	oracle_id:           uuid.UUID | None = None
	
	lang:   str
	layout: str
	
	prints_search_uri: str
	rulings_uri:       str
	scryfall_uri:      str
	uri:               str

	# Gameplay Fields ##########################################################

	all_parts:       list[LCAScryfallRelatedCardModel] | None = None
	card_faces:      list[LCAScryfallCardFaceModel] | None = None

	name:            str
	color_identity:  list[str]
	keywords:        list[str]
	cmc:             float | None = None
	type_line:       str | None = None
	oracle_text:     str | None = None
	mana_cost:       str | None = None
	power:           str | None = None
	toughness:       str | None = None
	loyalty:         str | None = None
	colors:          list[str] | None = None
	color_indicator: list[str] | None = None
	defense:         str | None = None
	hand_modifier:   str | None = None
	life_modifier:   str | None = None
	produced_mana:   list[str] | None = None

	legalities:   dict
	reserved:     bool
	game_changer: bool | None = None

	edhrec_rank: int | None = None
	penny_rank:  int | None = None

	# Print Fields #############################################################

	border_color:     str
	collector_number: str
	finishes:         list[str]
	frame:            str
	rarity:           str
	artist:           str | None = None
	artist_ids:       list[str] | None = None
	card_back_id:     uuid.UUID | None = None

	flavor_name:       str | None = None
	flavor_text:       str | None = None
	printed_name:      str | None = None
	printed_text:      str | None = None
	printed_type_line: str | None = None

	booster:      bool
	digital:      bool
	games:        list[str]
	reprint:      bool
	variation:    bool
	variation_of: uuid.UUID | None = None
	
	full_art:          bool
	oversized:         bool
	promo:             bool
	story_spotlight:   bool
	textless:          bool
	promo_types:       list[str] | None = None
	attraction_lights: list | None = None # TODO what types are present in this list?
	frame_effects:     list[str] | None = None
	security_stamp:    str | None = None
	watermark:         str | None = None

	set_name:       str
	set_search_uri: str
	set_type:       str
	set_uri:        str
	set:            str
	set_id:         uuid.UUID

	highres_image:   bool
	image_status:    str
	image_uris:      dict[str, str] | None = None
	illustration_id: uuid.UUID | None = None

	related_uris:     dict
	scryfall_set_uri: str
	prices:           dict | None = None
	purchase_uris:    dict | None = None

	released_at: datetime.date

	content_warning: bool | None = None

	# LCA Fields ###############################################################

	lca_selected_face: int = 0
	lca_quantity: int = 1

