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

import copy
import xml.etree.ElementTree

from loguru import logger

from ..LCATaskThread import *
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...models.LCAProjectStateModel import LCAProjectStateModel
from ...models.render.LCARPreparedProjectModel import LCARPreparedProjectModel
from ...integrations.autoeditor.LCAAutoeditorIntegration import LCAAutoeditorIntegration
from ...integrations.shotcut.LCAShotcutIntegration import LCAShotcutIntegration

class LCARFootagePreparerTaskThread (LCATaskThread):

	def _run (self,
		prepared: LCARPreparedProjectModel,
		segment_slug: str,
	) -> None:
		self.__prepared = prepared
		self.__segment_slug = segment_slug
		self.__segment_id, self.__segment_number = LCAProjectFileModel.split_slug(self.__segment_slug)
		self.__last_state = self.__prepared.states[ list(sorted(self.__prepared.states.keys()))[-1] ]
		self.__start_ts = self.__last_state.start_timestamps[self.__segment_slug]
		self.__run_autoeditor()
		self.__mlt = self.__load_shotcut_file()
		self.__mlt.write(f'projects/{self.__prepared.project.slug()}/shotcut/original-{segment_slug}.mlt') # TODO remove
		self.__framerate = LCAShotcutIntegration.get_framerate(self.__mlt)
		self.__extract_muted_segments()
		self.__apply_mistake_markers()
		self.__save_shotcut_file()

	def __run_autoeditor (self) -> None:
		with LCAAutoeditorIntegration() as autoeditor:
			logger.info(f'Preparing footage for {self.__prepared.project.slug()} {self.__segment_slug}')
			autoeditor.process_slug(self.__prepared.project, self.__segment_slug, margin = 0.23) # TODO margin as setting

	def __load_shotcut_file (self) -> xml.etree.ElementTree:
		return xml.etree.ElementTree.parse(self.__prepared.project.path_shotcut(
			segment_id = self.__segment_id,
			segment_number = self.__segment_number,
		))

	def __extract_muted_segments (self) -> None:
		parent = self.__mlt.getroot().find('./playlist[@id="playlist0"]')
		to_delete = []
		to_split = []
		to_update_start = []
		to_update_end = []
		for entry in parent.findall('./entry'):
			start = LCAShotcutIntegration.mltts_to_lcats(entry.attrib['in'],  offset = self.__start_ts)
			end   = LCAShotcutIntegration.mltts_to_lcats(entry.attrib['out'], offset = self.__start_ts)
			for mute_start, mute_end in self.__prepared.markers.mutes:
				if mute_start < start < end < mute_end:
					logger.debug(f'{self.__segment_slug}: Deleting entry with producer "{entry.get('producer')}" ({start}, {end}) due to mute ({mute_start}, {mute_end})')
					to_delete.append(entry)
				elif start < mute_start < mute_end < end:
					logger.debug(f'{self.__segment_slug}: Splitting entry with producer "{entry.get('producer')}" ({start}, {end}) due to mute ({mute_start}, {mute_end})')
					to_split.append((entry, mute_start, mute_end))
				elif start < mute_end < end:
					logger.debug(f'{self.__segment_slug}: Updating in-time of entry with producer "{entry.get('producer')}" ({start}, {end}) due to mute ({mute_start}, {mute_end})')
					to_update_start.append((entry, mute_end))
				elif start < mute_start < end:
					logger.debug(f'{self.__segment_slug}: Updating out-time of entry with producer "{entry.get('producer')}" ({start}, {end}) due to mute ({mute_start}, {mute_end})')
					to_update_end.append((entry, mute_start))
		for e in to_delete:
			parent.remove(e)
		for e, mute_start, mute_end in to_split:
			e1 = e
			e2 = copy.deepcopy(e)
			e1.set('out', LCAShotcutIntegration.lcats_to_mltts(mute_start, offset = self.__start_ts, framerate = self.__framerate))
			e2.set('in',  LCAShotcutIntegration.lcats_to_mltts(mute_end,   offset = self.__start_ts, framerate = self.__framerate))
			parent.insert(list(parent).index(e) + 1, e2)
		for e, mute_end in to_update_start:
			e.set('in',  LCAShotcutIntegration.lcats_to_mltts(mute_end,   offset = self.__start_ts, framerate = self.__framerate))
		for e, mute_start in to_update_end:
			e.set('out', LCAShotcutIntegration.lcats_to_mltts(mute_start, offset = self.__start_ts, framerate = self.__framerate))

	def __apply_mistake_markers (self) -> None:
		pass

	def __save_shotcut_file (self) -> None:
		self.__mlt.write(self.__prepared.project.path_shotcut(
			segment_id = self.__segment_id,
			segment_number = self.__segment_number,
		))

