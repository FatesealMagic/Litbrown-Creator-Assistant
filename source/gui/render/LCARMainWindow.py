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
import xml.etree.ElementTree

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Assets import Assets
from ...Config import Config
from ...I18n import I18n
from ...Settings import Settings
from ...Util import Util

from .LCARSegmentPreparerWidget import LCARSegmentPreparerWidget
from ..LCASeparator import LCASeparator
from ..LCALabel import LCALabel
from ..LCAMainWindow import LCAMainWindow
from ..LCAPopupMessage import LCAPopupMessage
from ..LCASideTabWidget import LCASideTabWidget
from ..LCATaskTrackerWidget import LCATaskTrackerWidget
from ...integrations.autoeditor.LCAAutoeditorIntegration import LCAAutoeditorIntegration
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...threads.render.LCARFootagePreparerTaskThread import LCARFootagePreparerTaskThread

class LCARMainWindow (LCAMainWindow):

	__TAB_NAMES = ('prepare', 'render', 'publish')

	__project: LCAProjectFileModel
	__prepare_scroll_area: QScrollArea
	__preparer_widgets: list[LCARSegmentPreparerWidget]
	__edit_scroll_area: QScrollArea

	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.error(I18n(self).errors.need_slug)
			sys.exit()
		self.setWindowIcon(Assets.QIcon('icons/render.ico'))
		self.__project = LCAProjectFileModel.from_slug(sys.argv[2])
		self.setWindowTitle(f'{I18n(self).title} | {Settings().series_from_id(self.__project.series_id).name} #{self.__project.entry_number}')
		self.resize(450, 600)

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
				refresh_btn.clicked.connect(lambda : scroll_area.setWidget(self.__construct_prepare_segments_widget()))
			btns_layout.addWidget(refresh_btn)
			if start_autoeditor_btn := QPushButton(' ' + I18n(self).tabs.prepare.start_autoeditor):
				start_autoeditor_btn.setProperty('css_class', 'big')
				start_autoeditor_btn.setIcon(Assets.QIcon('icons/advance.png'))
				start_autoeditor_btn.clicked.connect(self.__evt_do_prepare)
			btns_layout.addWidget(start_autoeditor_btn)
		layout.addWidget(btns_widget)
		if start_render_btn := QPushButton(' ' + I18n(self).tabs.prepare.start_render_yes):
			self.__start_render_btn = start_render_btn
			start_render_btn.setCheckable(True)
			start_render_btn.setChecked(True)
			start_render_btn.setVisible(False)
			start_render_btn.setProperty('css_class', 'big')
			start_render_btn.setIcon(Assets.QIcon('icons/advance.png'))
			start_render_btn.clicked.connect(self.__evt_start_render_clicked)
		layout.addWidget(start_render_btn)
		return widget

	def __construct_prepare_segments_widget (self) -> QWidget:
		old_widget = self.__prepare_scroll_area.takeWidget()
		if old_widget:
			old_widget.deleteLater()
		self.__preparer_widgets = []
		widget = QWidget()
		layout = QVBoxLayout(widget)
		for segment_slug in self.__project.all_segment_slugs():
			if len(self.__preparer_widgets):
				layout.addWidget(LCASeparator.horizontal())
			preparer_widget = LCARSegmentPreparerWidget(self.__project, segment_slug)
			preparer_widget.complete.connect(lambda val, l_preparer = preparer_widget : self.__evt_preparer_complete(val, l_preparer))
			self.__preparer_widgets.append(preparer_widget)
			layout.addWidget(preparer_widget)
		layout.addStretch()
		return widget

	def __evt_do_prepare (self) -> None:
		self.__prepare_btns_widget.hide()
		self.__start_render_btn.show()
		for preparer in self.__preparer_widgets.copy():
			preparer.launch_autoeditor()

	@Slot(bool)
	def __evt_preparer_complete (self, val: bool, preparer: LCARSegmentPreparerWidget) -> None:
		logger.debug(self.__preparer_widgets)
		logger.debug(val)
		logger.debug(preparer in self.__preparer_widgets)
		if val and preparer in self.__preparer_widgets:
			self.__preparer_widgets.remove(preparer)
		if not val and preparer not in self.__preparer_widgets:
			self.__preparer_widgets.append(preparer)
		logger.debug(self.__preparer_widgets)
		if not self.__preparer_widgets:
			if self.__start_render_btn.isChecked():
				self.__evt_start_render()
			else:
				self.__start_render_btn.setCheckable(False)
				self.__start_render_btn.setText(' ' + I18n(self).tabs.prepare.start_render)

	def __evt_start_render_clicked (self) -> None:
		if self.__start_render_btn.isCheckable():
			self.__start_render_btn.setText(
				' ' + getattr(I18n(self).tabs.prepare, f'start_render_{'yes' if self.__start_render_btn.isChecked() else 'no'}')
			)
		else:
			self.__evt_start_render()

	def __evt_start_render (self) -> None:
		self.centralWidget().setCurrentIndex(1)

	def __build_render_tab (self) -> QWidget:
		return QLabel('render')

	def __build_publish_tab (self) -> QWidget:
		return QLabel('publish')

