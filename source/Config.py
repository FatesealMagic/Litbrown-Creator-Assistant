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

import typing
import uuid

import pydantic

from .Util import *

class _ConfigModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
	disallowed_filename_characters_regex: str = r'[\x00-\x1F\x7F<>:"/\\|?*. -]'
	
	class IntegrationsModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
		
		class RemoteModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
			oauth_service_url: str = 'https://us-central1-lca-mtgo.cloudfunctions.net/microservice/oauth'
			
			class OauthModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
				api_url_base: str
				client_id: str
				disallowed_characters: str
				oauth_url: str

			# bluesky
			
			# discord
			
			patreon: OauthModel = OauthModel(
				api_url_base = 'https://www.patreon.com/api/oauth2/v2/',
				client_id = 'fevqUu5YFS3rBLG4JyGzU7ufYNsqbAoZdBtkLbXueudB07cMHWUOzavWgc66DCI-',
				disallowed_characters = '',
				oauth_url = 'https://www.patreon.com/oauth2/authorize' +
					'?response_type=code' +
					'&client_id=fevqUu5YFS3rBLG4JyGzU7ufYNsqbAoZdBtkLbXueudB07cMHWUOzavWgc66DCI-' +
					'&redirect_uri=http://localhost:42967/-/oauth/patreon' +
					'&scope=identity%20campaigns%20w:campaigns.lives%20campaigns.members%20campaigns.posts',
			)

			# reddit
			
			twitch: OauthModel = OauthModel(
				api_url_base = 'https://api.twitch.tv/helix/',
				client_id = 'vq4jarcjef1f33h30bq5nhzb33hayd',
				oauth_url = 'https://id.twitch.tv/oauth2/authorize' +
					'?response_type=code' +
					'&client_id=vq4jarcjef1f33h30bq5nhzb33hayd' +
					'&force_verify=true' +
					'&redirect_uri=http://localhost:42967/-/oauth/twitch' +
					'&scope' +
						'=channel%3Amanage%3Aads' +
						'+channel%3Amanage%3Abroadcast' +
						'+channel%3Aedit%3Acommercial' +
						'+channel%3Amanage%3Araids' +
						'+channel%3Amanage%3Aschedule' +
						'+channel%3Aread%3Asubscriptions',
				disallowed_characters = '',
			)
			
			# twitter
		
			youtube: OauthModel = OauthModel(
				api_url_base = '',
				client_id = '144186256573-na8dmu2r46jd6fd9r38f8cu9u7iq8fgt.apps.googleusercontent.com',
				disallowed_characters = '<>',
				oauth_url = 'https://accounts.google.com/o/oauth2/v2/auth' +
					'?client_id=144186256573-na8dmu2r46jd6fd9r38f8cu9u7iq8fgt.apps.googleusercontent.com' +
					'&redirect_uri=http://localhost:42967/-/oauth/youtube' +
					'&response_type=code' +
					'&scope' +
						  '=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube' +
						'%20https://www.googleapis.com/auth/youtube.channel-memberships.creator' +
					'&access_type=offline' +
					'&prompt=consent',
			)
		
		remote: RemoteModel = RemoteModel()

		class LocalModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):

			class ObsModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
				pass
			obs: ObsModel = ObsModel()
			
			class ShotcutModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
				pass
			shotcut: ShotcutModel = ShotcutModel()
			
			class VlcModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
				pass
			vlc: VlcModel = VlcModel()

		local: LocalModel = LocalModel()
		
	integrations: IntegrationsModel = IntegrationsModel()
	
	class MtgModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
		formats: tuple[str | None] = (
			'Standard', 'Pioneer', 'Modern', 'Legacy', 'Vintage', 'Pauper', 'Premodern', None,
			'Commander', 'Duel Commander', None,
			'Draft', 'Sealed', 'Cube', None,
			'Alchemy', 'Brawl', 'Dandan', 'Historic', 'Old School', 'Penny Dreadful', 'Timeless', 'Value Vintage',
		)
	mtg: MtgModel = MtgModel()
	
	class ProjectModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
		slug_regex: str = r'^(\w+)-(\d{4})$'
	project: ProjectModel = ProjectModel()

	class ToolsModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
		
		class DaemonModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
			filelock: str = 'lock_daemon.lock'
		daemon: DaemonModel = DaemonModel()
		
		class ScheduleModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
			image_size: dict = {'width': 1080, 'height': 1080}
		schedule: ScheduleModel = ScheduleModel()
	
	tools: ToolsModel = ToolsModel()
	
	class NetworkModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
		http_serve_port: int = 42967
		chromium_debug_port: int = 42968
		websocket_port: int = 42969
	network: NetworkModel = NetworkModel()
	
	class StyleModel (pydantic.BaseModel, frozen = True, extra = 'forbid'):
		text_lgt: str = '#ffffff'
		text_drk: str = '#000000'
		background_hilgt: str = '#505050'
		background_lgt: str = '#404040'
		background_med: str = '#202020'
		background_drk: str = '#101010'
		foreground_lgt: str = '#ffffff'
		foreground_med: str = '#dddddd'
		foreground_drk: str = '#bbbbbb'
		action_l: float = 0.83
		action_c: float = 0.08
		accent_l: float = 0.71
		accent_c: float = 0.12
		hint_l: float = 0.42 # 0.30
		hint_c: float = 0.07 # 0.05
		rainbow: str = pydantic.Field(default_factory = lambda : ', '.join([
			f'stop: {i / 100.0} {Util.oklch_to_hex(0.71, 0.12, i * 360.0 / 100.0)}' for i in range(0, 101)
		]))
	style: StyleModel = StyleModel()
		
# Implementation ###############################################################

	_instance: typing.ClassVar[typing.Self | None] = None
	
if not _ConfigModel._instance:
	_ConfigModel._instance = _ConfigModel()

def Config () -> _ConfigModel:
	return _ConfigModel._instance

