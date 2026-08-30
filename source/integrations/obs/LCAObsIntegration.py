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

from loguru import logger
import obsws_python

from ..LCAIntegration import *

class LCAObsIntegration (LCAIntegration):

	req_client: obsws_python.ReqClient | None = None
	evt_client: obsws_python.EventClient | None = None
	__host: str
	__port: int
	__pswd: str
	
	def __init__ (self,
		instance: str,
		*args, **kwargs
	):
		if instance not in ('record', 'stream', 'video', 'clip'):
			raise ValueError(f'Invalid instance type passed: {instance}')
		integration_model = getattr(Settings().integrations.obs, instance)
		self.__host = integration_model.host
		self.__port = integration_model.port
		self.__pswd = integration_model.pswd

	def _connect (self) -> None:
		self.connect()

	def connect (self) -> None:
		self.req_client = obsws_python.ReqClient(host = self.__host, port = self.__port, password = self.__pswd)
		self.evt_client = obsws_python.EventClient(host = self.__host, port = self.__port, password = self.__pswd)

	def _disconnect (self) -> None:
		self.disconnect()

	def disconnect (self) -> None:
		self.req_client.disconnect()
		self.evt_client.disconnect()
		self.req_client = None
		self.evt_client = None

	def is_initialized (self) -> bool:
		return bool(self.req_client) and bool(self.evt_client)

