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

import pathlib
import subprocess
import time

from loguru import logger
import requests

from ...Settings import *

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *
from ...models.LCAProjectStateModel import *

class LCAFoobarIntegration (LCAIntegration):

	@classmethod
	def is_initialized (cls) -> bool:
		logger.warning(Settings().integrations.foobar.install_location)
		return pathlib.Path(Settings().integrations.foobar.install_location).is_file()

	def _connect (self) -> None:
		self.__launch_foobar()
		self.__wait_for_connection()

	def __launch_foobar (self) -> None:
		subprocess.Popen(f'{Settings().integrations.foobar.install_location} {Settings().integrations.foobar.additional_arguments}') 

	def __wait_for_connection (self) -> None:
		while True:
			try:
				self.__request('GET', 'player')
				break
			except Exception as e:
				time.sleep(0.5)

	def _disconnect (self) -> None:
		pass

	def __request (self,
		method: str,
		endpoint: str,
		/, *,
		params: dict | None = None,
		json: dict | None = None,
	) -> request.Response:
		rsp = requests.request(
			method,
			f'http://localhost:{Settings().integrations.foobar.beefweb_port}/api/{endpoint}',
			params = params,
			json = json,
		)
		if not (200 <= rsp.status_code <= 299):
			raise LCAIntegrationNetworkFailureError(f'Received unexpected status code: {rsp.status_code}')
		return rsp

	def play_music (self) -> None:
		self.__request('POST', 'player/play')

	def stop_music (self) -> None:
		self.__request('POST', 'player/stop')

	def get_current_music (self) -> LCAProjectStateModel.Music:
		rsp = self.__request('GET', 'player', params = {'columns': '%artist%,%title%,%path%'})
		data = rsp.json()['player']['activeItem']['columns']
		return LCAProjectStateModel.Music(
			artist = data[0],
			title =  data[1],
			path =   data[2],
		)

