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

import collections
import functools
import json
import time
import typing
import xml

import obsws_python

from loguru import logger

from PySide6.QtCore import *

from ...Settings import Settings

from ..LCAWorkerObject import LCAWorkerObject
from ...common.LCAProjectState import LCAProjectState
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...models.LCAProjectStateModel import LCAProjectStateModel
from ...integrations.obs.LCAObsIntegration import LCAObsIntegration
from ...integrations.shotcut.LCAShotcutIntegration import LCAShotcutIntegration

class LCARFinalRenderWorkerObject (LCAWorkerObject):

	task_started = Signal(str)
	task_success = Signal(str)
	task_failure = Signal(str)
	complete = Signal()

	__project: LCAProjectFileModel
	__obs: LCAObsIntegration
	__state_data: dict[typing.Annotated[str, 'Segment slug'], dict[typing.Annotated[int, 'microseconds'], LCAProjectStateModel]]

	def __init__ (self,
		project: LCAProjectFileModel,
	):
		self.__project = project
		self.__state_data = {}
		super().__init__()

	@Slot()
	def slot_construct (self) -> None:
		self.__wait_for_state_initialization()
		try:
			with LCAObsIntegration('video') as obs:
				self.__obs = obs
				self.__organize_project_state_data()
				self.__obs_inject_project_settings()
				self.__obs_create_scenes_from_templates()
				self.__obs_prepare_first_segment_video()
				self.__obs_remove_scenes()
		finally:
			self.__deinitialize_state()

	def tracked_task (fn):
		@functools.wraps(fn)
		def wrapper (self, *args, **kwargs):
			task_name = fn.__name__.lstrip('_')
			logger.debug(f'Task started: {task_name}')
			self.task_started.emit(task_name)
			try:
				ret = fn(self, *args, **kwargs)
				logger.debug(f'Task success: {task_name}')
				self.task_success.emit(task_name)
				return ret
			except:
				logger.error(f'Task failure: {task_name}')
				self.task_failure.emit(task_name)
				raise
		return wrapper

	@tracked_task
	def __wait_for_state_initialization (self) -> None:
		while True:
			try:
				LCAProjectState(self.__project)
				break
			except RuntimeError as e:
				time.sleep(2)

	@tracked_task
	def __organize_project_state_data (self) -> None:
		for segment_slug in self.__project.all_segment_slugs():
			if segment_slug != 'match-0001':
				continue
			logger.debug(f'Organizing project state data for segment {segment_slug}')
			elapsed_us_to_lcats = self.__build_elapsed_us_to_lcats(segment_slug)
			lcats_to_state = self.__build_lcats_to_state(
				list(elapsed_us_to_lcats.values())[ 0],
				list(elapsed_us_to_lcats.values())[-1],
			)
			self.__state_data[segment_slug] = self.__build_elapsed_us_to_state(elapsed_us_to_lcats, lcats_to_state)
			logger.warning(elapsed_us_to_lcats)
			logger.warning(lcats_to_state.keys())
			logger.warning(self.__state_data[segment_slug].keys())

	def __build_elapsed_us_to_lcats (self,
		segment_slug: str,
	) -> collections.OrderedDict[
		typing.Annotated[int, 'elapsed microseconds'],
		typing.Annotated[int, 'microseconds since epoch']
	]:
		ret = collections.OrderedDict()
		elapsed = 0
		mlt = xml.etree.ElementTree.parse(str(self.__project.path_shotcut(segment_slug = segment_slug).resolve()))
		for entry in mlt.getroot().findall('./playlist[@id="playlist0"]/entry'):
			start_lcats, end_lcats = (
				LCAShotcutIntegration.mltts_to_lcats(
					entry.attrib[attrib], offset = self.__project.events.segments[segment_slug].start_ts
				) for attrib in ('in', 'out')
			)
			ret[elapsed] = start_lcats
			elapsed += end_lcats - start_lcats + int(1e6 / LCAShotcutIntegration.get_framerate(mlt))
		penultimate_elapsed, penultimate_lcats = list(ret.items())[-1]
		ret[elapsed] = penultimate_lcats + elapsed - penultimate_elapsed
		return ret

	def __build_lcats_to_state (self,
		start_lcats: int,
		end_lcats: int,
	) -> collections.OrderedDict[
		typing.Annotated[int, 'microseconds since epoch'],
		LCAProjectStateModel | None
	]:
		ret = collections.OrderedDict()
		state_paths = self.__project.path_state_all()
		lcats_from_path = lambda path : int(path.stem.split('-')[-1])
		while lcats_from_path(state_paths[-1]) > end_lcats:
			state_paths.pop()
		try:
			while lcats_from_path(state_paths[1]) < start_lcats:
				state_paths.pop(0)
		except IndexError:
			if lcats_from_path(state_paths[0]) > start_lcats:
				raise
		with self.__project:
			for path in state_paths:
				ret[lcats_from_path(path)] = LCAProjectStateModel(
					**( json.loads(self.__project.read_file(path, text = True)) | {
						'project': self.__project,
						'music': {
							'artist': '',
							'title': '',
							'path': '',
						},
					} )
				)
		ret[9999999999999999] = None
		return ret

	def __build_elapsed_us_to_state (self,
		elapsed_us_to_lcats: collections.OrderedDict[
			typing.Annotated[int, 'elapsed microseconds'],
			typing.Annotated[int, 'microseconds since epoch']
		],
		lcats_to_state: collections.OrderedDict[
			typing.Annotated[int, 'microseconds since epoch'],
			LCAProjectStateModel | None
		],
	) -> collections.OrderedDict[
		typing.Annotated[int, 'elapsed microseconds'],
		LCAProjectStateModel
	]:

		def elapsed_to_lcats (elapsed: int) -> typing.Annotated[int, 'microseconds since epoch']:
			for elapsed_key, lcats_offset in reversed(list(elapsed_us_to_lcats.items())):
				if elapsed_key <= elapsed:
					return lcats_offset + (elapsed - elapsed_key)
			logger.error(elapsed_us_to_lcats)
			raise ValueError(f'Could not locate us-since-epoch for elapsed time {elapsed}')

		def lcats_to_state_lcats_key (true_lcats: int) -> typing.Annotated[int, 'microseconds since epoch']:
			for lcats_key in reversed(list(lcats_to_state.keys())):
				if lcats_key <= true_lcats:
					return lcats_key
			logger.error(elapsed_us_to_lcats)
			logger.error(lcats_to_state)
			raise ValueError(f'Could not locate state lcats key for us-since-epoch {true_lcats}')

		ret = collections.OrderedDict()
		elapsed = 0
		state_lcats_key = 0
		for clip_start_elapsed_us, clip_end_elapsed_us in zip(
			list(elapsed_us_to_lcats.keys())[ : -1 ],
			list(elapsed_us_to_lcats.keys())[ 1 :  ],
		):
			if (new_state_lcats_key := lcats_to_state_lcats_key(elapsed_to_lcats(clip_start_elapsed_us))) != state_lcats_key:
				state_lcats_key = new_state_lcats_key
				ret[elapsed] = lcats_to_state[state_lcats_key]
			clip_start_lcats = elapsed_us_to_lcats[clip_start_elapsed_us]
			offset_within_clip_us = 0
			while True:
				us_remaining_in_clip = clip_end_elapsed_us - (clip_start_elapsed_us + offset_within_clip_us)
				next_state_lcats_key = list(lcats_to_state.keys())[ list(lcats_to_state.keys()).index(state_lcats_key) + 1 ]
				us_until_next_state_change = next_state_lcats_key - (clip_start_lcats + offset_within_clip_us)
				if us_until_next_state_change >= us_remaining_in_clip:
					elapsed += us_remaining_in_clip
					break
				elapsed += us_until_next_state_change
				offset_within_clip_us += us_until_next_state_change
				state_lcats_key = next_state_lcats_key
				ret[elapsed] = lcats_to_state[state_lcats_key]
		return ret

	@tracked_task
	def __obs_inject_project_settings (self) -> None:
		recording_path = self.__project.path_rendered().resolve()
		self.__obs.req_client.set_profile_parameter('SimpleOutput', 'FilePath', str(recording_path.parent))
		self.__obs.req_client.set_profile_parameter('AdvOut', 'RecFilePath', str(recording_path.parent))
		self.__obs.req_client.set_profile_parameter('Output', 'FilenameFormatting', str(recording_path.parts[-1]).split('.')[0])

	@tracked_task
	def __obs_create_scenes_from_templates (self) -> None:
		for segment_id, segment_number in self.__project.all_segment_ids():
			segment_slug = LCAProjectFileModel.slug(segment_id, segment_number)
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
			self.__obs.req_client.set_current_program_scene(copy_scene_name)
			time.sleep(1)

	@tracked_task
	def __obs_prepare_first_segment_video (self) -> None:
		segment_slug = self.__project.all_segment_slugs()[0]
		segment_id, segment_number = LCAProjectFileModel.split_slug(segment_slug)
		segment = Settings().series_segment_from_id(self.__project.series_id, segment_id)
		scene_name = f'{segment.obs_scene_name} | {segment_slug}'
		input_name = f'{segment.recording_source_name} | {segment_slug}'
		self.__obs.req_client.set_current_program_scene(scene_name)
		self.__obs.req_client.trigger_media_input_action(input_name, 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART')
		time.sleep(1)
		self.__obs.req_client.trigger_media_input_action(input_name, 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE')
		time.sleep(1)
		self.__obs.req_client.set_media_input_cursor(input_name, 0)

	@tracked_task
	def __obs_remove_scenes (self) -> None:
		for segment_id, segment_number in self.__project.all_segment_ids():
			segment_slug = LCAProjectFileModel.slug(segment_id, segment_number)
			segment = Settings().series_segment_from_id(self.__project.series_id, segment_id)
			scene_name = f'{segment.obs_scene_name} | {segment_slug}'
			self.__obs.req_client.remove_scene(scene_name)

	def __deinitialize_state (self) -> None:
		LCAProjectState().shutdown()

