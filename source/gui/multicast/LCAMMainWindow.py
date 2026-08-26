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
import pynput

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
from ...common.LCAKeySequence import *
from ...models.LCAProjectFileModel import *
from ...threads.LCAWorkerThread import *
from ...threads.multicast.LCAMObsRecordPuppeteerWorkerObject import *

class LCAMMainWindow (LCAMainWindow):

	hotkey_pressed = Signal(str)

	__project: LCAProjectFileModel
	
	__id_label: QLabel
	__segment_cbo: LCAComboBox
	__startstop_btn: QPushButton
	__status_lbl: QLabel
	
	__obs_thread: LCAWorkerThread
	
	__BUTTONS_STYLESHEET = 'font-size: 13pt; font-weight: bold;'
	
	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.error(I18n(self).errors.need_slug)
			sys.exit()
		self.__project = LCAProjectFileModel.from_slug(sys.argv[2])
		self.__initialize_project_state()
		self.__setup_obs_thread()
		self.__setup_keyboard_hotkey_signals()
		self.__setup_keyboard_hotkeys()
		self.setWindowIcon(Assets.QIcon('icons/multicast.ico'))
		self.setWindowTitle(I18n(self).title)
		if profile := Settings().tools.multicast.profile.get(self.__project.series_id, None):
			self.restoreGeometry(profile.geometry)
			self.restoreState(profile.state)
		self.setEnabled(False)

	def __initialize_project_state (self) -> None:
		try:
			LCAProjectState(self.__project)
		except RuntimeError:
			LCAPopupMessage.error(I18n(self).errors.state_server_already_running)
			sys.exit()

	def __setup_obs_thread (self) -> None:
		self.__obs_thread = LCAWorkerThread(LCAMObsRecordPuppeteerWorkerObject())
		self.obs().on_connected.connect(self.__slot_obs_connected)
		self.obs().on_scene_changed.connect(self.__slot_obs_on_scene_changed)
		self.obs().on_active_toggled.connect(self.__slot_obs_on_active_toggled)

	def __setup_keyboard_hotkey_signals (self) -> None:
		self.__hotkey_combos = {}
		self.hotkey_pressed.connect(self.__evt_hotkey_pressed)
		Settings().signals().changed.connect(self.__setup_keyboard_hotkeys)

	def __setup_keyboard_hotkeys (self) -> None:
		for hotkey in Settings().tools.multicast.hotkeys.model_fields.keys():
			if hotkey not in self.__hotkey_combos.get(getattr(Settings().tools.multicast.hotkeys, hotkey), ()):
				break
		else:
			return
		logger.info('Registering hotkeys')
		try:
			self.__keyboard_listener.stop()
		except AttributeError:
			pass
		self.__hotkey_combos = {}
		for hotkey in Settings().tools.multicast.hotkeys.model_fields.keys():
			combo = LCAKeySequence(getattr(Settings().tools.multicast.hotkeys, hotkey)).to_keyboard_string()
			if not combo:
				continue
			self.__hotkey_combos[combo] = self.__hotkey_combos.get(combo, ()) + (hotkey,)
		logger.warning(self.__hotkey_combos)
		self.__keyboard_listener = pynput.keyboard.GlobalHotKeys({
			combo: ( lambda l_combo = combo : self.hotkey_pressed.emit(','.join(self.__hotkey_combos[l_combo])) )
				for combo in self.__hotkey_combos.keys()
		})
		self.__keyboard_listener.start()

	def _setup_layout (self) -> None:
		if wrapper_widget := QWidget():
			wrapper_layout = QHBoxLayout(wrapper_widget)
			wrapper_layout.setContentsMargins(*([wrapper_layout.spacing() * 2] * 3 + [0]))
			if widget := QFrame():
				widget.setProperty('css_class', 'accent_bordered')
				layout = QVBoxLayout(widget)
				if id_label := QLabel(
					'<html><h3 style="text-align: center;">'
					+ f'{Settings().series_from_id(self.__project.series_id).name} #{self.__project.entry_number}'
					+ '</h3></html>'
				):
					self.__id_label = id_label
					LCAProjectState().updated_model.connect(self.__update_id_label)
				layout.addWidget(id_label)
				if segment_cbo := LCAComboBox():
					self.__segment_cbo = segment_cbo
					self.__rebuild_segment_cbo()
					segment_cbo.currentDataChanged.connect(self.__evt_segment_changed)
				layout.addWidget(segment_cbo, 1)
				if controls_widget := QWidget():
					controls_widget.setStyleSheet(self.__BUTTONS_STYLESHEET)
					controls_layout = QHBoxLayout(controls_widget)
					controls_layout.setContentsMargins(0, 0, 0, 0)
					if startstop_btn := QPushButton(I18n(self).buttons.start):
						self.__startstop_btn = startstop_btn
						startstop_btn.setEnabled(False)
						startstop_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
						startstop_btn.clicked.connect(self.__evt_startstop_clicked)
					controls_layout.addWidget(startstop_btn, 1)
				layout.addWidget(controls_widget, 1)
			wrapper_layout.addWidget(widget)
		self.setCentralWidget(wrapper_widget)
		self.__setup_status_bar()
		self.__obs_thread.start()

	def __update_id_label (self, state: LCAProjectStateModel) -> None:
		text  = f'<html><h3 style="text-align: center;">'
		text += f'{Settings().series_from_id(state.project.series_id).name} #{state.project.entry_number}'
		if state.segment_id:
			text += ' &nbsp;&mdash;&nbsp; '
			text += Settings().series_segment_from_id(state.project.series_id, state.segment_id).name
			if state.segment_number:
				text += f' #{state.segment_number}'
		text += '</h3></html>'
		self.__id_label.setText(text)

	def __rebuild_segment_cbo (self) -> None:
		with QSignalBlocker(self.__segment_cbo):
			self.__segment_cbo.clear()
			self.__segment_cbo.setPlaceholderText(I18n(self).segment.select_placeholder)
			for segment in Settings().series_from_id(self.__project.series_id).segments:
				if segment.repeatable:
					i = 1
					while True:
						if f'{segment.id}-{i}' not in LCAProjectState().model.start_timestamps.keys():
							break
						i += 1
					self.__segment_cbo.addItem(f'{segment.name} #{i}', (segment.id, i))
				else:
					if f'{segment.id}-0' not in LCAProjectState().model.start_timestamps.keys():
						self.__segment_cbo.addItem(segment.name, (segment.id, 0))

	def __setup_status_bar (self) -> None:
		self.statusBar().setSizeGripEnabled(False)
		self.__status_lbl = QLabel()
		self.__status_lbl.setStyleSheet('margin-right: 0.3em; margin-bottom: 0.3em;')
		self.statusBar().addPermanentWidget(self.__status_lbl)
		self.__set_status_message(I18n(self).statuses.obs_connecting)

	def closeEvent (self, event: QCloseEvent) -> None:
		LCAProjectState().shutdown()
		self.__obs_thread.quit()
		with Settings():
			Settings().tools.multicast.profile[self.__project.series_id] = \
				Settings().ToolsModel.ToolsMulticastModel.ToolsMulticastProfileModel(
					geometry = base64.b64encode(bytes(self.saveGeometry())),
					state = base64.b64encode(bytes(self.saveState())),
				)
		self.__obs_thread.wait()
		event.accept()

	def __evt_segment_changed (self, segment_info: tuple[str, int | None]) -> None:
		segment_id, segment_number = segment_info
		if (LCAProjectState().model.segment_id == segment_id) and (LCAProjectState().model.segment_number == segment_number):
			return
		segment = Settings().series_segment_from_id(self.__project.series_id, segment_id)
		self.setEnabled(False)
		with LCAProjectState() as state:
			state.model.segment_id = segment_id
			state.model.segment_number = segment_number

	def __evt_startstop_clicked (self) -> None:
		if not LCAProjectState().model.segment_id and not LCAProjectState().model.active:
			return
		if LCAPopupMessage.info(
			I18n(self).confirm.stop if LCAProjectState().model.active else I18n(self).confirm.start,
			QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
		) != QMessageBox.StandardButton.Ok:
			return
		self.setEnabled(False)
		with LCAProjectState() as state:
			state.model.active = not state.model.active
			if not state.model.active:
				state.model.segment_id = None
				state.model.segment_number = 0

	def __set_status_message (self, msg: str) -> None:
		self.__status_lbl.setText(f'{msg}')

	@Slot(bool)
	def __slot_obs_connected (self, success: bool) -> None:
		self.setEnabled(success)
		self.__set_status_message(I18n(self).statuses.obs_connected if success else I18n(self).statuses.obs_connecting)

	@Slot(str)
	def __slot_obs_on_scene_changed (self, scene_name: str) -> None:
		self.setEnabled(True)
		self.__rebuild_segment_cbo()
		self.__startstop_btn.setText(I18n(self).buttons.stop if LCAProjectState().model.active else I18n(self).buttons.start)
		self.__startstop_btn.setEnabled(True)

	@Slot(bool)
	def __slot_obs_on_active_toggled (self, active: bool) -> None:
		self.setEnabled(True)
		self.__rebuild_segment_cbo()
		self.__startstop_btn.setText(I18n(self).buttons.stop if LCAProjectState().model.active else I18n(self).buttons.start)
		self.__set_status_message(I18n(self).statuses.obs_recording if active else I18n(self).statuses.obs_connected)

	def __evt_mistake_clicked (self) -> None:
		logger.warning('mistake')

	def __evt_mute_clicked (self) -> None:
		logger.warning('mute')

	def __evt_unmute_clicked (self) -> None:
		logger.warning('unmute')

	def __evt_clip_clicked (self) -> None:
		logger.warning('clip')

	@Slot(str)
	def __evt_hotkey_pressed (self, hotkeys: str) -> None:
		logger.debug(f'Pressed hotkeys: {hotkeys}')
		if not self.isEnabled():
			return
		for hotkey in hotkeys.split(','):
			getattr(self, f'__evt_{hotkey}_clicked')()

	def obs (self) -> LCAMObsRecordPuppeteerWorkerObject:
		return self.__obs_thread.worker

	def setEnabled (self, enabled: bool) -> None:
		super().setEnabled(enabled)
		# Also disable floating docks

