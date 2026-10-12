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

import functools
import sys

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Assets import Assets
from ...Config import Config
from ...I18n import I18n
from ...Settings import Settings
from ...Util import Util

from ..LCAMainWindow import LCAMainWindow
from ..LCAPopupMessage import LCAPopupMessage
from ..LCASideTabWidget import LCASideTabWidget
from ..LCATaskTrackerWidget import LCATaskTrackerWidget
from ...integrations.autoeditor.LCAAutoeditorIntegration import LCAAutoeditorIntegration
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...threads.render.LCARFootagePreparerTaskThread import LCARFootagePreparerTaskThread

class LCARMainWindow (LCAMainWindow):

	__TAB_NAMES = ('prepare', 'edit', 'render')
	
	__prepare_scroll_area: QScrollArea
	__prepare_task_results: dict[LCATaskTrackerWidget, bool | None]

	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.error(I18n(self).errors.need_slug)
			sys.exit()
		self.setWindowIcon(Assets.QIcon('icons/render.ico'))
		self.__project = LCAProjectFileModel.from_slug(sys.argv[2])
		self.setWindowTitle(f'{I18n(self).title} | {Settings().series_from_id(self.__project.series_id).name} #{self.__project.entry_number}')
		self.resize(600, 400)

	def _setup_layout (self) -> None:
		central_widget = LCASideTabWidget(orientation = Qt.Orientation.Horizontal, enabled = False, headers = False)
		for tab in self.__TAB_NAMES:
			central_widget.addWidget(
				getattr(self, f'__build_{tab}_tab')(),
				I18n(self).tabs[tab].name,
			)
		central_widget.setCurrentIndex(0)
		self.setCentralWidget(central_widget)

	def __build_prepare_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if scroll_area := QScrollArea():
			self.__prepare_scroll_area = scroll_area
			scroll_area.setWidgetResizable(True)
			scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
			scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
			scroll_area.setWidget(self.__construct_prepare_segments_widget())
		layout.addWidget(scroll_area)
		if btns_widget := QWidget():
			self.__prepare_btns_widget = btns_widget
			btns_layout = QHBoxLayout(btns_widget)
			btns_layout.setContentsMargins(0, 0, 0, 0)
			if refresh_btn := QPushButton(' ' + I18n(self).tabs.prepare.refresh):
				refresh_btn.setProperty('css_class', 'big')
				refresh_btn.setIcon(Assets.QIcon('icons/refresh.png'))
				refresh_btn.clicked.connect(self.__construct_prepare_segments_widget)
			btns_layout.addWidget(refresh_btn)
			if proceed_btn := QPushButton(' ' + I18n(self).tabs.prepare.proceed):
				proceed_btn.setProperty('css_class', 'big')
				proceed_btn.setIcon(Assets.QIcon('icons/advance.png'))
				proceed_btn.clicked.connect(self.__evt_do_prepare)
			btns_layout.addWidget(proceed_btn)
		layout.addWidget(btns_widget)
		return widget

	def __construct_prepare_segments_widget (self) -> QWidget:
		old_widget = self.__prepare_scroll_area.takeWidget()
		if old_widget:
			old_widget.deleteLater()
		self.__prepare_task_results = {}
		widget = QWidget()
		layout = QVBoxLayout(widget)
		for segment_slug in self.__project.all_segment_slugs():
			segment_id, segment_number = LCAProjectFileModel.split_slug(segment_slug)
			task_tracker_widget = LCATaskTrackerWidget(
				label = Settings().series_segment_from_id(self.__project.series_id, segment_id).name +
					(f' #{segment_number}' if segment_number else ''),
				thread_factory = functools.partial(
					LCARFootagePreparerTaskThread,
					project = self.__project,
					segment_slug = segment_slug,
				),
				integration = LCAAutoeditorIntegration,
				not_unstagable = True,
			)
			layout.addWidget(task_tracker_widget)
			self.__prepare_task_results[task_tracker_widget] = None
		return widget

	def __evt_do_prepare (self) -> None:
		self.__prepare_btns_widget.setEnabled(False)
		for task in self.__prepare_task_results.keys():
			task.complete.connect(functools.partial(self.__evt_prepare_complete, task = task))
			task.execute()

	def __evt_prepare_complete (self, task: LCATaskTrackerWidget, complete: bool) -> None:
		self.__prepare_task_results[task] = complete
		logger.debug(self.__prepare_task_results)
		if None not in self.__prepare_task_results.values() and False not in self.__prepare_task_results.values():
			self.centralWidget().setCurrentIndex(1)

	def __build_edit_tab (self) -> QWidget:
		return QLabel('edit')

	def __build_render_tab (self) -> QWidget:
		return QLabel('render')

