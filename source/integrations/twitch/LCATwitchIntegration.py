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
import json

from loguru import logger
import requests
import tzlocal

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *

from ...Assets import *
from ...Settings import *

class LCATwitchIntegration (LCAIntegration):
	
	@staticmethod
	def is_initialized () -> bool:
		return bool(Settings().integrations.twitch.auth and Settings().integrations.twitch.auth.get('refresh_token'))

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
		for attempt in range(10):
			rsp = requests.request(
				method.upper(),
				Config().integrations.remote.twitch.api_url_base + path,
				data = body_data,
				json = body_json,
				params = params,
				headers = {
					'Authorization': f'Bearer {Settings().integrations.twitch.auth.get('access_token')}',
					'Client-Id': Config().integrations.remote.twitch.client_id,
				},
			)
			if rsp.status_code >= 200 and rsp.status_code <= 299:
				return rsp
			elif rsp.status_code == 401:
				if not caught_401:
					caught_401 = True
					logger.info('Refreshing Twitch access token...')
					self.__refresh_access_token()
				else:
					logger.error('Twitch token refresh unsuccessful')
					raise LCAIntegrationBadCredentialsError
			elif rsp.status_code in self._RETRIABLE_STATUS_CODES:
				self._exponential_wait(attempt, rsp.status_code)
			elif rsp.status_code in (403,):
				raise LCAIntegrationUserForbiddenError
			else:
				logger.error(f'Unexpected error while contacting Twitch: {rsp.status_code} {rsp.text}')
				raise LCAIntegrationError
		raise LCAIntegrationNetworkFailureError

	def __execute_paginated_request (self, path: str, /,
		method: str = 'GET',
		body_data: dict | None = None,
		body_json: dict | None = None,
		params: dict | None = None,
	) -> list[dict]:
		ret = []
		cursor = None
		while True:
			rsp = self.__execute_request(path,
				method = method,
				body_data = body_data,
				body_json = body_json,
				params = params | ({'after': cursor} if cursor else {}),
			)
			rspdict = rsp.json()
			ret.append(rspdict.get('data', []))
			cursor = rspdict.get('pagination', {}).get('cursor')
			if not cursor:
				break
		return ret

	def __refresh_access_token (self) -> None:
		rsp = requests.get(f'{
			Config().integrations.remote.oauth_service_url
		}/twitch?refresh={
			Settings().integrations.twitch.auth['refresh_token']
		}')
		if rsp.status_code < 200 or rsp.status_code > 299:
			logger.error(f'Error refreshing access token: {rsp.status_code}')
			logger.error(rsp.text)
			raise LCAIntegrationError # TODO maybe a better error type here?
		with Settings():
			logger.info('Saving new Twitch access token')
			Settings().integrations.twitch.auth = rsp.json()

	@LCAIntegration.in_context
	def get_user_info (self) -> Settings().IntegrationsModel.RemoteIntegrationModel:
		rsp = self.__execute_request('users').json()['data'][0]
		return Settings().IntegrationsModel.RemoteIntegrationModel(
			remote_id               = rsp['id'],
			handle                  = rsp['login'],
			display_name            = rsp['display_name'],
			profile_pic_url         = rsp['profile_image_url'],
			auth                    = Settings().integrations.twitch.auth,
			remote_membership_tiers = self.get_membertiers_info(),
		)

	@LCAIntegration.in_context
	def get_membertiers_info (self) -> list[Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel]:
		return [
			Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel(
				remote_id = '1000', remote_name = I18n(self).tier_1_name, cents = 599
			),
			Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel(
				remote_id = '2000', remote_name = I18n(self).tier_2_name, cents = 999
			),
			Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel(
				remote_id = '3000', remote_name = I18n(self).tier_3_name, cents = 2499
			),
		]

	@LCAIntegration.in_context
	def schedule_broadcast (self,
		title: str,
		start: str,
		duration: int,
	) -> str:
		return self.__execute_request('schedule/segment',
			method = 'POST',
			params = {'broadcaster_id': Settings().integrations.twitch.remote_id},
			body_json = {
				'start_time': self._apply_bounds_to_timestamp(start),
				'timezone': tzlocal.get_localzone_name(),
				'duration': str(duration),
				'is_recurring': False,
				'title': title,
			},
		).json()['data']['segments'][0]['id']

