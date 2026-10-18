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

from loguru import logger

from ...Settings import *

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *
from ...models.LCAProjectStateModel import *

class LCAShotcutIntegration (LCAIntegration):

	@classmethod
	def is_initialized (cls) -> bool:
		return pathlib.Path(Config().integrations.local.shotcut.shotcut_executable_location).is_file()

	def _connect (self) -> None:
		pass

	def _disconnect (self) -> None:
		pass

	@staticmethod
	def mltts_to_lcats (
		mltts: str,
		/, *,
		offset: int = 0,
	) -> int:
		h, m, s = mltts.split(':')
		return int( offset + 1e6 * datetime.timedelta(
			hours   = int(h),
			minutes = int(m),
			seconds = float(s),
		).total_seconds() )

	@staticmethod
	def lcats_to_mltts (lcats: int,
		/, *,
		offset: int = 0,
		framerate: float = 30.0,
	) -> str:
		total_seconds = (lcats - offset) / 1e6
		sign = '-' if total_seconds < 0 else ''
		total_seconds = abs(total_seconds)
		total_seconds = round( total_seconds * framerate ) / framerate
		h = int(total_seconds / 3600)
		m = int((total_seconds / 60) % 60)
		s = float(total_seconds % 60)
		return f'{sign}{h:02}:{m:02}:{s:.03f}'

	@staticmethod
	def get_framerate (
		mlt: xml.etree.ElementTree,
	) -> float:
		profile = mlt.getroot().find('./profile')
		return float(profile.get('frame_rate_num', 30)) / float(profile.get('frame_rate_den', 1))

