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

from loguru import logger
import pydantic

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from source.Config import Config
from source.Settings import Settings
from source.common.LCAProjectState import LCAProjectState
from source.gui.LCAMagicCardSelectorWidget import LCAMagicCardSelectorWidget
from source.gui.LCAPluginWidget import LCAPluginWidget
from source.integrations.mtgosdk.LCAMtgosdkIntegration import LCAMtgosdkIntegration
from source.models.LCAProjectStateModel import LCAProjectStateModel
from source.models.LCAScryfallCardModel import LCAScryfallCardModel
from source.threads.common.LCAScryfallSearchTaskThread import LCAScryfallSearchTaskThread

from .ChatManagerModel import ChatManagerModel
from .SingleChatWidget import SingleChatWidget
from .TwitchChatMonitorTaskThread import TwitchChatMonitorTaskThread
from .YoutubeChatMonitorTaskThread import YoutubeChatMonitorTaskThread

class ChatManagerWidget (LCAPluginWidget):

	__scroll_lock: bool = True
	__scroll_area: QScrollArea
	__chats_widget: QWidget
	__youtube_thread: YoutubeChatMonitorTaskThread

	def _project_state_type (self) -> type[pydantic.BaseModel]:
		return ChatManagerModel

	def _initial_project_state_data (self) -> pydantic.BaseModel:
		return ChatManagerModel()

	def _setup_layout (self) -> None:
		if widget := QWidget():
			layout = QVBoxLayout(widget)
			if scroll_area := QScrollArea():
				self.__scroll_area = scroll_area
				scroll_area.setWidgetResizable(True)
				scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
				scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
				scroll_area.verticalScrollBar().rangeChanged.connect(
					lambda minimum, maximum : scroll_area.verticalScrollBar().setValue(maximum) if self.__scroll_lock else None
				)
				if chats_widget := QWidget():
					self.__chats_widget = chats_widget
					chats_widget.setFixedWidth(self._get_project_state_data().width)
					chats_layout = QVBoxLayout(chats_widget)
					chats_layout.setContentsMargins(0, 0, 0, 0)
					chats_layout.setSpacing(0)
					chats_layout.addStretch()
				scroll_area.setWidget(chats_widget)
				scroll_area.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
				scroll_area.setFixedWidth(
					300 + # TODO
					(2 * scroll_area.frameWidth()) +
					scroll_area.verticalScrollBar().sizeHint().width()
				)
			layout.addWidget(scroll_area, alignment = Qt.AlignHCenter)
		self.setWidget(widget)

	def _post_layout (self) -> None:
		self.__start_chat_threads()
		self.__update_chat_display()

	def __start_chat_threads (self) -> None:
		'''if youtube_broadcast_id := LCAProjectState().model.project.stream.remote_ids.youtube:
			youtube_broadcast_id = 'rFZHOHl-L8A' # TODO Lofi girl stream, edit out later
			self.__youtube_thread = YoutubeChatMonitorTaskThread(youtube_broadcast_id)
			self.__youtube_thread.update.connect(self.__slot_new_message)
			self.__youtube_thread.start()'''
		if twitch_broadcast_id := Settings().integrations.twitch.handle:
			twitch_broadcast_id = 'ohnePixel' # TODO edit out later
			self.__twitch_thread = TwitchChatMonitorTaskThread(twitch_broadcast_id)
			self.__twitch_thread.update.connect(self.__slot_new_message)
			self.__twitch_thread.start()

	@Slot(object)
	def __slot_new_message (self, message: ChatManagerModel.Message) -> None:
		logger.debug(message.message)
		with self._project_state_data() as data:
			data.messages.append(message)
			data.messages.sort( key = lambda x : x.timestamp )
			data.messages = data.messages[-20:]
		self.__update_chat_display()

	def __update_chat_display (self) -> None:
		previous_index = 1
		for message in self._get_project_state_data().messages:
			if child_widget := self.__chats_widget.findChild(QWidget, str(message.timestamp)):
				previous_index = self.__chats_widget.layout().indexOf(child_widget)
			else:
				previous_index += 1
				scroll_bar = self.__scroll_area.verticalScrollBar()
				self.__scroll_lock = (scroll_bar.value() == scroll_bar.maximum())
				self.__chats_widget.layout().insertWidget(previous_index, SingleChatWidget(message))

	def closeEvent (self, e: QCloseEvent) -> None:
		self.__youtube_thread.requestInterruption()
		self.__youtube_thread.wait()
		super().closeEvent(e)

