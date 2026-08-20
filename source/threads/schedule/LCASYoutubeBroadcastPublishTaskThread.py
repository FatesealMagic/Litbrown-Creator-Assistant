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

import time

from loguru import logger

from ...Config import *
from ...I18n import *

from ..LCATaskThread import *
from ...integrations.youtube.LCAYoutubeIntegration import *
from ...models.LCAProjectFileModel import *

class LCASYoutubeBroadcastPublishTaskThread (LCATaskThread):

	def _run (self, data: list[LCAProjectFileModel], schedule_title: str, schedule_desc: str) -> None:
		operables = [ p for p in data if p.stream.membertier_id != '~nostream' ]
		for i, project in enumerate(operables):
			self._emit_progress( i / len(operables) )
			with LCAYoutubeIntegration() as yt:
				broadcast_id = yt.create_broadcast(
					title       = project.stream.full_title,
					description = project.stream.full_description,
					start       = project.stream.start,
					public      = (project.stream.membertier_id == '~public'),
				)
			if project.stream.thumbnail:
				self._emit_progress( i / len(operables) + (0.5 / len(operables)) )
				with LCAYoutubeIntegration() as yt:
					yt.set_thumbnail( video_id = broadcast_id, thumbnail_path = project.stream.thumbnail )
			with project:
				project.stream.remote_ids.youtube = broadcast_id

