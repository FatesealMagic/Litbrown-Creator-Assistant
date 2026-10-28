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

import obsws_python

from loguru import logger

from PySide6.QtCore import *

from ...Settings import Settings

from ..LCAWorkerObject import LCAWorkerObject
from ...common.LCAProjectState import LCAProjectState
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...models.LCAProjectStateModel import LCAProjectStateModel
from ...integrations.obs.LCAObsIntegration import LCAObsIntegration

class LCARFinalRenderWorkerObject (LCAWorkerObject):

	task_started = Signal(str)
	task_success = Signal(str)
	task_failure = Signal(str)
	complete = Signal()

	__project: LCAProjectFileModel
	__obs: LCAObsIntegration

	def __init__ (self,
		project: LCAProjectFileModel,
	):
		self.__project = project
		super().__init__()

	@Slot()
	def slot_construct (self) -> None:
		self.__wait_for_state_initialization()
		try:
			with LCAObsIntegration('video') as obs:
				self.__obs = obs
				self.__create_scenes_from_templates()
		finally:
			self.__deinitialize_state()

	def __wait_for_state_initialization (self) -> None:
		self.task_started.emit('wait_for_state_initialization')
		while True:
			try:
				LCAProjectState(self.__project)
				break
			except RuntimeError as e:
				time.sleep(2)
		self.task_success.emit('wait_for_state_initialization')

	def __create_scenes_from_templates (self) -> None:
		self.task_started.emit('create_scenes_from_templates')
		for segment_id, segment_slug in self.__project.all_segment_ids():
			segment_slug = LCAProjectFileModel.slug(segment_id, segment_slug)
			segment = Settings().series_segment_from_id(self.__project.series_id, segment_id)
			orig_scene_name = segment.obs_scene_name
			copy_scene_name = f'{orig_scene_name} | {segment_slug}'
			self.__obs.req_client.create_scene(copy_scene_name)
			for scene_item in self.__obs.req_client.get_scene_item_list(orig_scene_name).scene_items:
				orig_source_name = segment.recording_source_name
				if orig_source_name == scene_item['sourceName']:
					copy_source_name = f'{orig_source_name} | {segment_slug}'
					self.__obs.req_client.create_input(
						sceneName = copy_scene_name,
						inputName = copy_source_name,
						inputKind = 'ffmpeg_source',
						inputSettings = self.__obs.req_client.get_input_settings(segment.recording_source_name).input_settings | {
							'local_file': str(self.__project.path_rendered(segment_slug = segment_slug).resolve()),
						},
						sceneItemEnabled = True,
					)
					orig_transform = self.__obs.req_client.get_scene_item_transform(
						scene_name = orig_scene_name,
						item_id = self.__obs.req_client.get_scene_item_id(
							scene_name = orig_scene_name,
							source_name = orig_source_name,
						).scene_item_id,
					).scene_item_transform
					orig_transform['boundsWidth']  = orig_transform['boundsWidth']  or 1.0
					orig_transform['boundsHeight'] = orig_transform['boundsHeight'] or 1.0
					self.__obs.req_client.set_scene_item_transform(
						scene_name = copy_scene_name,
						item_id = self.__obs.req_client.get_scene_item_id(
							scene_name = copy_scene_name,
							source_name = copy_source_name,
						).scene_item_id,
						transform = orig_transform,
					)
					for filter in self.__obs.req_client.get_source_filter_list(orig_source_name).filters:
						if not filter['filterEnabled']:
							continue
						self.__obs.req_client.create_source_filter(
							source_name = copy_source_name,
							filter_name = f'{filter['filterName']} | {segment_slug}',
							filter_kind = filter['filterKind'],
							filter_settings = filter['filterSettings'],
						)
				else:
					self.__obs.req_client.duplicate_scene_item(
						scene_name = orig_scene_name,
						item_id = scene_item['sceneItemId'],
						dest_scene_name = copy_scene_name,
					)
		self.task_success.emit('create_scenes_from_templates')

	def __deinitialize_state (self) -> None:
		LCAProjectState().shutdown()

