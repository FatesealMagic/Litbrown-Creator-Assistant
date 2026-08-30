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
import filelock
import functools
import importlib
import re
import traceback
import typing

from loguru import logger
import tzlocal

from ..Settings import *

from .LCAIntegrationErrors import *

class LCAIntegration:
	
	_RETRIABLE_STATUS_CODES = (429, 500, 502, 503, 504)

	def __init__ (self, *,
		suppress_checks = False,
	):
		self.__filelock = filelock.FileLock(f'lock_{self.integration_name()}.lock')
		self.__suppress_checks = suppress_checks
	
	@classmethod
	def integration_name (cls) -> str:
		return re.match('^LCA(.+)Integration$', cls.__name__).group(1).lower()

	def __enter__ (self):
		if not self.__suppress_checks:
			if not self.is_initialized():
				raise LCAIntegrationNotInitializedError
			self._connect()
			self.__filelock.acquire()
			logger.debug(f'acquired filelock for {self.integration_name()}')
		return self

	def _connect (self) -> None:
		raise NotImplementedError

	def __exit__ (self, exc_type, exc_val, exc_tb) -> bool:
		if exc_type:
			rebuilt = exc_type(exc_val)
			rebuilt.__traceback__ = exc_tb
			logger.exception(rebuilt)
		if not self.__suppress_checks:
			self.__filelock.release()
			logger.debug(f'released filelock for {self.integration_name()}')
			self._disconnect()
		return False

	def _disconnect (self) -> None:
		raise NotImplementedError

	def get_user_info (self) -> Settings().IntegrationsModel.RemoteIntegrationModel:
		raise NotImplementedError

	def get_membertiers_info (self) -> list[Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel]:
		raise NotImplementedError

	@staticmethod
	def is_initialized () -> bool:
		raise NotImplementedError

	@staticmethod
	def in_context (func: typing.Callable) -> typing.Callable:
		@functools.wraps(func)
		def wrapper (self, *args, **kwargs):
			if not self.__suppress_checks and not self.__filelock.is_locked:
				raise RuntimeError('This integration method must be called within a context manager')
			return func(self, *args, **kwargs)
		return wrapper

	@classmethod
	def by_name (cls, name: str) -> type[typing.Self]:
		return getattr(
			importlib.import_module(f'.{name}.LCA{name.title()}Integration', package = __package__),
			f'LCA{name.title()}Integration'
		)

	@staticmethod
	def _exponential_wait (attempt_number: int, status_code: int) -> None:
		logger.warning(f'Exponential backoff attempt #{attempt_number + 1} after received status code {status_code}')
		logger.warning('\n' + ''.join(traceback.format_stack()))
		time.sleep(1.75 ** (attempt_number + 1))

	@staticmethod
	def _apply_bounds_to_timestamp (ts_str: str) -> str:
		ts = datetime.datetime.fromisoformat(ts_str)
		lower = datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(minutes = 15)
		return max(lower, ts).isoformat()

