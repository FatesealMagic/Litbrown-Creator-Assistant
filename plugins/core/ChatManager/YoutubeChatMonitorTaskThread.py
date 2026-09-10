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

from loguru import logger
import playwright.sync_api

from .ChatMonitorTaskThread import ChatMonitorTaskThread

class YoutubeChatMonitorTaskThread (ChatMonitorTaskThread):

	def __init__ (self,
		broadcast_id: str,
	):
		self.__broadcast_id = broadcast_id
		super().__init__()

	@property
	def _platform_name (self) -> str:
		return 'youtube'

	@property
	def _url (self) -> str:
		return f'https://www.youtube.com/live_chat?is_popout=1&v={self.__broadcast_id}'

	@property
	def _style (self) -> str:
		return '''

			body, yt-live-chat-text-message-renderer, yt-live-chat-renderer {
				background: transparent !important;
			}

			div#item-scroller {
				overflow: clip !important;
			}

			div#items {
				transform: none !important;
				overflow: clip;
			}

			body >:not(yt-live-chat-app),
			yt-live-chat-app >:not(#contents), 
			yt-live-chat-renderer >:not(tp-yt-iron-pages),
			tp-yt-iron-pages >:not(#chat-messages),
			#chat-messages >:not(#contents),
			#chat-messages >#contents >:not(#chat),
			#item-scroller >:not(#item-offset),
			#item-offset >#items >:not(yt-live-chat-text-message-renderer),
			#reaction-control-panel-overlay {
				display: none !important;
			}

			yt-live-chat-text-message-renderer {
				padding-left: 14px !important;
				padding-right: 6px !important;
				font-size: 15px !important;
			}

			yt-live-chat-text-message-renderer >yt-img-shadow {
				margin-right: 10px !important;
			}

		'''

	@property
	def _container_selector (self) -> str:
		return 'div#items'

	def _js_determine_message (self) -> str:
		return '''
			(el) => {
				return el.querySelector('span#message').innerText;
			}
		'''

	def _js_determine_platform_message_id (self) -> str:
		return '''
			(el) => {
				return el.id;
			}
		'''

	def _js_determine_platform_user_id (self) -> str:
		return '''
			(el) => {
				return el.querySelector('span#author-name').innerText;
			}
		'''

