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
import time
import typing
import urllib

from loguru import logger
import pydantic

from ..Config import *
from ..Settings import *

from .LCADecklistModel import *
from .LCAScryfallCardModel import *
from .LCAIntegrationSafeTextValidator import *
from ..common.LCAFileOverwriter import *
from ..common.LCAHybridMethod import *
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

	model_config = pydantic.ConfigDict(
		ignored_types = (LCAHybridMethod,),
	)

	_fullpath: pathlib.Path = pydantic.PrivateAttr()
	_filelock: filelock.FileLock = pydantic.PrivateAttr()
	_filelocklock: threading.Lock = pydantic.PrivateAttr()

	def model_post_init (self, __context) -> None:
		logger.debug('project file model_post_init')
		self._fullpath = self.path()
		self._filelock = self.filelock()
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
		self._fullpath.parent.mkdir(parents = True, exist_ok = True)
		with open(self._fullpath, 'w', encoding='utf-8') as f:
			f.write(dump)

	def mutex (self) -> threading.Lock:
		return self._filelocklock

	@classmethod
	def from_slug (cls,
		slug: str,
		/,
	) -> typing.Self | None:
		if not slug:
			return None
		fullpath = cls.path(slug)
		filelock = cls.filelock(slug)
		try:
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

	@LCAHybridMethod
	def slug (obj,
		series_id: str | None = None,
		entry_number: int | None = None,
		/,
	) -> str:
		if not isinstance(obj, type) and (self := obj):
			series_id = self.series_id
			entry_number = self.entry_number
		return f'{series_id}-{entry_number:04}'

	@LCAHybridMethod
	def split_slug (obj,
		slug: str | None = None,
		/,
	) -> tuple[str, int]:
		if not isinstance(obj, type) and (self := obj):
			slug = self.slug()
		match = re.match(Config().project.slug_regex, slug)
		if not match:
			raise ValueError(f'Invalid slug received: {slug}')
		return (str(match.group(1)), int(match.group(2)))

	@LCAHybridMethod
	def path (obj,
		filename_or_slug: str | None = None,
		filename: str | None = None,
		/,
	) -> pathlib.Path:
		if isinstance(obj, type) and (cls := obj):
			slug = filename_or_slug
		elif self := obj:
			slug = self.slug()
			filename = filename_or_slug
		filename = filename or '.lca'
		if slug in str(filename):
			return pathlib.Path(filename)
		filename = ('' if filename[0] == '.' else '-') + filename
		return pathlib.Path(Settings().tools.general.projects_location) / pathlib.Path(f'{slug}/{slug}{filename}')

	@LCAHybridMethod
	def path_footage (obj,
		slug: str | None = None,
		/, *,
		segment_id: str,
		segment_number: int | None = None,
	) -> pathlib.Path:
		filename = f'footage-{segment_id}'
		if segment_number:
			filename += f'-{segment_number:04}'
		filename += '.mkv'
		if isinstance(obj, type) and (cls := obj):
			return cls.path(slug, filename)
		elif self := obj:
			return self.path(filename)

	@LCAHybridMethod
	def path_state (obj,
		slug: str | None = None,
		/, *,
		ms: int | str | None = None,
	) -> pathlib.Path:
		if ms is None:
			ms = time.time() * 1000
		ms = int(ms)
		filename = f'~state-{ms}.json'
		if isinstance(obj, type) and (cls := obj):
			return cls.path(slug, filename)
		elif self := obj:
			return self.path(filename)

	@LCAHybridMethod
	def path_state_all (obj,
		slug: str | None = None,
		/,
	) -> list[pathlib.Path]:
		if not isinstance(obj, type) and (self := obj):
			slug = self.slug()
		project_directory = pathlib.Path(Settings().tools.general.projects_location) / pathlib.Path(slug)
		return sorted(list(project_directory.glob(f'{slug}-~state-*.json')))

	@LCAHybridMethod
	def filename (obj,
		slug_or_path: str | pathlib.Path,
		path: str | pathlib.Path | None = None,
	) -> str:
		if isinstance(obj, type) and (cls := obj):
			slug = str(slug_or_path)
			path = pathlib.Path(path).as_posix()
		elif self := obj:
			slug = self.slug()
			path = pathlib.Path(slug_or_path).as_posix()
		filename = pathlib.Path(pathlib.Path(path).as_posix().split(f'{slug}/{slug}')[-1])
		if filename[0] == '-':
			filename = filename[1:]
		return filename

	@LCAHybridMethod
	def filelock (obj,
		slug: str | None = None,
		/,
	) -> filelock.FileLock:
		if isinstance(obj, type) and (cls := obj):
			path = cls.path(slug, '.lock')
		elif self := obj:
			path = self.path('.lock')
		return filelock.FileLock(str(path))

	@classmethod
	def get_existing_slugs (cls) -> list[str]:
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
	def get_existing_slugs_split (cls) -> list[tuple[str, int]]:
		return [ cls.split_slug(slug) for slug in cls.get_existing_slugs() ]

	# TODO clean this up
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

	# TODO clean this up
	@classmethod
	def get_thumbnail_path (cls, *,
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

	def read_file (self,
		filename: str | pathlib.Path,
		/, *,
		text: bool = False,
		binary: bool = False,
	) -> bytes | str | None:
		if not (text ^ binary):
			raise ValueError(f'Need one of text {text} or binary {binary} to be true, not both or neither')
		try:
			with self, open( self.path(filename), 'r' if text else 'rb', encoding = 'utf-8' if text else None ) as f:
				return f.read()
		except FileNotFoundError:
			return None

	def overwrite_file (self,
		filename: str,
		contents: bytes | str,
		/, *,
		text: bool = False,
		binary: bool = False,
	) -> None:
		with self, LCAFileOverwriter( self.path(filename), binary = binary, text = text ) as f:
			f.write(contents)

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

