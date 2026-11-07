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

import collections
from loguru import logger

from ...Config import *
from ...I18n import *

from ..LCATaskThread import *
from ...integrations.youtube.LCAYoutubeIntegration import *
from ...models.LCAProjectFileModel import *

class LCARYoutubeVideoPublishTaskThread (LCATaskThread):

	def _run (self,
		project: LCAProjectFileModel,
		privacy: typing.Literal['private', 'unlisted'],
	) -> str:
		with LCAYoutubeIntegration() as yt:
			yt_video_uploader = yt.upload_video(
				filename = project.path_rendered(),
				title = project.video.full_title,
				description = project.video.full_description,
				privacy = privacy,
			)
			while True:
				try:
					self.progress.emit(next(yt_video_uploader))
				except StopIteration as e:
					yt_video_id = e.value
					break
			for _ in yt.set_thumbnail(
				video_id = yt_video_id,
				thumbnail_path = project.video.thumbnail.resolve(),
			):
				pass
			if privacy == 'private':
				series_playlists = Settings().series_from_id(project.series_id).video.add_to_playlists
				variant_playlists = []
				try:
					variant_playlists = Settings().series_variant_from_id(project.series_id, project.variant_id).publishing.video.youtube_playlist_ids
				except ValueError:
					pass
				for playlist_id in ( series_playlists + variant_playlists ):
					yt.add_to_playlist( video_id = yt_video_id, playlist_id = playlist_id )
		with project:
			setattr(project.video.remote_ids.youtube, privacy, yt_video_id)
		return yt_video_id

