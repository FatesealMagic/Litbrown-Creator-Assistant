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

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Config import *
from ...I18n import *
from ...Assets import *
from ...Util import *

from ..LCAConnectionLabelWidget import *
from ..LCAPopupMessage import *
from ..LCASeparator import *
from ..LCATaskTrackerWidget import *
from ..LCAWidget import *
from ...integrations.LCAIntegrationErrors import *
from ...integrations.patreon.LCAPatreonIntegration import *
from ...integrations.twitch.LCATwitchIntegration import *
from ...integrations.youtube.LCAYoutubeIntegration import *
from ...threads.schedule.LCASPatreonCreateLivesTaskThread import *
from ...threads.schedule.LCASYoutubeBroadcastPublishTaskThread import *
from ...threads.schedule.LCASTwitchUpdateStreamScheduleTaskThread import *

class LCASPublishManagerWidget (LCAWidget):
	
	__task_widgets: list[LCATaskTrackerWidget]
	__publish_thread_params_factory: typing.Callable[[], dict]
	
	def __init__ (self, publish_thread_params_factory: typing.Callable[[], dict], *args, **kwargs):
		self.__task_widgets = []
		self.__publish_thread_params_factory = publish_thread_params_factory
		super().__init__(*args, **kwargs)
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		if publish_scrollarea := QScrollArea():
			publish_scrollarea.setWidgetResizable(True)
			publish_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
			publish_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
			if publishmgr_widget := QWidget():
				publishmgr_layout = QVBoxLayout(publishmgr_widget)
				if youtubemgr_widget := QWidget():
					youtubemgr_layout = QVBoxLayout(youtubemgr_widget)
					youtubemgr_layout.setSpacing(youtubemgr_layout.spacing() * 2)
					youtubemgr_layout.addWidget(LCAConnectionLabelWidget('youtube'))
					if youtube_broadcastpublish_widget := LCATaskTrackerWidget(
						label = I18n(self).youtube.broadcastpublish.title,
						thread_factory = lambda : LCASYoutubeBroadcastPublishTaskThread( ** self.__publish_thread_params_factory() ),
						integration = LCAYoutubeIntegration,
					):
						self.__task_widgets.append(youtube_broadcastpublish_widget)
					youtubemgr_layout.addWidget(youtube_broadcastpublish_widget)
				publishmgr_layout.addWidget(youtubemgr_widget)
				publishmgr_layout.addWidget(LCASeparator.horizontal())
				if twitchmgr_widget := QWidget():
					twitchmgr_layout = QVBoxLayout(twitchmgr_widget)
					twitchmgr_layout.setSpacing(twitchmgr_layout.spacing() * 2)
					twitchmgr_layout.addWidget(LCAConnectionLabelWidget('twitch'))
					if twitch_updatestreamschedule_widget := LCATaskTrackerWidget(
						label = I18n(self).twitch.updatestreamschedule.title,
						thread_factory = lambda : LCASTwitchUpdateStreamScheduleTaskThread( ** self.__publish_thread_params_factory() ),
						integration = LCATwitchIntegration,
					):
						twitch_updatestreamschedule_widget.error.connect(self.__evt_error_twitch_updatestreamschedule)
						self.__task_widgets.append(twitch_updatestreamschedule_widget)
					twitchmgr_layout.addWidget(twitch_updatestreamschedule_widget)
				publishmgr_layout.addWidget(twitchmgr_widget)
				publishmgr_layout.addWidget(LCASeparator.horizontal())
				if patreonmgr_widget := QWidget():
					patreonmgr_layout = QVBoxLayout(patreonmgr_widget)
					patreonmgr_layout.setSpacing(patreonmgr_layout.spacing() * 2)
					patreonmgr_layout.addWidget(LCAConnectionLabelWidget('patreon'))
					if patreon_createlives_widget := LCATaskTrackerWidget(
						label = I18n(self).patreon.createlives.title,
						thread_factory = lambda : LCASPatreonCreateLivesTaskThread( ** self.__publish_thread_params_factory() ),
						integration = LCAPatreonIntegration,
					):
						patreon_createlives_widget.error.connect(self.__evt_error_patreon_createlives)
						self.__task_widgets.append(patreon_createlives_widget)
					patreonmgr_layout.addWidget(patreon_createlives_widget)
				publishmgr_layout.addWidget(patreonmgr_widget)
				publishmgr_layout.addStretch()
			publish_scrollarea.setWidget(publishmgr_widget)
		layout.addWidget(publish_scrollarea)

	def __evt_error_twitch_updatestreamschedule (self, e: Exception) -> None:
		error_key = 'error_unknown'
		match e:
			case LCAIntegrationUserForbiddenError:
				error_key = 'error_not_affiliate_partner'
		LCAPopupMessage.error(getattr(I18n(self).twitch.updatestreamschedule, error_key))

	def __evt_error_patreon_createlives (self, e: Exception) -> None:
		error_key = 'error_unknown'
		match e:
			case LCAIntegrationDeficientRemoteError:
				error_key = 'error_liveapi_not_working'
		LCAPopupMessage.error(getattr(I18n(self).patreon.createlives, error_key))

	def do_publish (self) -> None:
		for task in self.__task_widgets:
			task.execute()

