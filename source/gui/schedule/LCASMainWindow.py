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

import collections
import string
import sys
import time

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Config import *
from ...I18n import *
from ...Assets import *
from ...Util import *

from ..LCACarouselWidget import *
from ..LCAMainWindow import *
from ..LCAPopupMessage import *
from ..LCASideTabWidget import *
from ..LCATableModel import *
from ..LCAWebEngineView import *
from .LCASDetailsEditingWidget import *
from .LCASScheduleEditingWidget import *
from .LCASPublishManagerWidget import *
from ...models.LCAProjectFileModel import *
from ...threads.LCATaskThreadGroup import *
from ...threads.common.LCADeckFetcherTaskThread import *

class LCASMainWindow (LCAMainWindow):
	
	__TAB_NAMES = ('create', 'preview', 'details', 'publish')
	__BTN_STYLESHEET = 'QPushButton { font-size: 14pt; font-weight: bold; qproperty-iconSize: 20px; }'
	
	__model: LCATableModel[LCAProjectFileModel]
	
	def _initialize_window (self) -> None:
		if not Settings().series:
			LCAPopupMessage.info(I18n(self).errors.need_content_series)
			Util.launch_new_instance('configure')
			sys.exit() # QCoreApplication.exit() doesn't work here...
		self.setWindowIcon(Assets.QIcon('icons/schedule.ico'))
		self.setWindowTitle(I18n(self).title)
		self.resize(820, 820)
		self.__model = LCATableModel(LCAProjectFileModel)

	def _setup_layout (self) -> None:
		central_widget = LCASideTabWidget(orientation = Qt.Orientation.Horizontal, enabled = False, headers = False)
		for tab in self.__TAB_NAMES:
			central_widget.addWidget(
				getattr(self, f'__build_{tab}_tab')(),
				I18n(self).tabs[tab].name,
			)
		central_widget.setCurrentIndex(0)
		self.setCentralWidget(central_widget)

	def __build_create_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		self.__schedule_edit_widget = LCASScheduleEditingWidget(self.__model)
		layout.addWidget(self.__schedule_edit_widget, 1)
		if preview_btn := QPushButton(' ' + I18n(self).tabs.create.preview_btn):
			self.__preview_btn = preview_btn
			preview_btn.setStyleSheet(self.__BTN_STYLESHEET)
			preview_btn.setIcon(Assets.QIcon('icons/next.png'))
			preview_btn.clicked.connect(self.__evt_create_moveto_preview)
		layout.addWidget(preview_btn)
		return widget

	def __build_preview_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if viewer := LCAWebEngineView():
			self.__viewer = viewer
			viewer.setFixedSize(512, 512)
			viewer.setZoomFactor(0.5)
			viewer.setUrl(f'http://127.0.0.1:42967/{Settings().tools.schedule.render_file}')
		layout.addWidget(viewer, alignment = Qt.AlignHCenter)
		if title_text := QLineEdit():
			self.__title_text = title_text
			title_text.setPlaceholderText(I18n(self).tabs.preview.title_placeholder)
		layout.addWidget(title_text)
		if notes_text := QPlainTextEdit():
			self.__notes_text = notes_text
			notes_text.setPlaceholderText(I18n(self).tabs.preview.notes_placeholder)
		layout.addWidget(notes_text)
		if buttons_widget := QWidget():
			buttons_widget.setStyleSheet(self.__BTN_STYLESHEET)
			buttons_layout = QHBoxLayout(buttons_widget)
			buttons_layout.setContentsMargins(0, 0, 0, 0)
			if back_btn := QPushButton(' ' + I18n(self).tabs.preview.back_btn):
				back_btn.setIcon(Assets.QIcon('icons/prev.png'))
				back_btn.clicked.connect(self.__evt_preview_moveto_create)
			buttons_layout.addWidget(back_btn)
			if movetodetails_btn := QPushButton(' ' + I18n(self).tabs.preview.details_btn):
				self.__movetodetails_btn = movetodetails_btn
				movetodetails_btn.setIcon(Assets.QIcon('icons/save.png'))
				movetodetails_btn.setEnabled(False)
				movetodetails_btn.clicked.connect(self.__evt_preview_moveto_details)
			buttons_layout.addWidget(movetodetails_btn)
		layout.addWidget(buttons_widget)
		return widget

	def __build_details_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if details_widget := LCASDetailsEditingWidget(self.__model):
			self.__details_widget = details_widget
		layout.addWidget(details_widget)
		if buttons_widget := QWidget():
			buttons_widget.setStyleSheet(self.__BTN_STYLESHEET)
			buttons_layout = QHBoxLayout(buttons_widget)
			buttons_layout.setContentsMargins(0, 0, 0, 0)
			if publish_btn := QPushButton(' ' + I18n(self).tabs.details.publish_btn):
				publish_btn.setIcon(Assets.QIcon('icons/advance.png'))
				publish_btn.clicked.connect(self.__evt_details_moveto_publish)
			buttons_layout.addWidget(publish_btn)
		layout.addWidget(buttons_widget)
		return widget

	def __build_publish_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if publishmanager_widget := LCASPublishManagerWidget(self.__get_publish_thread_params):
			self.__publishmanager_widget = publishmanager_widget
		layout.addWidget(publishmanager_widget, 1)
		if buttons_widget := QWidget():
			buttons_widget.setStyleSheet(self.__BTN_STYLESHEET)
			buttons_layout = QHBoxLayout(buttons_widget)
			buttons_layout.setContentsMargins(0, 0, 0, 0)
			if publish_btn := QPushButton(' ' + I18n(self).tabs.publish.publish_btn):
				self.__publish_btn = publish_btn
				publish_btn.setIcon(Assets.QIcon('icons/advance.png'))
				publish_btn.clicked.connect(self.__evt_publish_finalize)
			buttons_layout.addWidget(publish_btn)
		layout.addWidget(buttons_widget)
		return widget

	def __evt_create_moveto_preview (self) -> None:
		if not len(self.__model.get_data_reference()):
			LCAPopupMessage.info(I18n(self).errors.need_a_multicast)
			return
		self.setEnabled(False)
		logger.debug(self.__model)
		self.__decklists_thread_group = LCATaskThreadGroup(self.__create_decklist_threads())
		self.__decklists_thread_group.error.connect(self.__signal_decklists_error)
		self.__decklists_thread_group.result.connect(self.__signal_decklists_result)
		self.__decklists_thread_group.complete.connect(self.__signal_decklists_complete)
		self.__decklists_thread_group.start()

	def __create_decklist_threads (self) -> list[LCADeckFetcherTaskThread]:
		ret = []
		for project in self.__model.get_data_reference():
			for i in range(len(project.decklists)):
				ret.append(LCADeckFetcherTaskThread(project = project, deck_index = i, save_project = False))
		return ret

	def __signal_decklists_error (self, error: tuple[LCATaskThread, Exception, dict[LCATaskThread, object]]) -> None:
		if type(error[1]) is ValueError:
			LCAPopupMessage.error(f'{I18n(self).errors.decklist_bad_url} {error[1]}')
		elif type(error[1]) is LCAIntegrationNotInitializedError:
			if not self.isEnabled():
				LCAPopupMessage.error(I18n(self).errors.decklist_notinitialized)
		elif type(error[1]) is LCAIntegrationUserForbiddenError:
			if not self.isEnabled():
				LCAPopupMessage.error(I18n(self).errors.decklist_unauthorized)
		else:
			LCAPopupMessage.error(I18n(self).errors.decklist_other)

	def __signal_decklists_result (self, _) -> None:
		pass

	def __signal_decklists_complete (self, _) -> None:
		self.setEnabled(True)
		if not self.__generate_stream_texts():
			return
		self.__movetodetails_btn.setEnabled(False)
		self.centralWidget().setCurrentIndex(1)
		self.__set_viewer_data()

	def __generate_stream_texts (self) -> bool:
		for multicast in self.__model.get_data_reference():
			try:
				multicast.generate_stream_texts()
			except (ValueError, KeyError) as e:
				logger.exception(e)
				LCAPopupMessage.error(string.Template(I18n(self).errors.bad_template).substitute(
					series_name = Settings().series_from_id(multicast.series_id).name,
				))
				Util.launch_new_instance('configure')
				return False
		return True

	def __set_viewer_data (self) -> None:
		self.__viewer.page().runJavaScript(f'''
			((data) => {Settings().tools.schedule.render_function}(data))({{
				'schedule': {json.dumps([ project.model_dump(mode='json') for project in self.__model.get_data_reference() ])},
				'settings': {Settings().model_dump_json()},
			}});
		''')
		self.__movetodetails_btn.setEnabled(True)

	def __evt_preview_moveto_create (self) -> None:
		self.__movetodetails_btn.setEnabled(False)
		self.centralWidget().setCurrentIndex(0)

	def __evt_preview_moveto_details (self) -> None:
		for project in self.__model.get_data_reference():
			with project:
				pass # Save each project
		self.__details_widget.refresh()
		self.centralWidget().setCurrentIndex(2)
		self.__take_viewer_screenshot()

	def __take_viewer_screenshot (self) -> None:
		# TODO See if there is a better way to accomplish this.
		# I wanted to take 1024x1024 screenshots while only displaying a 512x512 view to the user.
		# As far as I can tell, doing this requires an ugly resize of the underlying Chromium instance.
		# Detach and resize
		self.__viewer.setZoomFactor(1)
		self.__viewer.setParent(None)
		self.__viewer.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
		self.__viewer.setFixedSize(1024, 1024)
		self.__viewer.show()
		# Wait 5 seconds ... I couldn't figure out how to accurately see if the window had resized or not
		loop = QEventLoop()
		QTimer.singleShot(5000, loop.quit)
		loop.exec()
		# Save the screenshot and destroy the underlying instance
		self.__viewer.save_screenshot(Settings().tools.schedule.output_file)
		self.__viewer.setUrl('about:blank')
		QCoreApplication.processEvents()
		self.__viewer.deleteLater()
		self.__viewer = None

	def __evt_details_moveto_publish (self) -> None:
		self.centralWidget().setCurrentIndex(3)

	def __evt_publish_finalize (self) -> None:
		self.__publish_btn.setEnabled(False)
		self.__publishmanager_widget.do_publish()

	def __get_publish_thread_params (self) -> dict:
		return {
			'data': self.__model.get_data_reference(),
			'schedule_title': self.__title_text.text(),
			'schedule_desc': self.__notes_text.toPlainText(),
		}
			
