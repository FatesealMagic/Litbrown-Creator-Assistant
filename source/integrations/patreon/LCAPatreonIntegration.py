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

from loguru import logger
import requests

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *

from ...Assets import *
from ...Settings import *

class LCAPatreonIntegration (LCAIntegration):
	
	@staticmethod
	def is_initialized () -> bool:
		return bool(Settings().integrations.patreon.auth and Settings().integrations.patreon.auth.get('refresh_token'))

	def _connect (self) -> None:
		pass

	def _disconnect (self) -> None:
		pass

	def __execute_request (self, path: str, /,
		method: str = 'GET',
		body_data: dict | None = None,
		body_json: dict | None = None,
		params: dict | None = None,
	) -> requests.Response:
		caught_401 = False
		logger.debug(body_json)
		for attempt in range(10):
			rsp = requests.request(
				method.upper(),
				Config().integrations.remote.patreon.api_url_base + path,
				data = body_data,
				json = body_json,
				params = params,
				headers = {
					'Authorization': f'Bearer {Settings().integrations.patreon.auth.get('access_token')}',
					'Client-Id': Config().integrations.remote.patreon.client_id,
				},
			)
			if rsp.status_code >= 200 and rsp.status_code <= 299:
				return rsp
			elif rsp.status_code == 401:
				if not caught_401:
					caught_401 = True
					logger.info('Refreshing Patreon access token...')
					self.__refresh_access_token()
				else:
					logger.error('Patreon token refresh unsuccessful')
					raise LCAIntegrationBadCredentialsError
			elif rsp.status_code in self._RETRIABLE_STATUS_CODES:
				self._exponential_wait(attempt, rsp.status_code)
			elif rsp.status_code in (403,):
				raise LCAIntegrationUserForbiddenError
			else:
				logger.error(f'Unexpected error while contacting Patreon: {rsp.status_code} {rsp.text}')
				logger.error(rsp.request.url)
				logger.error(rsp.request.body)
				raise LCAIntegrationUnexpectedError
		raise LCAIntegrationNetworkFailureError

	def __execute_paginated_request (self, path: str, /,
		method: str = 'GET',
		body_data: dict | None = None,
		body_json: dict | None = None,
		params: dict | None = None,
	) -> list[dict]:
		RETURNABLE_KEYS = ('data', 'included')
		ret = {k: [] for k in RETURNABLE_KEYS}
		cursor = None
		while True:
			rsp = self.__execute_request(path,
				method = method,
				body_data = body_data,
				body_json = body_json,
				params = params | ({'page[cursor]': cursor} if cursor else {}),
			)
			rspdict = rsp.json()
			for k in RETURNABLE_KEYS:
				ret[k].append(rspdict.get(k, []))
			cursor = rspdict.get('meta', {}).get('pagination', {}).get('cursors', {}).get('next')
			if not cursor:
				break
		return ret

	def __refresh_access_token (self) -> None:
		rsp = requests.get(f'{
			Config().integrations.remote.oauth_service_url
		}/patreon?refresh={
			Settings().integrations.patreon.auth['refresh_token']
		}')
		if rsp.status_code < 200 or rsp.status_code > 299:
			logger.error(f'Error refreshing access token: {rsp.status_code}')
			logger.error(rsp.text)
			raise LCAIntegrationError # TODO maybe a better error type here?
		with Settings():
			logger.info('Saving new Patreon access token')
			Settings().integrations.patreon.auth = rsp.json()

	@LCAIntegration.in_context
	def get_user_info (self) -> Settings().IntegrationsModel.RemoteIntegrationModel:
		rsp = self.__execute_request('campaigns', params={
			'fields[campaign]': 'image_small_url,name,vanity',
		}).json()['data'][0]
		return Settings().IntegrationsModel.RemoteIntegrationModel(
			remote_id               = rsp['id'],
			handle                  = rsp['attributes']['vanity'],
			display_name            = rsp['attributes']['name'],
			profile_pic_url         = rsp['attributes']['image_small_url'],
			auth                    = Settings().integrations.patreon.auth,
			remote_membership_tiers = self.get_membertiers_info(),
		)

	@LCAIntegration.in_context
	def get_membertiers_info (self) -> list[Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel]:
		rsp = self.__execute_paginated_request('campaigns', params={
			'include': 'tiers',
			'fields[tier]': 'title,amount_cents,description',
		})
		return [ Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel(
			remote_id   = tier['id'],
			remote_name = tier['attributes']['title'],
			cents       = tier['attributes']['amount_cents'],
		) for tier in rsp['included'][0] if tier['type'] == 'tier' and tier['attributes']['amount_cents'] > 0 ]

	@LCAIntegration.in_context
	def schedule_broadcast (self, /,
		title: str,
		description: str,
		start: str,
		for_member_tier_id: str | None,
	) -> str:
		#raise LCAIntegrationDeficientRemoteError
		access_ids = []
		if for_member_tier_id:
			for tier in Settings().membership_tiers:
				if access_ids or tier.id == for_member_tier_id:
					access_ids.append(int(tier.remote_ids.patreon))
		ret = self.__execute_request('lives', method = 'POST', body_json = { 'data': {
			'type': 'live',
			'attributes': {
				'title': title,
				'description': description,
				'state': 'pre_live',
				'scheduled_for': self._apply_bounds_to_timestamp(start),
			} | ({'live_access_rule_ids': access_ids} if access_ids else {}),
		}})
		logger.warning(ret.status_code)
		logger.warning(ret.text)
		return ''

