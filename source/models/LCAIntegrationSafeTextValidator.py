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

import typing

from loguru import logger

from ..Config import *

def LCAIntegrationSafeTextValidator (*, max_len: int = -1) -> typing.Callable[[str], str]:
	def validator (val: str) -> str:
		try:
			disallowed = ''
			for integration in Config().integrations.remote.model_dump().values():
				disallowed += getattr(integration, 'disallowed_characters', '')
			safe = val.translate(str.maketrans('', '', disallowed))
			return safe[:max_len] if max_len >= 0 else safe
		except AttributeError:
			return val[:max_len] if max_len >= 0 else val
	return validator

