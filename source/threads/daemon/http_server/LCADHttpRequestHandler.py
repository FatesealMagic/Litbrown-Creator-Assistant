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

import http.server
import re
import urllib.parse

from loguru import logger
import requests

from ....I18n import *
from ....Settings import *

from ....integrations.LCAIntegration import *

class LCADHttpRequestHandler (http.server.SimpleHTTPRequestHandler):
	
	def __init__ (self, *args):
		super().__init__(*args, directory = Settings().tools.general.www_directory)

	def log_message (self, format: str, *args) -> None:
		logger.info((format % args).translate(self._control_char_table))

	def _send_response (self, code: int, data: dict | None = None) -> None:
		self.send_response(code)
		if not data:
			self.send_header('Content-Length', '0')
			body = ''
		elif type(data) == dict:
			self.send_header('Content-Type', 'application/json')
			body = json.dumps(data).encode('utf-8')
		elif type(data) == str:
			self.send_header('Content-Type', 'text/plain')
			body = data.encode('utf-8')
		self.end_headers()
		if body:
			self.wfile.write(body)
	
	def __is_private_request (self) -> bool:
		return self.path[:3] == '/-/'

	def __get_private_request_path (self) -> str:
		return self.path[3:]

	def do_GET (self) -> None:
		if not self.__is_private_request():
			return super().do_GET()
		match path := self.__get_private_request_path():
			case _ if m := re.match(r'^oauth\/([a-z]+)\/?[\?#](.*)$', path):
				integration_name = m.group(1)
				code = urllib.parse.parse_qs(m.group(2)).get('code', '')
				code = code[0] if type(code) == list else code
				if integration_name in Config().integrations.remote.model_dump().keys():
					self.__handle_oauth(integration_name, code)
				else:
					self._send_response(404)
			case _:
				logger.warning(f'Could not route private request: {path}')
				self._send_response(404)

	def do_POST (self) -> None:
		if not self.__is_private_request():
			return super().do_POST()
		match path := self.__get_private_request_path():
			case _ if m := re.match(r'^register-lcapid\/(\d+)$', path):
				self.__register_lcapid(int(m.group(1)))
				self._send_response(204)
			case _:
				logger.warning(f'Could not route private request: {path}')
				self._send_response(404)

	def __register_lcapid (self, lcapid: int) -> None:
		self.server.pid_deque.append(lcapid)
		logger.info(f'Now watching PID {lcapid}')

	def __handle_oauth (self, integration_name: str, code: str) -> None:
		try:
			assert code
			IntegrationClass = LCAIntegration.by_name(integration_name)
			rsp = requests.get(f'{Config().integrations.remote.oauth_service_url}/{integration_name}?code={code}')
			assert rsp.status_code == 200
			logger.debug(rsp.json())
			with Settings():
				getattr(Settings().integrations, integration_name).auth = rsp.json()
			with IntegrationClass(suppress_checks = True) as integration:
				user = integration.get_user_info()
			with Settings():
				setattr(Settings().integrations, integration_name, user)
			with IntegrationClass():
				pass # Always ensure connected account is whitelisted
			self._send_response(200, I18n(self).oauth_successful)
		except Exception as e:
			logger.exception(e)
			with Settings():
				getattr(Settings().integrations, integration_name).reset()
			self._send_response(499, I18n(self).oauth_aborted)
	
	'''def __handle_twitch_oauth (self, code: str) -> None:
		try:
			assert code
			rsp = requests.get(f'{Config().integrations.remote.oauth_service_url}/twitch?code={code}')
			assert rsp.status_code == 200
			with Settings():
				Settings().integrations.twitch.auth = rsp.json()
			with LCATwitchIntegration(suppress_checks = True) as twitch:
				user_info = twitch.get_user_info()
				with Settings():
					for k, v in user_info.items():
						setattr(getattr(Settings().integrations, 'twitch'), k, v)
			with LCATwitchIntegration():
				pass # Validate user information only
			self._send_response(200, I18n(self).oauth_successful)
		except Exception as e:
			logger.exception(e)
			with Settings():
				Settings().integrations.twitch.reset()
			self._send_response(499, I18n(self).oauth_aborted)

	def __handle_youtube_oauth (self, code: str) -> None:
		try:
			assert code
			rsp = requests.get(f'{Config().integrations.remote.oauth_service_url}/youtube?code={code}')
			assert rsp.status_code == 200
			with Settings():
				Settings().integrations.youtube.auth = rsp.json()
			with LCAYoutubeIntegration(suppress_checks = True) as youtube:
				user_info = youtube.get_user_info()
				with Settings():
					pass
			self._send_response(200, I18n(self).oauth_successful)
		except Exception as e:
			logger.exception(e)
			with Settings():
				Settings().integrations.youtube.reset()
			self._send_response(499, I18n(self).oauth_aborted)'''

