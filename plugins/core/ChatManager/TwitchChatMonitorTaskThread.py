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
'stateNode.__reactFiber$3ha5n4xzuur.stateNode.__reactFiber$3ha5n4xzuur.return.return.stateNode.props.40d90ce0-8f18-4128-9827-ff0b457ec3ef'
from loguru import logger
import playwright.sync_api

from .ChatMonitorTaskThread import ChatMonitorTaskThread

class TwitchChatMonitorTaskThread (ChatMonitorTaskThread):

	def __init__ (self,
		broadcast_id: str,
	):
		self.__broadcast_id = broadcast_id
		super().__init__()

	@property
	def _platform_name (self) -> str:
		return 'twitch'

	@property
	def _url (self) -> str:
		return f'https://www.twitch.tv/popout/{self.__broadcast_id}/chat'

	@property
	def _style (self) -> str:
		return '''

		body, div#root, section.chat-room  {
			background: transparent !important;
		}

		div.scrollable-area >div >div >div >div:not(.chat-line__message),
		div.chat-room__content >:not(:nth-child(4)),
		div.snackbar-list__container.snackbar-overlay__list,
		div.stream-chat-header,
		div[data-a-target='chat-welcome-message'] {
			display: none !important;
		}

		div.chat-room__content >:nth-child(4) div.scrollable-area {
			overflow: hidden;
		}

		'''

	@property
	def _container_selector (self) -> str:
		return 'div.chat-scrollable-area__message-container'

	def _determine_message (self,
		chat_element: playwright.sync_api.Locator,
	) -> str:
		logger.debug('in determine message')
		return chat_element.locator('span[data-a-target="chat-line-message-body"]').inner_text()

	def _determine_platform_message_id (self,
		chat_element: playwright.sync_api.Locator,
	) -> str:
		return chat_element.locator('div.chat-line__message').first.evaluate('''
			(el) => {
				try {
					const ret = el[
						Object.keys(el).find( k => k.startsWith('__reactProps$') )
					]?.children?.props?.children?.[0]?._owner?.stateNode?.props?.message?.id;
					if (!ret) return '';
					return ret;
				} catch (e) {
					return '';
				}
			}
		''')

	def _determine_platform_user_id (self,
		chat_element: playwright.sync_api.Locator,
	) -> str:
		return chat_element.locator('span[data-a-target="chat-message-username"]').inner_text()

