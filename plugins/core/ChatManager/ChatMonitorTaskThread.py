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
import queue
import time

from loguru import logger
import playwright.sync_api

from source.threads.LCATaskThread import LCATaskThread

from .ChatManagerModel import *

class ChatMonitorTaskThread (LCATaskThread):

	__page: playwright.sync_api.Page
	__queue: queue.SimpleQueue

	@property
	def _platform_name (self) -> str:
		raise NotImplementedError

	@property
	def _url (self) -> str:
		raise NotImplementedError

	@property
	def _style (self) -> str:
		raise NotImplementedError

	@property
	def _container_selector (self) -> str:
		raise NotImplementedError

	def _determine_message (self,
		chat_element: playwright.sync_api.Locator,
	) -> str:
		raise NotImplementedError

	def _determine_platform_message_id (self,
		chat_element: playwright.sync_api.Locator,
	) -> str:
		raise NotImplementedError

	def _determine_platform_user_id (self,
		chat_element: playwright.sync_api.Locator,
	) -> str:
		raise NotImplementedError

	def _run (self,
	) -> None:
		self.__queue = queue.SimpleQueue()
		with playwright.sync_api.sync_playwright() as p:
			browser = p.webkit.launch(headless = True)
			self.__page = self.__initialize_page(browser)
			while not self.isInterruptionRequested():
				while True:
					try:
						self.__process_new_chat( self.__queue.get(block = False) )
					except queue.Empty:
						break
				self.__page.wait_for_timeout(50)
			browser.close()

	def __initialize_page (self,
		browser: playwright.sync_api.Browser,
	) -> playwright.sync_api.Page:
		page = browser.new_page(
			color_scheme = 'dark',
			viewport = {'width': 300, 'height': 900},
		)
		page.on('pageerror', lambda e : logger.error(f'Browser error: {e}'))
		page.set_default_timeout(2000)
		page.goto(self._url, timeout = 20000)
		page.wait_for_load_state(timeout = 20000)
		page.add_style_tag(content = self._style)
		page.expose_function('lca_callback_new_chat', lambda lcaid : self.__queue.put(lcaid))
		container = page.locator(self._container_selector)
		container.evaluate(self.__js_hookup_callback())
		return page

	def __process_new_chat (self, lcaid: str) -> None:
		logger.debug(f'Processing new chat: {lcaid}')
		try:
			el = self.__page.locator(f'[data-lcaid="{lcaid}"]').first
		except Exception as e:
			logger.exception(e)
			return
		try:
			screenshot = el.screenshot(
				animations = 'disabled',
				omit_background = True,
				timeout = 10000,
			)
		except Exception as e:
			logger.exception(e)
			return
		try:
			message = ChatManagerModel.Message(
				lcaid = lcaid,
				timestamp = time.time(),
				message = self._determine_message(el),
				screenshot = str(base64.b64encode(screenshot), 'utf-8'),
				platform_name = self._platform_name,
				platform_message_id = self._determine_platform_message_id(el),
				platform_user_id = self._determine_platform_user_id(el),
			)
		except Exception as e:
			logger.exception()
			return
		self.update.emit(message)

	def __js_hookup_callback (self) -> str:
		return '''
			async (el) => {
				new MutationObserver( async (records, observer) => {
					for (let record of records) {
						for (let node of record.addedNodes) {
							node.dataset.lcaid = `lcaid${Date.now()}''' + self._platform_name + '''${Math.floor(Math.random() * 1000000).toString().padStart(6, '0')}`;
							console.log(`Processing item with lcaid ${node.dataset.lcaid}`);
							await window.lca_callback_new_chat(node.dataset.lcaid);
						}
					}
				} ).observe( el, { childList: true } );
			}
		'''

