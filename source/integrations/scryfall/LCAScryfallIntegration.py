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
import gzip
import io
import itertools
import json
import pathlib
import sqlite3
import time

from loguru import logger
import requests

from ...Config import Config

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *
from ...models.LCAScryfallCardModel import *

class LCAScryfallIntegration (LCAIntegration):
	
	@staticmethod
	def is_initialized () -> bool:
		return True

	def _connect (self) -> None:
		pass

	def _disconnect (self) -> None:
		pass

	def __get_headers (self) -> dict:
		return {
			'Accept': 'application/json',
			'User-Agent': f'LitbrownCreatorAssistant/0.3.0', # TODO put version number somewhere better
		}

	def __execute_paginated_request (self, path: str, /,
		method: str = 'GET',
		delay_between_requests: float = 0.1,
		body_data: dict | None = None,
		body_json: dict | None = None,
		params: dict | None = None,
	) -> collections.abc.Iterator[object]:
		next_uri = None
		while True:
			for attempt in range(10):
				time.sleep(delay_between_requests)
				logger.debug(next_uri)
				if next_uri:
					rsp = requests.request(
						method.upper(),
						next_uri,
						headers = self.__get_headers(),
					)
				else:
					rsp = requests.request(
						method.upper(),
						'https://api.scryfall.com/' + path,
						headers = self.__get_headers(),
						data = body_data,
						json = body_json,
						params = params,
					)
				try:
					rsp_json = rsp.json()
				except Exception as e:
					logger.error(f'Could not parse JSON from Scryfall: {rsp.status_code} {rsp.text}')
					logger.exception(e)
					raise LCAIntegrationUnexpectedError
				if rsp.status_code >= 200 and rsp.status_code <= 299:
					break
				elif rsp.status_code in (400, 404):
					raise LCAIntegrationErroneousUserInputError(rsp_json['details'])
				elif rsp.status_code == 429:
					logger.warning('Encountered 429 Too Many Requests from Scryfall. Waiting 30 seconds, then trying again. https://scryfall.com/docs/api/rate-limits')
					time.sleep(30)
				elif rsp.status_code in self._RETRIABLE_STATUS_CODES:
					self._exponential_wait(attempt, rsp.status_code)
				else:
					logger.error(f'Unexpected error while contacting Scryfall: {rsp.status_code} {rsp.text}')
					logger.error(rsp.request.url)
					logger.error(rsp.request.body)
					raise LCAIntegrationUnexpectedError
			yield rsp_json['data']
			if rsp_json.get('has_more', None):
				next_uri = rsp_json['next_page']
			else:
				return

	@LCAIntegration.in_context
	def refresh_local_data (self) -> None:
		gzipped_cards = self.remote_bulk_data()
		with gzip.GzipFile( fileobj = io.BytesIO(gzipped_cards), mode = 'rb' ) as gzip_file:
			with io.TextIOWrapper( gzip_file, encoding = 'utf-8' ) as raw_cards:
				with self.__prepare_local_card_database() as db:
					cur = db.cursor()
					for raw_card in raw_cards:
						card = json.loads(raw_card)
						cur.execute(
							'INSERT INTO cards (name, set_code, collector_number, scryfall_id, json) VALUES (?, ?, ?, ?, ?)',
							(card['name'], card['set'], card['collector_number'], card['id'], raw_card),
						)
					cur.close()
				db.close()

	def __prepare_local_card_database (self) -> sqlite3.Connection:
		db_path = pathlib.Path(Config().integrations.local.scryfall.models_path)
		db_path.parent.mkdir(parents = True, exist_ok = True)
		db_path.unlink(missing_ok = True)
		db = sqlite3.connect(db_path)
		db.executescript( Config().integrations.local.scryfall.db_schema ).close()
		return db

	def __get_model_db (self) -> sqlite3.Connection:
		return sqlite3.connect(pathlib.Path(Config().integrations.local.scryfall.models_path))

	@LCAIntegration.in_context
	def search_by_name (self,
		name: str,
		*,
		unique: typing.Literal['cards', 'art', 'prints'] = 'prints',
	) -> list[LCAScryfallCardModel]:
		tokens = [ f'%{token}%' for token in name.lower().split(' ') if token ]
		query = 'SELECT json FROM cards WHERE '
		if len(tokens) == 1 and len(tokens[0]) <= 5:
			tokens[0] = name
			query += 'LOWER(name) IS ? '
		else:
			query += ' AND '.join(['LOWER(name) LIKE ?'] * len(tokens))
		with self.__get_model_db() as db:
			cur = db.cursor()
			cur.execute(query, tokens)
			results = cur.fetchall()
			cur.close()
		db.close()
		models = [ LCAScryfallCardModel(**json.loads(result[0])) for result in results ]
		if unique == 'prints':
			return models
		if unique == 'art':
			raise NotImplementedError
		if unique == 'cards':
			logger.warning(len(models))
			collapsed_results = {}
			for model in models:
				if getattr(
					collapsed_results.get(model.name, object()),
					'released_at',
					datetime.datetime.fromisoformat('1990-01-01').date()
				) < model.released_at:
					collapsed_results[model.name] = model
			return list(collapsed_results.values())

	@LCAIntegration.in_context
	def remote_bulk_data (self) -> bytes:
		for bulk_data_info in self.__execute_paginated_request('bulk-data'):
			download_uri = next( (obj for obj in bulk_data_info if obj['type'] == 'default_cards') )['jsonl_download_uri']
			rsp = requests.get(download_uri)
			if rsp.status_code != 200:
				raise LCAIntegrationUnexpectedError
			return rsp.content

	@LCAIntegration.in_context
	def remote_query (self,
		query: str,
		*,
		unique: typing.Literal['cards', 'art', 'prints'] = 'prints',
	) -> collections.abc.Iterator[list[LCAScryfallCardModel]]:
		for page in self.__execute_paginated_request(
			'cards/search',
			delay_between_requests = 0.5,
			params = {'q': query, 'unique': 'prints'},
		):
			yield [LCAScryfallCardModel(**raw_card_data) for raw_card_data in page]

	@LCAIntegration.in_context
	def remote_collection (self, identifiers: collections.abc.Iterable[dict]) -> collections.abc.Iterator[LCAScryfallCardModel]:
		for batch in itertools.batched(identifiers, 75):
			logger.debug(batch)
			page = self.__execute_paginated_request(
				'cards/collection',
				method = 'POST',
				delay_between_requests = 0.5,
				body_json = {'identifiers': batch},
			)
			for result in page:
				for raw_card_data in result:
					yield LCAScryfallCardModel(**raw_card_data)

