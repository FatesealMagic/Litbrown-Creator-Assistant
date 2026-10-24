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

from loguru import logger

from ..LCATaskThread import *
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...models.LCAProjectStateModel import LCAProjectStateModel
from ...integrations.shotcut.LCAShotcutIntegration import LCAShotcutIntegration

class LCARSegmentMelterTaskThread (LCATaskThread):

	def _run (self,
		project: LCAProjectFileModel,
		segment_slug: str,
	) -> None:
		with LCAShotcutIntegration():
			pass
		melter = subprocess.Popen(
			[
				str(pathlib.Path(Config().integrations.local.shotcut.melt_executable_location).resolve()),
				str(project.path_shotcut(segment_slug = segment_slug).resolve()),
				'vcodec=libx264',
				'threads=8',
				'real_time=-8',
				'-progress',
				'-consumer',
				'avformat:' + str(project.path_rendered(segment_slug = segment_slug).resolve()),
			],
			bufsize = 1,
			stdout = subprocess.PIPE,
			stderr = subprocess.STDOUT,
			text = True,
		)
		for line in melter.stdout:
			self.progress.emit( int(line.strip().split(':')[-1].strip()) / 100.0 )
		melter.wait()

