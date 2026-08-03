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

from ..LCAMainWindow import *
from ..LCAPopupMessage import *
from ..LCASideTabWidget import *
from ..LCAWebEngineView import *
from .LCASScheduleEditingWidget import *
from .LCASPublishManagerWidget import *
from ...models.LCAProjectFileModel import *
from ...threads.LCAThreadGroup import *
from ...threads.common.LCADeckFetcherThread import *

class LCASMainWindow (LCAMainWindow):
	
	__TAB_NAMES = ('create', 'preview', 'publish')
	__BTN_STYLESHEET = 'QPushButton { font-size: 14pt; font-weight: bold; qproperty-iconSize: 20px; }'
	
	__model: LCATableModel[LCAProjectFileModel]
	
	def _initialize_window (self) -> None:
		if not Settings().series:
			LCAPopupMessage.info(I18n(self).errors.need_content_series)
			Util.launch_new_instance('configure')
			sys.exit() # QCoreApplication.exit() doesn't work here...
		self.setWindowIcon(Assets.QIcon('icons/schedule.ico'))
		self.setWindowTitle(I18n(self).title)
		self.resize(800, 800)
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
			preview_btn.clicked.connect(self.__evt_preview_clicked)
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
			'''doc = self.__notes_text.document()
			fm = QFontMetrics(doc.defaultFont())
			margins = self.__notes_text.contentsMargins()
			self.__notes_text.setFixedHeight(
				fm.lineSpacing() * 3 +
				(doc.documentMargin() + self.__notes_text.frameWidth()) * 2 +
				margins.top() + margins.bottom()
			)'''
		layout.addWidget(notes_text)
		if buttons_widget := QWidget():
			buttons_widget.setStyleSheet(self.__BTN_STYLESHEET)
			buttons_layout = QHBoxLayout(buttons_widget)
			buttons_layout.setContentsMargins(0, 0, 0, 0)
			if back_btn := QPushButton(' ' + I18n(self).tabs.preview.back_btn):
				back_btn.setIcon(Assets.QIcon('icons/undo.png'))
				back_btn.clicked.connect(self.__evt_revise_clicked)
			buttons_layout.addWidget(back_btn)
			if movetopublish_btn := QPushButton(' ' + I18n(self).tabs.preview.publish_btn):
				self.__movetopublish_btn = movetopublish_btn
				movetopublish_btn.setIcon(Assets.QIcon('icons/next.png'))
				movetopublish_btn.setEnabled(False)
				movetopublish_btn.clicked.connect(self.__evt_movetopublish_clicked)
			buttons_layout.addWidget(movetopublish_btn)
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
			if back_btn := QPushButton(' ' + I18n(self).tabs.publish.back_btn):
				self.__back_btn = back_btn
				back_btn.setIcon(Assets.QIcon('icons/undo.png'))
				back_btn.clicked.connect(self.__evt_backbtn_clicked)
			buttons_layout.addWidget(back_btn)
			if publish_btn := QPushButton(' ' + I18n(self).tabs.publish.publish_btn):
				self.__publish_btn = publish_btn
				publish_btn.setIcon(Assets.QIcon('icons/advance.png'))
				publish_btn.clicked.connect(self.__evt_finalize_publish)
			buttons_layout.addWidget(publish_btn)
		layout.addWidget(buttons_widget)
		return widget

	def __evt_preview_clicked (self) -> None:
		self.setEnabled(False)
		logger.debug(self.__model)
		self.__decklists_thread_group = LCAThreadGroup(self.__create_decklist_threads())
		self.__decklists_thread_group.error.connect(self.__signal_decklists_error)
		self.__decklists_thread_group.result.connect(self.__signal_decklists_result)
		self.__decklists_thread_group.start()

	def __create_decklist_threads (self) -> list[LCADeckFetcherThread]:
		ret = []
		for project in self.__model.get_data_reference():
			for i in range(len(project.decklists)):
				ret.append(LCADeckFetcherThread(project = project, deck_index = i, save_project = False))
		return ret

	def __signal_decklists_error (self, error: tuple[LCAThread, Exception, dict[LCAThread, object]]) -> None:
		self.setEnabled(True)
		if type(error[1]) is ValueError:
			LCAPopupMessage.error(f'{I18n(self).errors.decklist_bad_url} {error[1]}')
		else:
			LCAPopupMessage.error(I18n(self).errors.decklist_other)

	def __signal_decklists_result (self, result: dict[LCAThread, object]) -> None:
		self.setEnabled(True)
		if not self.__generate_stream_texts():
			return
		self.__movetopublish_btn.setEnabled(False)
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

	def __signal_decklists_complete (self, success: bool) -> None:
		self.setEnabled(True)
		self.centralWidget().setCurrentIndex(1 if success else 0)

	def __set_viewer_data (self) -> None:
		self.__viewer.page().runJavaScript(f'''
			((data) => {Settings().tools.schedule.render_function}(data))({{
				'schedule': {json.dumps([ project.model_dump(mode='json') for project in self.__model.get_data_reference() ])},
				'settings': {Settings().model_dump_json()},
			}});
		''')
		self.__movetopublish_btn.setEnabled(True)

	def __evt_revise_clicked (self) -> None:
		self.__movetopublish_btn.setEnabled(False)
		self.centralWidget().setCurrentIndex(0)

	def __evt_backbtn_clicked (self) -> None:
		self.centralWidget().setCurrentIndex(1)

	def __evt_movetopublish_clicked (self) -> None:
		self.__viewer.save_screenshot(Settings().tools.schedule.output_file)
		self.centralWidget().setCurrentIndex(2)

	def __evt_finalize_publish (self) -> None:
		self.__back_btn.setEnabled(False)
		self.__publish_btn.setEnabled(False)
		for project in self.__model.get_data_reference():
			logger.debug(project)
			with project:
				pass # Save each project
		self.__publishmanager_widget.do_publish()

	def __get_publish_thread_params (self) -> dict:
		return {
			'data': self.__model.get_data_reference(),
			'schedule_title': self.__title_text.text(),
			'schedule_desc': self.__notes_text.toPlainText(),
		}
			
