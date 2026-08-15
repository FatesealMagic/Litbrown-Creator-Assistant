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

import contextlib
import filelock
import json
import textwrap
import threading
import time
import traceback
import typing

from loguru import logger
import deepmerge
import pydantic
import yaml

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .Util import *

from .models.LCAIntegrationSafeTextValidator import *
from .models.LCAScryfallCardModel import *

# Model ########################################################################
	
class _SettingsModel (pydantic.BaseModel, validate_assignment = True):
	
	class AffiliatesModel (pydantic.BaseModel, validate_assignment = True):
		
		class AffiliateModel (pydantic.BaseModel, validate_assignment = True):
			code: str = ''
		manapool:      AffiliateModel = AffiliateModel()
		cardhoarder:   AffiliateModel = AffiliateModel()
		cardkingdom:   AffiliateModel = AffiliateModel()
		starcitygames: AffiliateModel = AffiliateModel()
		toamagic:      AffiliateModel = AffiliateModel()
		
	affiliates: AffiliatesModel = AffiliatesModel()
	
	class SeriesModel (pydantic.BaseModel, validate_assignment = True):
		id: str = 'newseries'
		name: str = 'New Series'
		
		stream_duration: int = 180
		
		class OutputTypeModel (pydantic.BaseModel, validate_assignment = True):
			decklist_template: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator())]
			decklist_separator: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator())]
			description_template: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator())]
			enabled: bool
			publish_to_membership_id: str
			title_template: typing.Annotated[str, pydantic.AfterValidator(LCAIntegrationSafeTextValidator())]
		stream: OutputTypeModel = OutputTypeModel(
			decklist_template = '''
				${decklist_name}
				Link to decklist: ${decklist_link}
				'''.strip().replace('\t', ''),
			decklist_separator = '\n----------\n',
			description_template = '''
				${description_hook}

				Decklists used in this video:

				${decklists}
				'''.strip().replace('\t', ''),
			enabled = True,
			publish_to_membership_id = '~public',
			title_template = '${title_hook} ${series_hashtags} ${variant_hashtags}' )
		video: OutputTypeModel = OutputTypeModel(
			decklist_template = '''
				${decklist_name}
				Link to decklist: ${decklist_link}
				Buy on Mana Pool: ${manapool_link}
				${decklist}
				'''.strip().replace('\t', ''),
			decklist_separator = '\n\n--------------------\n\n',
			description_template = '''
				${description_hook}

				Decklists used in this video:

				${decklists}

				This content was streamed on ${stream_date}
				'''.strip().replace('\t', ''),
			enabled = True,
			publish_to_membership_id = '~public',
			title_template = '${title_hook} | ${series_name} #${entry_number}: ${variant_name} in ${mtg_format}' )
		clip: OutputTypeModel = OutputTypeModel(
			decklist_template = '''
				${decklist_link}
				'''.strip().replace('\t', ''),
			decklist_separator = '\n',
			description_template = '''
				${description_hook}

				Decklists used in this video:

				${decklists}
				'''.strip().replace('\t', ''),
			enabled = False,
			publish_to_membership_id = '~public',
			title_template = '${title_hook} | ${series_name} #${entry_number}: ${variant_name} in ${mtg_format}' )

		class VariantModel (pydantic.BaseModel, validate_assignment = True):
			description: str = ''
			id: str = 'newvariant'
			mtgformat: str = ''
			name: str = 'New Variant'
		variants: list[VariantModel] = []

		class SegmentModel (pydantic.BaseModel, validate_assignment = True):
			id: str
			name: str
			obs_scene_name: str = ''
			timestamp_template: str = '${timestamp} ${segment_name}'
			repeatable: bool = False
			# TODO implement ad reads, link here, account for pluralability
		segments: list[SegmentModel] = []
		
	series: list[SeriesModel] = []

	class IntegrationsModel (pydantic.BaseModel, validate_assignment = True):
		
		class MoxfieldIntegrationModel (pydantic.BaseModel, validate_assignment = True):
			user_agent: str = ''
		moxfield: MoxfieldIntegrationModel = MoxfieldIntegrationModel()
		
		class MymtgoIntegrationModel (pydantic.BaseModel, validate_assignment = True):
			accounts: list[str] = []
		mymtgo: MymtgoIntegrationModel = MymtgoIntegrationModel()

		class ObsIntegrationModel (pydantic.BaseModel, validate_assignment = True):
			class ObsInstanceIntegrationModel (pydantic.BaseModel, validate_assignment = True):
				host: str = '127.0.0.1'
				port: int = 4455
				pswd: str = ''
			record: ObsInstanceIntegrationModel = ObsInstanceIntegrationModel(port = 4444)
			stream: ObsInstanceIntegrationModel = ObsInstanceIntegrationModel()
			video: ObsInstanceIntegrationModel = ObsInstanceIntegrationModel()
			clip: ObsInstanceIntegrationModel = ObsInstanceIntegrationModel()
		obs: ObsIntegrationModel = ObsIntegrationModel()

		class RemoteIntegrationModel (pydantic.BaseModel, validate_assignment = True):
			remote_id: str = ''
			handle: str = ''
			display_name: str = ''
			profile_pic_url: str = ''
			auth: dict | None = None
			
			class RemoteMembershipTierModel (pydantic.BaseModel, validate_assignment = True):
				remote_id: str
				remote_name: str
				cents: int
			remote_membership_tiers: list[RemoteMembershipTierModel] = []
			
			def reset (self) -> None:
				for attr, _ in self:
					v = ''
					if attr in ['auth']:
						v = {}
					if attr in ['remote_membership_tiers']:
						v = []
					setattr(self, attr, v)

		youtube: RemoteIntegrationModel = RemoteIntegrationModel()
		twitch: RemoteIntegrationModel = RemoteIntegrationModel()
		patreon: RemoteIntegrationModel = RemoteIntegrationModel()

	integrations: IntegrationsModel = IntegrationsModel()

	class MembershipTierModel (pydantic.BaseModel, validate_assignment = True):
		id: str
		name: str
		
		class RemoteIdsModel (pydantic.BaseModel, validate_assignment = True):
			youtube: str | None = None
			twitch: str | None = None
			patreon: str | None = None
		remote_ids: RemoteIdsModel = RemoteIdsModel()

	membership_tiers: list[MembershipTierModel] = []

	class ToolsModel (pydantic.BaseModel, validate_assignment = True):
		
		class ToolsGeneralModel (pydantic.BaseModel, validate_assignment = True):
			language: str = 'en-US'
			projects_location: str = 'projects'
			www_directory: str = 'www'
			time_display_format: str = 'h:mm AP'
			accent_hue: int = 300
		general: ToolsGeneralModel = ToolsGeneralModel()

		class ToolsScheduleModel (pydantic.BaseModel, validate_assignment = True):
			output_file: str = 'schedule.png'
			render_file: str = 'schedule.html'
			render_function: str = 'process_data'
		schedule: ToolsScheduleModel = ToolsScheduleModel()

		class ToolsThumbnailModel (pydantic.BaseModel, validate_assignment = True):
			render_file: str = 'thumbnail.html'
			render_func: str = 'new_data_update'
			
			class ToolsThumbnailProfileModel (pydantic.BaseModel, validate_assignment = True):
				name: str = ''
			
				class ToolsThumbnailControlBaseModel (pydantic.BaseModel, validate_assignment = True):
					input_type: str
					name: str
				class ToolsThumbnailControlTextModel (ToolsThumbnailControlBaseModel):
					input_type: typing.Literal['text'] = 'text'
					default: str = ''
				class ToolsThumbnailControlNumberModel (ToolsThumbnailControlBaseModel):
					input_type: typing.Literal['number'] = 'number'
					minimum: int = 0
					maximum: int = 99
					default: int = 0
				class ToolsThumbnailControlComboModel (ToolsThumbnailControlBaseModel):
					input_type: typing.Literal['combo'] = 'combo'
					options: list[str] = []
				class ToolsThumbnailControlCheckboxModel (ToolsThumbnailControlBaseModel):
					input_type: typing.Literal['checkbox'] = 'checkbox'
				class ToolsThumbnailControlSeparatorModel (ToolsThumbnailControlBaseModel):
					input_type: typing.Literal['separator'] = 'separator'
				class ToolsThumbnailControlMagicCardSelectorModel (ToolsThumbnailControlBaseModel):
					input_type: typing.Literal['mtgcard'] = 'mtgcard'
				controls: list[typing.Annotated[ typing.Union[
						ToolsThumbnailControlTextModel,
						ToolsThumbnailControlNumberModel,
						ToolsThumbnailControlComboModel,
						ToolsThumbnailControlCheckboxModel,
						ToolsThumbnailControlSeparatorModel,
						ToolsThumbnailControlMagicCardSelectorModel,
					], pydantic.Field(discriminator = 'input_type')
				]] = []
			
			profiles: list[ToolsThumbnailProfileModel] = [ ToolsThumbnailProfileModel(
				name = 'Default Profile',
				controls = [
					ToolsThumbnailProfileModel.ToolsThumbnailControlTextModel(
						name = 'Splash Text',
						default = 'What a cool deck!',
					),
					ToolsThumbnailProfileModel.ToolsThumbnailControlNumberModel(
						name = 'Hue',
						minimum = 0,
						maximum = 359,
						default = 30,
					),
					ToolsThumbnailProfileModel.ToolsThumbnailControlSeparatorModel(
						name = 'Cards',
					),
					ToolsThumbnailProfileModel.ToolsThumbnailControlMagicCardSelectorModel(
						name = 'Left Card',
					),
					ToolsThumbnailProfileModel.ToolsThumbnailControlMagicCardSelectorModel(
						name = 'Center Card',
					),
					ToolsThumbnailProfileModel.ToolsThumbnailControlMagicCardSelectorModel(
						name = 'Right Card',
					),
				],
			) ]
		
		thumbnail: ToolsThumbnailModel = ToolsThumbnailModel()

	tools: ToolsModel = ToolsModel()
	
# Implementation ###############################################################

	class _SettingsSignals (QObject):
		changed = Signal()

	_SETTINGS_FILENAME: typing.ClassVar[str] = 'settings.json'
	_SETTINGS_LOCKNAME: typing.ClassVar[str] = 'settings.json.lock'

	_raw: typing.ClassVar[str] = ''
	_instance: typing.ClassVar[typing.Self | None] = None
	_filelock: typing.ClassVar[filelock.FileLock] = filelock.FileLock(_SETTINGS_LOCKNAME)
	_filelocklock: typing.ClassVar[threading.Lock] = threading.Lock()
	_filewatcher: typing.ClassVar[QFileSystemWatcher] = QFileSystemWatcher([_SETTINGS_FILENAME])
	_signals: typing.ClassVar[_SettingsSignals] = _SettingsSignals()
	
	def model_post_init (self, __context) -> None:
		try:
			self._filewatcher.fileChanged.disconnect(self._reload)
		except RuntimeWarning:
			pass
		self._filewatcher.fileChanged.connect(self._reload)

	@classmethod
	def _reload (cls) -> typing.Self:
		data = cls._load_data()
		if data is None:
			return
		logger.debug('\n' + ''.join(traceback.format_stack()))
		logger.debug(data)
		cls._instance = cls(**data)
		cls._signals.changed.emit()
		return cls._instance

	@classmethod
	def _load_data (cls, path: str | None = None) -> dict | None:
		try:
			with filelock.FileLock(cls._SETTINGS_LOCKNAME), open(cls._SETTINGS_FILENAME, encoding='utf-8') as f:
				raw = f.read()
			if not raw:
				return {}
			if raw == cls._raw:
				return None
			cls._raw = raw
			return json.loads(raw)
		except (FileNotFoundError,):
			return {}
		except json.JSONDecodeError as e:
			if e.pos != 0:
				raise
			return {}

	def __enter__ (self):
		self._filelocklock.acquire()
		self._filewatcher.removePath(self._SETTINGS_FILENAME)
		self._filelock.acquire()
		logger.debug('filelock acquired')

	def __exit__ (self, exc_type, exc_val, exc_tb):
		self._save()
		self._filelock.release()
		logger.debug('filelock released')
		self._filewatcher.addPath(self._SETTINGS_FILENAME)
		self._filelocklock.release()
		self._signals.changed.emit()
		return False

	def _save (self) -> None:
		dump = self.model_dump_json()
		logger.debug('\n' + ''.join(traceback.format_stack()))
		logger.debug(dump)
		with open(self._SETTINGS_FILENAME, 'w', encoding='utf-8') as f:
			f.write(dump)

	@classmethod
	def signals (cls) -> _SettingsSignals:
		return cls._signals

	@staticmethod
	def series_from_id (id: str) -> SeriesModel:
		for s in Settings().series:
			if s.id == id:
				return s
		raise ValueError(f'Could not find series with id {id}')

	@staticmethod
	def series_variant_from_id (s: SeriesModel | str, id: str) -> SeriesModel.VariantModel:
		if type(s) is str:
			s = Settings().series_from_id(s)
		for v in s.variants:
			if v.id == id:
				return v
		raise ValueError(f'Could not find variant with id {id} in series {s.id}')

	@staticmethod
	def membership_tier_from_id (id: str) -> MembershipTierModel:
		for t in Settings().membership_tiers:
			if t.id == id:
				return t
		raise ValueError(f'Could not find membership tier with id {id}')

	@staticmethod
	def get (path: str) -> typing.Any:
		props = path.split('.')
		ref = Settings()
		while props:
			p = props.pop(0)
			ref = getattr(ref, p)
		return ref

	@staticmethod
	def set (path: str, val: typing.Any) -> None:
		with Settings():
			props = path.split('.')
			ref = Settings()
			while len(props) > 1:
				p = props.pop(0)
				ref = getattr(ref, p)
			setattr(ref, props.pop(0), val)

	@staticmethod
	def bind (widget: QWidget, path: str) -> None:
		user_prop = widget.metaObject().userProperty()
		widget.setProperty(user_prop.name(), Settings().get(path))
		Settings().signals().changed.connect(
			lambda : widget.setProperty(user_prop.name(), Settings().get(path)) \
				if widget.property(user_prop.name()) != Settings().get(path) else logger.debug('skipping settings -> widget')
		)
		getattr(widget, str(user_prop.notifySignal().methodSignature().split('(')[0], 'utf-8')).connect(
			lambda v : Settings().set(path, v) if v != Settings().get(path) else logger.debug('skipping widget -> settings')
		)

_SettingsModel._reload()

def Settings () -> _SettingsModel:
	return _SettingsModel._instance

