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

import math
import subprocess
import sys

from loguru import logger

class Util:
	
	CLI_TOOLS = ('daemon',)
	GUI_TOOLS = ('launcher', 'configure', 'schedule', 'multicast', 'edit', 'thumbnail', 'render')
	
	@classmethod
	def app_name (cls) -> str:
		if len(sys.argv) > 1 and sys.argv[1].lower() in cls.CLI_TOOLS + cls.GUI_TOOLS:
			return sys.argv[1].lower()
		return 'daemon'
	
	@classmethod
	def app_args (cls) -> list[str]:
		return sys.argv[2:]

	@classmethod
	def is_python_build (cls) -> None:
		return '.' in sys.argv[0] and sys.argv[0].split('.')[-1] == 'py'

	@classmethod
	def launch_new_instance (cls,
		tool: str,
		args: list[str] = [],
		/,
	) -> subprocess.Popen | None:
		try:
			return subprocess.Popen( [sys.executable, '-m', 'source', tool.lower()] + args )
		except Exception as e:
			logger.exception(e)
			return None

	@classmethod
	def oklch_to_hex (cls, l: float, c: float, h: float) -> QColor:
		# Yeah I stole this, good luck understanding it: https://observablehq.com/@coulterg/oklab-oklch-color-functions
		oklab_l  = l
		oklab_a  = c * math.cos(math.radians(h))
		oklab_b  = c * math.sin(math.radians(h))
		lsrgb_l = (oklab_l + 0.3963377774 * oklab_a + 0.2158037573 * oklab_b) ** 3
		lsrgb_m = (oklab_l - 0.1055613458 * oklab_a - 0.0638541728 * oklab_b) ** 3
		lsrgb_s = (oklab_l - 0.0894841775 * oklab_a - 1.2914855480 * oklab_b) ** 3
		lsrgb_r = + 4.0767416621 * lsrgb_l - 3.3077115913 * lsrgb_m + 0.2309699292 * lsrgb_s
		lsrgb_g = - 1.2684380046 * lsrgb_l + 2.6097574011 * lsrgb_m - 0.3413193965 * lsrgb_s
		lsrgb_b = - 0.0041960863 * lsrgb_l - 0.7034186147 * lsrgb_m + 1.7076147010 * lsrgb_s
		idk = lambda x : 1.055 * (x ** (1.0 / 2.4)) - 0.055 if x >= 0.0031308 else 12.92 * x
		srgb_r, srgb_g, srgb_b = (int(round(idk(x) * 255)) for x in (lsrgb_r, lsrgb_g, lsrgb_b))
		return f'#{srgb_r:02X}{srgb_g:02X}{srgb_b:02X}'

