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

from ...I18n import I18n
from ...Settings import Settings

from ..LCATaskThread import *
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...models.LCAProjectStateModel import LCAProjectStateModel
from ...integrations.autoeditor.LCAAutoeditorIntegration import LCAAutoeditorIntegration
from ...integrations.shotcut.LCAShotcutIntegration import LCAShotcutIntegration

class LCARFootagePreparerTaskThread (LCATaskThread):

	def _run (self,
		project: LCAProjectFileModel,
		segment_slug: str,
	) -> None:
		self.__project = project
		self.__segment_slug = segment_slug
		self.__segment_id, self.__segment_number = LCAProjectFileModel.split_slug(self.__segment_slug)
		self.__start_ts = self.__project.events.segments[self.__segment_slug].start_ts
		self.__run_autoeditor()
		self.__mlt = self.__load_shotcut_file()
		self.__framerate = LCAShotcutIntegration.get_framerate(self.__mlt)
		self.__apply_mistake_markers()
		self.__apply_mute_markers()
		self.__save_shotcut_file()

	def __run_autoeditor (self) -> None:
		with LCAAutoeditorIntegration() as autoeditor:
			logger.info(f'Preparing footage for {self.__project.slug()} {self.__segment_slug}')
			autoeditor.process_slug(
				self.__project,
				self.__segment_slug,
				margin = Settings().series_from_id(self.__project.series_id).video.autoeditor_margin,
			)

	def __load_shotcut_file (self) -> xml.etree.ElementTree:
		return xml.etree.ElementTree.parse(self.__project.path_shotcut(
			segment_id = self.__segment_id,
			segment_number = self.__segment_number,
		))

	def __apply_mute_markers (self) -> None:
		for i, (mute_start_lcats, mute_end_lcats) in enumerate(self.__project.events.mutes):
			mute_end_lcats = mute_end_lcats or 9999_9999_9999_9999
			mute_start_mltts = self.__lcats_to_mltts(mute_start_lcats)
			mute_end_mltts = self.__lcats_to_mltts(mute_end_lcats)
			if mute_start_mltts == mute_end_mltts:
				continue
			self.__add_marker_to_mlt(
				text = f'{I18n(self).markers.mute.prefix}{i + 1}{I18n(self).markers.mute.suffix}',
				start_mltts = mute_start_mltts,
				end_mltts = mute_end_mltts,
			)

	def __apply_mistake_markers (self) -> None:
		for i, mistake_lcats in enumerate(self.__project.events.segments[self.__segment_slug].mistakes_ts):
			mltts = self.__lcats_to_mltts(mistake_lcats)
			self.__add_marker_to_mlt(
				text = f'{I18n(self).markers.mistake.prefix}{i + 1}{I18n(self).markers.mistake.suffix}',
				start_mltts = mltts,
				end_mltts = mltts,
			)

	def __lcats_to_mltts (self, marker_ts: int) -> str:
		timeline_length = 0
		marker_offset = 0
		end = 0
		for entry in self.__mlt.getroot().findall('./playlist[@id="playlist0"]/entry'):
			start = LCAShotcutIntegration.mltts_to_lcats(entry.attrib['in'],  offset = self.__start_ts)
			end   = LCAShotcutIntegration.mltts_to_lcats(entry.attrib['out'], offset = self.__start_ts)
			if end > marker_ts:
				marker_offset = timeline_length + max(0, marker_ts - start)
				break
			timeline_length += end - start + int(1e6 / self.__framerate)
		else:
			marker_offset = timeline_length
		return LCAShotcutIntegration.lcats_to_mltts(marker_offset, framerate = self.__framerate)

	def __add_marker_to_mlt (self,
		text: str,
		start_mltts: str,
		end_mltts: str,
		color: str = '#FF6699',
	) -> None:
		MARKERS_PARENT = './tractor[@id="tractor0"]/properties[@name="shotcut:markers"]'
		if not len(self.__mlt.getroot().findall(MARKERS_PARENT)):
			self.__mlt.getroot().find('./tractor[@id="tractor0"]').append(
				xml.etree.ElementTree.Element(
					'properties',
					{'name': 'shotcut:markers'},
				)
			)
		marker = xml.etree.ElementTree.Element('properties', {'name': str(len(self.__mlt.getroot().findall(f'{MARKERS_PARENT}/*')))})
		text_el  = xml.etree.ElementTree.Element('property', {'name': 'text'})
		text_el.text = text
		marker.append(text_el)
		start_el = xml.etree.ElementTree.Element('property', {'name': 'start'})
		start_el.text = start_mltts
		marker.append(start_el)
		end_el   = xml.etree.ElementTree.Element('property', {'name': 'end'})
		end_el.text = end_mltts
		marker.append(end_el)
		color_el = xml.etree.ElementTree.Element('property', {'name': 'color'})
		color_el.text = color
		marker.append(color_el)
		self.__mlt.getroot().find(MARKERS_PARENT).append(marker)

	def __save_shotcut_file (self) -> None:
		self.__mlt.write(self.__project.path_shotcut(
			segment_id = self.__segment_id,
			segment_number = self.__segment_number,
		))

