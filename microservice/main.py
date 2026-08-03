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
import re
import typing

import flask
import functions_framework
import requests

class LCAMRequestHandler:
	
	__OAUTH_URLS = {
		'twitch':  'https://id.twitch.tv/oauth2/token',
		'youtube': 'https://oauth2.googleapis.com/token',
		'patreon': 'https://www.patreon.com/api/oauth2/token',
	}
	
	__CONFIG_PORT = 42967
	
	__req: flask.Request
	
	def __init__ (self, req: flask.Request):
		self.__req = req

	def response (self) -> flask.Response:
		for pattern, handler in self.__routing():
			if match := re.match(pattern, self.__req.path):
				try:
					return handler(match)
				except Exception as e:
					print(e)
					return flask.make_response('', 500)
		return flask.make_response('', 400)

	def __routing (self) -> list[tuple[str, typing.Callable]]:
		return [
			(r'^\/oauth\/([a-z]+)$', self.__oauth_handle_request),
		]
		
	def __oauth_handle_request (self, match: re.Match) -> flask.Response:
		integration = match.group(1)
		if integration in self.__OAUTH_URLS.keys():
			secret = self.__oauth_get_secret(integration)
			if arg := self.__req.args.get('code'):
				secret |= self.__oauth_get_code_fields(arg, integration)
			elif arg := self.__req.args.get('refresh'):
				secret |= self.__oauth_get_refresh_fields(arg)
			else:
				return flask.make_response('', 400)
			rsp = requests.post(self.__OAUTH_URLS[integration], data = secret)
			if rsp.status_code != 200:
				print(f'Encountered non-OK status code: {integration} {arg} {rsp.status_code} {rsp.text}')
				return flask.make_response('', 503)
			return flask.make_response(rsp.json(), 200)
		else:
			return flask.make_response('', 404)

	def __oauth_get_secret (self, integration: str) -> dict:
		with open(f'secrets_{integration}.json') as f:
			secret = json.loads(f.read())
		if integration in ('youtube',):
			secret = secret['web']
		return { key: secret[key] for key in ('client_id', 'client_secret') }

	def __oauth_get_code_fields (self, code: str, integration: str) -> dict:
		fields = {
			'redirect_uri': f'http://localhost:{self.__CONFIG_PORT}/-/oauth/{integration}',
			'grant_type':   'authorization_code',
			'code':         code,
		}
		if integration in ('youtube',):
			fields['access_type'] = 'offline'
		return fields

	def __oauth_get_refresh_fields (self, refresh: str) -> dict:
		return {
			'refresh_token': refresh,
			'grant_type':    'refresh_token',
		}
	
def main (req: flask.Request) -> flask.Response:
	return LCAMRequestHandler(req).response()



