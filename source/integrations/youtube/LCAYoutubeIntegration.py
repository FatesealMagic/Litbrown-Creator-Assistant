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

import json
import pathlib
import sys

from loguru import logger
import requests

import google.auth
import google.oauth2
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http

from ..LCAIntegration import LCAIntegration
from ..LCAIntegrationErrors import *

from ...Assets import Assets
from ...Config import Config
from ...Settings import Settings

class LCAYoutubeIntegration (LCAIntegration):
	
	__SCOPES = [
		'https://www.googleapis.com/auth/youtube',
		'https://www.googleapis.com/auth/youtube.channel-memberships.creator',
	]
	
	__API_NAME = 'youtube'
	__API_VERSION = 'v3'

	@staticmethod
	def is_initialized () -> bool:
		return bool(Settings().integrations.youtube.auth)

	def _connect (self) -> None:
		self.__yt = self.__build_yt_client()

	def _disconnect (self) -> None:
		try:
			self.__yt.close()
			del self.__yt
		except AttributeError:
			pass

	def __build_yt_client (self) -> googleapiclient.discovery.Resource:
		return googleapiclient.discovery.build(
			self.__API_NAME,
			self.__API_VERSION,
			credentials = self.__get_yt_credentials()
		)

	def __get_yt_credentials (self) -> google.oauth2.credentials.Credentials:
		try:
			return google.oauth2.credentials.Credentials(
				token = Settings().integrations.youtube.auth['access_token'],
				scopes = self.__SCOPES,
			)
		except:
			with Settings():
				Settings().integrations.youtube.auth = None
			raise LCAIntegrationBadCredentialsError

	def __refresh_yt_credentials (self, cred: google.oauth2.credentials.Credentials) -> None:
		cred.refresh(google.auth.transport.requests.Request())

	@LCAIntegration.in_context
	def yt (self) -> googleapiclient.discovery.Resource:
		return getattr(self, '__yt', self.__build_yt_client())

	def __execute_request (self, req: typing.Callable[[], googleapiclient.http.HttpRequest]) -> dict:
		caught_401 = False
		for attempt in range(10):
			try:
				return req().execute()
			except google.auth.exceptions.RefreshError as e:
				if not caught_401:
					logger.debug('caught 401 as refresherror')
					caught_401 = True
					self.__refresh_token()
				else:
					raise LCAIntegrationBadCredentialsError
			except (googleapiclient.errors.HttpError, google.auth.exceptions.RefreshError) as e:
				if (type(e) is google.auth.exceptions.RefreshError) or (e.resp.status in (401,)):
					if not caught_401:
						logger.debug('caught 401 as httperror')
						caught_401 = True
						self.__refresh_token()
					else:
						raise LCAIntegrationBadCredentialsError
				elif e.resp.status in self._RETRIABLE_STATUS_CODES:
					self._exponential_wait(attempt, e.resp.status)
				else:
					raise LCAIntegrationNetworkFailureError
		raise LCAIntegrationNetworkFailureError

	def __execute_paginated_request (self, req: typing.Callable[[], googleapiclient.http.HttpRequest]) -> list:
		ret = []
		next_page = None
		while True:
			# Create a new req factory each time where the uri of the original request is modified to have the next page token
			req_next = lambda : ((r := req()), setattr(r, 'uri', r.uri + (f'&pageToken={next_page}' if next_page else '')), r)[-1]
			rsp = self.__execute_request(req_next)
			ret += rsp.get('items', [])
			next_page = rsp.get('nextPageToken')
			if not next_page:
				break
		return ret

	def __execute_chunked_request (self,
		req: typing.Callable[[], googleapiclient.http.HttpRequest],
	) -> typing.Generator[float, None, dict]:
		rsp = None
		caught_401 = False
		req_obj = req()
		while rsp is None:
			for attempt in range(10):
				try:
					status, rsp = req_obj.next_chunk()
					if status is not None:
						yield status.progress()
					break
				except (googleapiclient.errors.HttpError, google.auth.exceptions.RefreshError) as e:
					if (type(e) is google.auth.exceptions.RefreshError) or (e.resp.status in (401,)):
						if not caught_401:
							logger.debug('caught 401')
							caught_401 = True
							self.__refresh_token()
						else:
							raise LCAIntegrationBadCredentialsError
					elif e.resp.status in self._RETRIABLE_STATUS_CODES:
						self._exponential_wait(attempt, e.resp.status)
					else:
						raise LCAIntegrationNetworkFailureError
				raise LCAIntegrationNetworkFailureError
		return rsp

	def __create_media_file_upload (self, path: str) -> googleapiclient.http.MediaFileUpload:
		return googleapiclient.http.MediaFileUpload(
			path,
			chunksize = 1024*1024,
			resumable = True,
		)

	def __refresh_token (self) -> None:
		refresh = Settings().integrations.youtube.auth['refresh_token']
		rsp = requests.get( f'{Config().integrations.remote.oauth_service_url}/youtube', params = {'refresh': refresh} )
		if rsp.status_code < 200 or rsp.status_code > 299:
			raise LCAIntegrationNetworkFailureError
		logger.info('Updating Youtube refresh token')
		new_auth = rsp.json()
		new_auth['refresh_token'] = refresh
		with Settings():
			Settings().integrations.youtube.auth = new_auth

	@LCAIntegration.in_context
	def get_user_info (self) -> Settings().IntegrationsModel.RemoteIntegrationModel:
		rsp = self.__execute_request( lambda : self.yt().channels().list(
			part = 'snippet,contentDetails,statistics',
			mine = True,
		) )
		if rsp.get('items'):
			return Settings().IntegrationsModel.RemoteIntegrationModel(
				remote_id               = rsp['items'][0]['id'],
				handle                  = rsp['items'][0]['snippet']['customUrl'],
				display_name            = rsp['items'][0]['snippet']['title'],
				profile_pic_url         = rsp['items'][0]['snippet']['thumbnails']['default']['url'],
				auth                    = Settings().integrations.youtube.auth,
				remote_membership_tiers = self.get_membertiers_info(),
			)
		else:
			return Settings().IntegrationsModel.RemoteIntegrationModel(
				remote_id               = '',
				handle                  = '',
				display_name            = '',
				profile_pic_url         = '',
				auth                    = Settings().integrations.youtube.auth,
				remote_membership_tiers = self.get_membertiers_info(),
			)

	@LCAIntegration.in_context
	def get_membertiers_info (self) -> list[Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel]:
		try:
			rsp = self.__execute_request( lambda : self.yt().membershipsLevels().list(part = 'id,snippet') )
			return [ Settings().IntegrationsModel.RemoteIntegrationModel.RemoteMembershipTierModel(
				remote_id = item['id'],
				remote_name = item['snippet']['levelDetails']['displayName'],
			) for item in rsp['items'] ]
		except:
			return []

	@LCAIntegration.in_context
	def create_broadcast (self, /,
		title: str,
		description: str,
		start: str,
		public: bool,
	) -> str:
		return self.__execute_request( lambda : self.yt().liveBroadcasts().insert(
			part = 'snippet,status',
			body = {
				'snippet': {
					'title': title,
					'description': description,
					'scheduledStartTime': self._apply_bounds_to_timestamp(start),
				},
				'status': {
					'privacyStatus': 'public' if public else 'unlisted',
					'selfDeclaredMadeForKids': False, # TODO is there really any situation where this would be True ???
				},
			}
		) )['id']

	@LCAIntegration.in_context
	def upload_video (self, *,
		filename: str | pathlib.Path,
		title: str,
		description: str,
		privacy: typing.Literal['private', 'unlisted'],
	) -> typing.Generator[float, None, str]:
		for _ in range(3):
			try:
				return ( yield from self.__execute_chunked_request(
					lambda : self.yt().videos().insert(
						part = 'snippet,status',
						media_body = self.__create_media_file_upload(str(filename)),
						body = {
							'snippet': {
								'title': title,
								'description': description,
								'categoryId': '20',
							},
							'status': {
								'privacyStatus': privacy,
							},
						},
					)
				) )['id']
			except Exception as e:
				logger.warning(f'Encountered exception during video upload: {e}')
		raise LCAIntegrationUnexpectedError

	@LCAIntegration.in_context
	def set_thumbnail (self, /,
		video_id: str,
		thumbnail_path: str,
	) -> typing.Generator[float, None, None]:
		yield from self.__execute_chunked_request( lambda : self.yt().thumbnails().set(
			videoId = video_id,
			media_body = self.__create_media_file_upload(thumbnail_path),
		) )

	@LCAIntegration.in_context
	def get_playlists (self) -> list[Settings().IntegrationsModel.YoutubeRemoteIntegrationModel.PlaylistModel]:
		return [ Settings().IntegrationsModel.YoutubeRemoteIntegrationModel.PlaylistModel(
			title      = playlist['snippet']['title'],
			id         = playlist['id'],
			privacy    = playlist['status']['privacyStatus'],
			item_count = playlist['contentDetails']['itemCount'],
		) for playlist in self.__execute_paginated_request( lambda : self.yt().playlists().list(
			part = 'contentDetails,snippet,status',
			mine = True,
			maxResults = 50,
		) ) ]

	@LCAIntegration.in_context
	def add_to_playlist (self,
		/, *,
		video_id: str,
		playlist_id: str,
	) -> None:
		self.__execute_request( lambda : self.yt().playlistItems().insert(
			part = 'snippet',
			body = { 'snippet': {
				'playlistId': playlist_id,
				'resourceId': { 'kind': 'youtube#video', 'videoId': video_id },
			} },
		) )

