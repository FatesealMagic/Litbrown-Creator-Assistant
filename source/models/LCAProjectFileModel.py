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

import base64
import datetime
import pathlib
import re
import threading
import typing
import urllib

from loguru import logger
import pydantic

from ..Config import *
from ..Settings import *

from .LCADecklistModel import *
from .LCAScryfallCardModel import *
from .LCAIntegrationSafeTextValidator import *
from ..common.LCATextTemplate import *

# Model ########################################################################

class LCAProjectFileModel (pydantic.BaseModel, validate_assignment = True):
	
	series_id: str
	entry_number: int
	variant_id: str = ''
	mtg_format: str = ''
	
	decklists: list[LCADecklistModel] = []

	class StreamModel (pydantic.BaseModel, validate_assignment = True):
		start: str = ''
		membertier_id: str = ''
		title_hook: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator())] = ''
		description_hook: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator())] = ''
		thumbnail: pathlib.Path | None = None
		full_title: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator(max_len = 100))] = ''
		full_description: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator(max_len = 5000))] = ''
		
		class RemoteIdsModel (pydantic.BaseModel, validate_assignment = True):
			youtube: str = ''
			twitch: str = ''
			patreon: str = ''
		remote_ids: RemoteIdsModel = RemoteIdsModel()

	stream: StreamModel = StreamModel()
	
	class VideoModel (pydantic.BaseModel, validate_assignment = True):
		thumbnail: pathlib.Path | None = None
	video: VideoModel = VideoModel()

# Implementation ###############################################################

	_fullpath: pathlib.Path = pydantic.PrivateAttr()
	_filelock: filelock.FileLock = pydantic.PrivateAttr()
	_filelocklock: threading.Lock = pydantic.PrivateAttr()

	def model_post_init (self, __context) -> None:
		logger.debug('project file model_post_init')
		self._fullpath = self.get_fullpath(self.series_id, self.entry_number)
		self._filelock = self.get_filelock(self.series_id, self.entry_number)
		self._filelocklock = threading.Lock()

	def __enter__ (self):
		logger.debug(dir(self))
		self._filelocklock.acquire()
		self._filelock.acquire()

	def __exit__ (self, exc_type, exc_val, exc_tb):
		self._save()
		self._filelock.release()
		self._filelocklock.release()
		return False

	def _save (self) -> None:
		dump = self.model_dump_json()
		logger.debug('\n' + ''.join(traceback.format_stack()))
		logger.debug(dump)
		self._fullpath.parent.mkdir(parents = True, exist_ok = True)
		with open(self._fullpath, 'w', encoding='utf-8') as f:
			f.write(dump)

	def mutex (self) -> threading.Lock:
		return self._filelocklock

	@classmethod
	def get_fullpath (cls, slug_or_series_id: str, entry_number: int | str | None = None) -> pathlib.Path:
		slug = cls.create_slug(slug_or_series_id, entry_number)
		return pathlib.Path(Settings().tools.general.projects_location) / pathlib.Path(f'{slug}/{slug}.lca')

	@classmethod
	def get_filelock (cls, slug_or_series_id: str, entry_number: int | str | None = None) -> filelock.FileLock:
		return filelock.FileLock(str(cls.get_fullpath(slug_or_series_id, entry_number)) + '.lock')

	@classmethod
	def load (cls, slug_or_series_id: str, entry_number: int | str | None = None) -> typing.Self | None:
		if not slug_or_series_id:
			return None
		slug = cls.create_slug(slug_or_series_id, entry_number)
		series_id, entry_number = cls.create_id(slug)
		fullpath = cls.get_fullpath(slug)
		filelock = cls.get_filelock(slug)
		try:
			import time
			with filelock, open(fullpath, encoding='utf-8') as f:
				data = json.loads(f.read()) or {}
		except (FileNotFoundError,):
			return None
		except json.JSONDecodeError as e:
			if e.pos == 0:
				data = {}
			else:
				raise
		return cls(**data)
	
	@classmethod
	def create_id (cls, slug_or_series_id: str, entry_number: int | str | None = None) -> tuple[str, int]:
		if entry_number is None:
			match = re.match(Config().project.slug_regex, slug_or_series_id)
			if not match:
				raise ValueError(f'Invalid slug received: {slug_or_series_id}')
			return (match.group(1), int(match.group(2)))
		else:
			return (slug_or_series_id, entry_number)

	@classmethod
	def create_slug (cls, slug_or_series_id: str, entry_number: int | str | None = None) -> str:
		if not slug_or_series_id:
			raise ValueError(f'create_slug called with falsey slug/series {slug_or_series_id}')
		return slug_or_series_id if entry_number is None else f'{slug_or_series_id}-{int(entry_number):04d}'

	def get_slug (self) -> str:
		return self.create_slug(self.series_id, self.entry_number)

	@classmethod
	def find_all_slugs (cls) -> list[str]:
		ret = []
		projects_location = pathlib.Path(Settings().tools.general.projects_location)
		projects_location.mkdir(parents = True, exist_ok = True)
		for child in projects_location.iterdir():
			if not child.is_dir() or not re.match(Config().project.slug_regex, child.name):
				continue
			for subchild in child.iterdir():
				if subchild.name == f'{child.name}.lca':
					ret.append(child.stem)
		return ret

	@classmethod
	def find_all_ids (cls) -> list[tuple[str, int]]:
		return [ cls.create_id(slug) for slug in cls.find_all_slugs() ]

	def generate_stream_texts (self) -> None:
		decklists = self.__generate_decklists_text('stream')
		substitutions = {
			'decklists': decklists,
			'description_hook': self.stream.description_hook,
			'entry_number': self.entry_number,
			'mtg_format': self.mtg_format,
			'series_name': Settings().series_from_id(self.series_id).name,
			'stream_date': self.stream.start,
			'title_hook': self.stream.title_hook,
			'variant_description': Settings().series_variant_from_id(self.series_id, self.variant_id).description \
				if self.variant_id else '',
			'variant_name': Settings().series_variant_from_id(self.series_id, self.variant_id).name \
				if self.variant_id else '',
		}
		self.stream.full_title = LCATextTemplate(
			Settings().series_from_id(self.series_id).stream.title_template,
			LCATextTemplate.VariableGroup.STREAM,
		).substitute(substitutions)
		self.stream.full_description = LCATextTemplate(
			Settings().series_from_id(self.series_id).stream.description_template,
			LCATextTemplate.VariableGroup.STREAM,
		).substitute(substitutions)

	def __generate_decklists_text (self, key: str) -> str:
		return getattr(Settings().series_from_id(self.series_id), key).decklist_separator.join([ LCATextTemplate(
			getattr(Settings().series_from_id(self.series_id), key).decklist_template,
			LCATextTemplate.VariableGroup.DECKLISTS,
		).substitute(
			decklist = self.__decklist_to_text(decklist),
			decklist_link = decklist.url or '',
			decklist_name = decklist.title or '',
			manapool_link = self.__decklist_to_manapool_link(decklist),
		) for decklist in self.decklists ])

	@staticmethod
	def __decklist_to_text (decklist: LCADecklistModel) -> str:
		return '\n\n'.join([
			'\n'.join([
				f'- {card.lca_quantity} {card.name}'
				for card in sorted(getattr(decklist.boards, board_name, []), key = lambda card : card.name)
				if card.lca_quantity
			])
			for board_name in ('command', 'companion', 'mainboard', 'sideboard')
			if getattr(decklist.boards, board_name, [])
		])

	@staticmethod
	def __decklist_to_manapool_link (decklist: LCADecklistModel) -> str:
		return f'https://manapool.com/add-deck?{
			f'ref={Settings().affiliates.manapool.code}&' if Settings().affiliates.manapool.code else ''
		}deck={
			urllib.parse.quote(base64.b64encode(bytes( '\n'.join([
				'\n'.join([
					f'{card.lca_quantity} {card.name}'
					for card in getattr(decklist.boards, board_name, [])
					if card.lca_quantity
				])
				for board_name in ('command', 'companion', 'mainboard', 'sideboard')
				if getattr(decklist.boards, board_name, [])
			]), 'utf-8' )).decode('utf-8'))
		}'

	def __load_file (self, file: str, mode: str, encoding: str | None) -> bytes | str | None:
		try:
			with open(pathlib.Path(
				f'{Settings().tools.general.projects_location}/{self.get_slug()}/{self.get_slug()}-{file}'
			), mode, encoding = encoding) as f:
				return fp.read()
		except FileNotFoundError:
			return None

	def load_file_binary (self, file: str) -> bytes | None:
		return self.__get_file(file, 'rb', None)

	def load_file_text (self, file: str) -> str | None:
		return self.__get_file(file, 'r', 'utf-8')

	def __save_file (self, file: str, contents: bytes | str, mode: str, encoding: str | None) -> None:
		with open(pathlib.Path(
			f'{Settings().tools.general.projects_location}/{self.get_slug()}/{self.get_slug()}-{file}'
		), mode, encoding = encoding) as f:
			f.write(contents)

	def save_file_binary (self, file: str, contents: bytes) -> None:
		return self.__save_file(file, contents, 'wb', None)

	def save_file_text (self, file: str, contents: str) -> None:
		return self.__save_file(file, contents, 'w', 'utf-8')

	def update_thumbnail_path (self, format: str) -> tuple[pathlib.Path | None, str]:
		if format not in ('stream', 'video'):
			raise ValueError(f'Invalid format passed: {format}')
		thumbnail_path, thumbnail_type = (None, None)
		if (path := self.get_thumbnail_path(
			format = format,
			slug = self.get_slug(),
		)).is_file():
			thumbnail_path, thumbnail_type = (path, 'multicast')
		elif self.variant_id and (path := self.get_thumbnail_path(
			format = format,
			series_id = self.series_id,
			variant_id = self.variant_id,
		)).is_file():
			thumbnail_path, thumbnail_type = (path, 'variant')
		elif (path := self.get_thumbnail_path(
			format = format,
			series_id = self.series_id,
		)).is_file():
			thumbnail_path, thumbnail_type = (path, 'series')
		elif (path := self.get_thumbnail_path(
			format = format,
		)).is_file():
			thumbnail_path, thumbnail_type = (path, 'channel')
		if getattr(self, format).thumbnail != thumbnail_path:
			with self:
				getattr(self, format).thumbnail = thumbnail_path
		return (thumbnail_path, thumbnail_type)

	@classmethod
	def get_thumbnail_path (cls, /,
		format: str,
		slug: str | None = None,
		series_id: str | None = None,
		variant_id: str | None = None,
	) -> pathlib.Path:
		if format not in ('stream', 'video'):
			raise ValueError(f'Invalid format passed: {format}')
		if slug:
			# multicast
			filename = f'{slug}/{slug}-'
		elif series_id and variant_id:
			# variant
			filename = f'{series_id}/{variant_id}/'
		elif series_id:
			# series
			filename = f'{series_id}/'
		else:
			# channel
			filename = ''
		return pathlib.Path(
			f'{Settings().tools.general.projects_location}/' +
				f'{filename}{I18n(cls).thumbnail.filename.thumbnail}-{getattr(I18n(cls).thumbnail.filename, format)}.png'
		)

