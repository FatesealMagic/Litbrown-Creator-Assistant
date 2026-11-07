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
		with LCAYoutubeIntegration() as yt:
			for i, project in enumerate(operables):
				self._emit_progress( i / len(operables) )
				broadcast_id = yt.create_broadcast(
					title       = project.stream.full_title,
					description = project.stream.full_description,
					start       = project.stream.start,
					public      = (project.stream.membertier_id == '~public'),
				)
				self._emit_progress( i / len(operables) + ((1 / 3) / len(operables)) )
				if project.stream.thumbnail:
					for _ in yt.set_thumbnail(
						video_id = broadcast_id,
						thumbnail_path = project.stream.thumbnail.resolve(),
					):
						pass
				self._emit_progress( i / len(operables) + ((2 / 3) / len(operables)) )
				series_playlists = Settings().series_from_id(project.series_id).stream.add_to_playlists
				variant_playlists = []
				try:
					variant_playlists = Settings().series_variant_from_id(project.series_id, project.variant_id).publishing.stream.youtube_playlist_ids
				except ValueError:
					pass
				for playlist_id in ( series_playlists + variant_playlists ):
					yt.add_to_playlist( video_id = broadcast_id, playlist_id = playlist_id )
				with project:
					project.stream.remote_ids.youtube = broadcast_id

