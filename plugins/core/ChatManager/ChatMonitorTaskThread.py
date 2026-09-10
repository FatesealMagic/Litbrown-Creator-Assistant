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

	def _js_determine_message (self) -> str:
		raise NotImplementedError

	def _js_determine_platform_message_id (self) -> str:
		raise NotImplementedError

	def _js_determine_platform_user_id (self) -> str:
		raise NotImplementedError

	def _run (self,
	) -> None:
		self.__queue = queue.SimpleQueue()
		with playwright.sync_api.sync_playwright() as p:
			browser = p.chromium.launch(headless = True)
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
		page.add_style_tag(content = self.__css_clear_nonactive_siblings())
		page.expose_function('lca_callback_new_chat', lambda lcaid : self.__queue.put(lcaid))
		container = page.locator(self._container_selector)
		container.evaluate(self.__js_prepare_container(), timeout = 15000)
		return page

	def __process_new_chat (self, message: dict) -> str:
		logger.info(f'Received chat w/ ts {message['timestamp']}: {message['message']}')
		try:
			message['screenshot'] = str( base64.b64encode(
				self.__page.locator(f'[data-lcats="{message['timestamp']}"]').first.screenshot(
					animations = 'disabled',
					omit_background = True,
					timeout = 10000,
				)
			), 'utf-8' )
		except Exception as e:
			logger.exception(e)
			return 'error'
		self.update.emit(ChatManagerModel.Message(**message))
		return str(message['timestamp'])

	def __css_clear_nonactive_siblings (self) -> str:
		return '''
			''' + self._container_selector + ''' >:not([data-lcats]) {
				display: none;
			}
		'''

	def __js_clear_container (self) -> str:
		return '''
			(el) => {
				el.replaceChildren();
			}
		'''

	def __js_prepare_container (self) -> str:
		return '''
			(el) => {

				const setup_mutation_observer = () => {
					new MutationObserver( async (records, observer) => {
						for (let record of records) {
							for (let node of record.addedNodes) {
								if (node.nodeType !== 1)
									continue;
								process_node(node);
							}
						}
					} ).observe( el, { childList: true } );
				};

				const process_node = async (node) => {

					node.dataset.lcats = Temporal.Now.instant().epochMilliseconds.toString() +
						Math.floor(Math.random() * 1e12).toString().padStart(12, '0');
					console.log(`Processing node w/ ID ${node.dataset.lcats}`);

					const determined_message = determine_message(node);
					const determined_platform_message_id = determine_platform_message_id(node);
					const determined_platform_user_id = determine_platform_user_id(node);

					window.lca_callback_new_chat({
						timestamp: node.dataset.lcats,
						message: determined_message,
						platform_name: "''' + self._platform_name + '''",
						platform_message_id: determined_platform_message_id,
						platform_user_id: determined_platform_user_id,
					});
					
					console.log(`Finished processing node w/ ID ${ret}`);

				};

				const determine_message             = ''' + self._js_determine_message() + ''';
				const determine_platform_message_id = ''' + self._js_determine_platform_message_id() + ''';
				const determine_platform_user_id    = ''' + self._js_determine_platform_user_id() + ''';

				el.replaceChildren();
				setup_mutation_observer();
				console.info('Setup complete');

			};
		'''

