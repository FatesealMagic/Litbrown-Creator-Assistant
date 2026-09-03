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
from ..LCALabel import *
from ..LCAMainWindow import *
from ..LCAPluginWidget import *
from ..LCAPopupMessage import *
from ..LCASeparator import *
from ...common.LCAPluginManager import *
from ...common.LCAProjectState import *
from ...common.LCAKeySequence import *
from ...integrations.LCAIntegrationErrors import *
from ...models.LCAProjectFileModel import *
from ...threads.LCAWorkerThread import *
from ...threads.multicast.LCACFoobarControllerTaskThread import *
from ...threads.multicast.LCACMtgosdkObserveTaskThread import *
from ...threads.multicast.LCAMObsRecordPuppeteerWorkerObject import *

class LCAMMainWindow (LCAMainWindow):

	hotkey_pressed = Signal(str)

	__project: LCAProjectFileModel
	
	__id_label: LCALabel
	__segment_cbo: LCAComboBox
	__startstop_btn: QPushButton
	__status_lbl: LCALabel
	__plugins_menu: QMenu

	__obs_thread: LCAWorkerThread
	__mtgosdk_thread: LCACMtgosdkObserveTaskThread
	__foobar_thread: LCACFoobarControllerTaskThread

	__BUTTONS_STYLESHEET = 'font-size: 13pt; font-weight: bold; padding: 0.3em;'
	
	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.error(I18n(self).errors.need_slug)
			sys.exit()
		self.__status_lbls = {}
		self.__project = LCAProjectFileModel.from_slug(sys.argv[2])
		self.__initialize_project_state()
		self.__setup_obs_thread()
		self.__setup_mtgosdk_thread()
		self.__setup_foobar_thread()
		self.__setup_keyboard_hotkey_signals()
		self.__setup_keyboard_hotkeys()
		self.setWindowIcon(Assets.QIcon('icons/multicast.ico'))
		self.setWindowTitle(I18n(self).title)
		if profile := Settings().tools.multicast.profile.get(self.__project.series_id, None):
			for plugin in profile.loaded_plugins:
				self.__load_and_dock_plugin(plugin)
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

	def __setup_mtgosdk_thread (self, e: Exception | None = None) -> None:
		if isinstance(e, LCAIntegrationNotInitializedError):
			self.__update_integration_status('mtgosdk', False)
			return
		self.__update_integration_status('mtgosdk', None)
		self.__mtgosdk_thread = LCACMtgosdkObserveTaskThread()
		self.__mtgosdk_thread.error.connect(self.__setup_mtgosdk_thread)
		self.__mtgosdk_thread.update.connect(lambda _ : self.__update_integration_status('mtgosdk', True))
		self.__mtgosdk_thread.start()

	def __setup_foobar_thread (self, e: Exception | None = None) -> None:
		if isinstance(e, LCAIntegrationNotInitializedError):
			self.__update_integration_status('foobar', False)
			return
		self.__update_integration_status('foobar', None)
		self.__foobar_thread = LCACFoobarControllerTaskThread()
		self.__foobar_thread.error.connect(self.__setup_foobar_thread)
		self.__foobar_thread.update.connect(lambda _ : self.__update_integration_status('foobar', True))
		self.__foobar_thread.start()

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
				if id_label := LCALabel(
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
					controls_layout = QVBoxLayout(controls_widget)
					controls_layout.setContentsMargins(0, 0, 0, 0)
					if startstop_btn := QPushButton(I18n(self).buttons.start):
						self.__startstop_btn = startstop_btn
						startstop_btn.setStyleSheet('padding: 0.75em;')
						startstop_btn.setEnabled(False)
						startstop_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
						startstop_btn.clicked.connect(self.__evt_startstop_clicked)
					controls_layout.addWidget(startstop_btn)
					if addlbtns_widget := QWidget():
						addlbtns_layout = QHBoxLayout(addlbtns_widget)
						addlbtns_layout.setContentsMargins(0, 0, 0, 0)
						if mistake_btn := QPushButton(I18n(self).buttons.mistake):
							mistake_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
							mistake_btn.clicked.connect(self.__evt_mistake_clicked)
						addlbtns_layout.addWidget(mistake_btn)
						if muteunmute_btn := QPushButton(
							I18n(self).buttons.unmute
							if LCAProjectState().model.muted
							else I18n(self).buttons.mute
						):
							self.__muteunmute_btn = muteunmute_btn
							muteunmute_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
							muteunmute_btn.setCheckable(True)
							muteunmute_btn.setChecked(LCAProjectState().model.muted)
							muteunmute_btn.clicked.connect(self.__evt_muteunmute_clicked)
						addlbtns_layout.addWidget(muteunmute_btn)
					controls_layout.addWidget(addlbtns_widget)
				layout.addWidget(controls_widget, 1)
			wrapper_layout.addWidget(widget)
		self.setCentralWidget(wrapper_widget)
		self.__setup_status_bar()
		self.__obs_thread.start()
		self.setEnabled(True)

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
		self.__status_lbls = {}
		for integration in ('foobar', 'obs', 'mtgosdk'):
			if logo_lbl := QLabel():
				logo_lbl.setPixmap(Assets.QIcon(f'external/icons/{integration}.png').pixmap(QSize(24, 24)))
			self.statusBar().addPermanentWidget(logo_lbl)
			if status_lbl := QLabel():
				self.__status_lbls[integration] = status_lbl
				status_lbl.setPixmap(Assets.QIcon('icons/help.png').pixmap(QSize(24, 24)))
			self.statusBar().addPermanentWidget(status_lbl)
			self.statusBar().addPermanentWidget(LCASeparator.vertical())
		if plugins_btn := QPushButton(I18n(self).plugins.button):
			plugins_btn.setStyleSheet('margin-right: 0.7em; margin-bottom: 0.4em; margin-top: 0.4em; margin-left: 0.1em;')
			plugins_btn.clicked.connect(lambda : QMenu.exec(self.__build_plugins_menu(), QCursor.pos()))
		self.statusBar().addPermanentWidget(plugins_btn)

	def __build_plugins_menu (self) -> list[QAction]:
		actions = []
		for import_path, plugin_name in LCAPluginManager.list_plugins():
			action = QAction(plugin_name)
			action.triggered.connect(lambda _, l_import_path = import_path : self.__evt_toggle_plugin_activated(l_import_path))
			action.setCheckable(True)
			action.setChecked(LCAPluginManager.is_plugin_loaded(import_path))
			actions.append(action)
		return actions

	def closeEvent (self, event: QCloseEvent) -> None:
		LCAProjectState().shutdown()
		self.__obs_thread.quit()
		self.__mtgosdk_thread.requestInterruption()
		self.__foobar_thread.requestInterruption()
		with Settings():
			Settings().tools.multicast.profile[self.__project.series_id] = \
				Settings().ToolsModel.ToolsMulticastModel.ToolsMulticastProfileModel(
					geometry = base64.b64encode(bytes(self.saveGeometry())),
					state = base64.b64encode(bytes(self.saveState())),
					loaded_plugins = LCAPluginManager.list_loaded_plugins(),
				)
		self.__obs_thread.wait()
		self.__mtgosdk_thread.wait()
		self.__foobar_thread.wait()
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

	def __update_integration_status (self, integration: str, status: bool | None) -> None:
		if not self.__status_lbls.get(integration, None):
			return
		self.__status_lbls[integration].setPixmap(Assets.QIcon(f'icons/{ {
			None:  'help',
			True:  'ok',
			False: 'close',
		}[status] }.png').pixmap(24, 24))

	@Slot(bool)
	def __slot_obs_connected (self, success: bool) -> None:
		self.setEnabled(success)
		self.__update_integration_status('obs', True if success else None)

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

	def __evt_mistake_clicked (self) -> None:
		logger.warning(self.__class__.__module__)
		logger.warning(self.__class__.__qualname__)
		logger.info('Marking a mistake')
		with LCAProjectState() as state:
			state.model.mistake_count += 1

	def __evt_mute_clicked (self) -> None:
		logger.info('Muted')
		with LCAProjectState() as state:
			state.model.muted = True
		self.__muteunmute_btn.setChecked(True)
		self.__muteunmute_btn.setText(I18n(self).buttons.unmute)

	def __evt_unmute_clicked (self) -> None:
		logger.info('Unmuted')
		with LCAProjectState() as state:
			state.model.muted = False
		self.__muteunmute_btn.setChecked(False)
		self.__muteunmute_btn.setText(I18n(self).buttons.mute)

	def __evt_muteunmute_clicked (self) -> None:
		self.__evt_unmute_clicked() if LCAProjectState().model.muted else self.__evt_mute_clicked()

	def __evt_clip_clicked (self) -> None:
		logger.info('Clip')

	@Slot(str)
	def __evt_hotkey_pressed (self, hotkeys: str) -> None:
		logger.debug(f'Pressed hotkeys: {hotkeys}')
		muted = LCAProjectState().model.muted
		if not self.isEnabled():
			return
		for hotkey in hotkeys.split(','):
			if ((hotkey == 'muted') and muted) or ((hotkey == 'unmuted') and not muted):
				continue
			getattr(self, f'__evt_{hotkey}_clicked')()

	def __evt_toggle_plugin_activated (self, import_path: str) -> None:
		if LCAPluginManager.is_plugin_loaded(import_path):
			self.findChild(LCAPluginWidget, f'plugin.{import_path}').close()
		else:
			self.__load_and_dock_plugin(import_path)

	def __load_and_dock_plugin (self, import_path: str) -> None:
		dock = LCAPluginManager.load_plugin(self, import_path)
		if not dock:
			LCAPopupMessage.warning(I18n(self).errors.plugin_not_loaded)
			return
		self.addDockWidget(Qt.BottomDockWidgetArea, dock)
		dock.setFloating(True)

	def obs (self) -> LCAMObsRecordPuppeteerWorkerObject:
		return self.__obs_thread.worker

	def setEnabled (self, enabled: bool) -> None:
		super().setEnabled(enabled)

