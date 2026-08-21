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
import sys

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtWidgets import *

from ...Assets import *
from ...Config import *
from ...I18n import *
from ...Settings import *
from ...Util import *

from ..LCAComboBox import *
from ..LCAMainWindow import *
from ..LCAPopupMessage import *
from ...common.LCAProjectState import *
from ...models.LCAProjectFileModel import *
from ...threads.LCAWorkerThread import *
from ...threads.multicast.LCAMObsRecordPuppeteerWorkerObject import *

class LCAMMainWindow (LCAMainWindow):
	
	__project: LCAProjectFileModel
	
	__segment_cbo: LCAComboBox
	__start_btn: QPushButton
	__stop_btn: QPushButton
	__status_lbl: QLabel
	
	__obs_thread: LCAWorkerThread
	
	__BUTTONS_STYLESHEET = 'font-size: 13pt; font-weight: bold;'
	
	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.error(I18n(self).errors.need_slug)
			sys.exit()
		self.__project = LCAProjectFileModel.from_slug(sys.argv[2])
		self.__attempt_initialize_project_state()
		self.__setup_obs_thread()
		self.setWindowIcon(Assets.QIcon('icons/multicast.ico'))
		self.setWindowTitle(I18n(self).title)
		if profile := Settings().tools.multicast.profile.get(self.__project.series_id, None):
			self.restoreGeometry(profile.geometry)
			self.restoreState(profile.state)
		self.setEnabled(False)

	def __attempt_initialize_project_state (self) -> None:
		try:
			LCAProjectState(self.__project)
		except RuntimeError:
			LCAPopupMessage.error(I18n(self).errors.state_server_already_running)
			sys.exit()

	def __setup_obs_thread (self) -> None:
		self.__obs_thread = LCAWorkerThread(LCAMObsRecordPuppeteerWorkerObject('record'))
		self.obs().on_connected.connect(self.__slot_obs_connected)
		self.obs().do_scene_change_complete.connect(self.__slot_obs_do_scene_change_complete)

	def _setup_layout (self) -> None:
		if wrapper_widget := QWidget():
			wrapper_layout = QHBoxLayout(wrapper_widget)
			wrapper_layout.setContentsMargins(*([wrapper_layout.spacing() * 2] * 3 + [0]))
			if widget := QFrame():
				widget.setProperty('css_class', 'accent_bordered')
				layout = QVBoxLayout(widget)
				layout.addWidget(QLabel(
					f'<h3 style="text-align: center;">{Settings().series_from_id(self.__project.series_id).name} '
						+ f'#{self.__project.entry_number}</h3>'
				))
				if segment_cbo := LCAComboBox():
					self.__segment_cbo = segment_cbo
					self.__rebuild_segment_cbo()
					segment_cbo.currentDataChanged.connect(self.__evt_segment_changed)
				layout.addWidget(segment_cbo, 1)
				if controls_widget := QWidget():
					controls_widget.setStyleSheet(self.__BUTTONS_STYLESHEET)
					controls_layout = QHBoxLayout(controls_widget)
					controls_layout.setContentsMargins(0, 0, 0, 0)
					if start_btn := QPushButton(I18n(self).buttons.start):
						self.__start_btn = start_btn
						start_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
					controls_layout.addWidget(start_btn, 1)
					if stop_btn := QPushButton(I18n(self).buttons.stop):
						self.__stop_btn = stop_btn
						stop_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
					controls_layout.addWidget(stop_btn, 1)
				layout.addWidget(controls_widget, 1)
			wrapper_layout.addWidget(widget)
		self.setCentralWidget(wrapper_widget)
		self.__setup_status_bar()
		self.__obs_thread.start()

	def __rebuild_segment_cbo (self) -> None:
		with QSignalBlocker(self.__segment_cbo):
			self.__segment_cbo.clear()
			for segment in Settings().series_from_id(self.__project.series_id).segments:
				if segment.repeatable:
					pass
				else:
					if 
				segment_cbo.addItem(f'{segment.name} #1' if segment.repeatable else segment.name, segment.id)


	def __setup_status_bar (self) -> None:
		self.statusBar().setSizeGripEnabled(False)
		self.__status_lbl = QLabel()
		self.__status_lbl.setStyleSheet('margin-right: 0.3em; margin-bottom: 0.3em;')
		self.statusBar().addPermanentWidget(self.__status_lbl)
		self.__set_status_message(I18n(self).statuses.obs_connecting)

	def closeEvent (self, event: QCloseEvent) -> None:
		LCAProjectState().shutdown()
		self.__obs_thread.quit()
		logger.debug(self.saveGeometry())
		logger.debug(self.saveState())
		with Settings():
			Settings().tools.multicast.profile[self.__project.series_id] = \
				Settings().ToolsModel.ToolsMulticastModel.ToolsMulticastProfileModel(
					geometry = base64.b64encode(bytes(self.saveGeometry())),
					state = base64.b64encode(bytes(self.saveState())),
				)
		self.__obs_thread.wait()
		event.accept()

	def __evt_segment_changed (self, segment_id: str) -> None:
		segment = Settings().series_segment_from_id(self.__project.series_id, segment_id)
		self.setEnabled(False)
		self.obs().do_scene_change.emit(segment.obs_scene_name)
		with LCAProjectState() as state:
			state.model.segment_id = segment_id

	def __set_status_message (self, msg: str) -> None:
		self.__status_lbl.setText(f'{msg}')

	@Slot(bool)
	def __slot_obs_connected (self, success: bool) -> None:
		self.setEnabled(success)
		self.__set_status_message(I18n(self).statuses.obs_connected if success else I18n(self).statuses.obs_connecting)
		self.__evt_segment_changed(self.__segment_cbo.currentData())

	@Slot(bool)
	def __slot_obs_do_scene_change_complete (self, scene_name: str) -> None:
		self.setEnabled(True)

	def obs (self) -> LCAMObsRecordPuppeteerWorkerObject:
		return self.__obs_thread.worker

