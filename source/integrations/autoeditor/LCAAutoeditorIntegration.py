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

import collections.abc
import pathlib
import subprocess

from loguru import logger

from PySide6.QtCore import *

from ...Settings import *

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *
from ...models.LCAProjectStateModel import *

class LCAAutoeditorIntegration (LCAIntegration):

	@classmethod
	def is_initialized (cls) -> bool:
		return pathlib.Path(Config().integrations.local.autoeditor.executable_location).is_file()

	def _connect (self) -> None:
		pass

	def _disconnect (self) -> None:
		pass

	@LCAIntegration.in_context
	def process_slug (self,
		project: LCAProjectFileModel,
		segment_slug: str,
		/, *,
		margin: float,
	) -> None:
		if not self.is_initialized():
			raise LCAIntegrationNotInitializedError
		segment_id, segment_number = LCAProjectFileModel.split_slug(segment_slug)
		ae = subprocess.run([
			str(pathlib.Path(Config().integrations.local.autoeditor.executable_location).resolve()),
			str(project.path_footage(segment_id = segment_id, segment_number = segment_number).resolve()),
			'--output',
			str(project.path_shotcut(segment_id = segment_id, segment_number = segment_number).resolve()),
			'--margin',
			f'{margin}sec',
			'--export',
			'shotcut',
			'--progress',
			'none',
			'--no-cache',
		])
		if code := ae.returncode:
			raise LCAIntegrationUnexpectedError(f'Auto-Editor processing footage for segment {segment_slug} in project {project.slug()} returned status code {code}')

