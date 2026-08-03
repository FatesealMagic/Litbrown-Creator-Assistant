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

import collections.abc
import threading
import time

from loguru import logger
import requests

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *
from ..scryfall.LCAScryfallIntegration import *
from ...models.LCADecklistModel import *
from ...models.LCAScryfallCardModel import *

class LCAMoxfieldIntegration (LCAIntegration):

	@staticmethod
	def is_initialized () -> bool:
		return bool(Settings().integrations.moxfield.user_agent)

	def _connect (self) -> None:
		pass

	def _disconnect (self) -> None:
		pass

	def __get_headers (self) -> dict:
		return {
			'User-Agent': Settings().integrations.moxfield.user_agent,
		}

	def __execute_request (self, path: str, /,
		method: str = 'GET',
		delay_between_requests: float = 1.0,
		body_data: dict | None = None,
		body_json: dict | None = None,
		params: dict | None = None,
	) -> dict:
		next_uri = None
		while True:
			for attempt in range(10):
				time.sleep(delay_between_requests)
				rsp = requests.request(
					method.upper(),
					f'https://api2.moxfield.com/v3/{path}',
					headers = self.__get_headers(),
					data = body_data,
					json = body_json,
					params = params,
				)
				try:
					rsp_json = rsp.json()
				except Exception as e:
					logger.error(f'Could not parse JSON from Moxfield: {rsp.status_code} {rsp.text}')
					logger.exception(e)
					raise LCAIntegrationUnexpectedError
				if rsp.status_code >= 200 and rsp.status_code <= 299:
					break
				elif rsp.status_code in self._RETRIABLE_STATUS_CODES:
					self._exponential_wait(attempt, rsp.status_code)
				else:
					logger.error(f'Unexpected error while contacting Moxfield: {rsp.status_code} {rsp.text}')
					logger.error(rsp.request.url)
					logger.error(rsp.request.body)
					raise LCAIntegrationUnexpectedError
			return rsp_json

	@LCAIntegration.in_context
	def get_decklist (self, public_id: str) -> LCADecklistModel:
		decklist = LCADecklistModel(
			url = f'https://moxfield.com/decks/{public_id}',
			updated = datetime.datetime.now(),
		)
		moxfield_rsp = self.__execute_request(f'decks/all/{public_id}')
		decklist.title = moxfield_rsp['name']
		decklist.description = moxfield_rsp['description']
		scryfall_ids = {
			card['card']['scryfall_id']
			for card in itertools.chain.from_iterable([
				moxfield_rsp['boards'][board]['cards'].values()
				for board in ('mainboard', 'sideboard', 'commanders', 'companions')
			])
		}
		with LCAScryfallIntegration() as scryfall:
			scryfall_cards = {
				str(card.id): card
				for card in scryfall.collection([{'id': id} for id in scryfall_ids])
			}
		for mox_board, lca_board in (
			('mainboard',  'mainboard'),
			('sideboard',  'sideboard'),
			('commanders', 'command'),
			('companions', 'companion'),
		):
			for mox_card in moxfield_rsp['boards'][mox_board]['cards'].values():
				lca_card = scryfall_cards[mox_card['card']['scryfall_id']].model_copy(deep = True)
				lca_card.lca_quantity = mox_card['quantity']
				getattr(decklist.boards, lca_board).append(lca_card)
		return decklist

