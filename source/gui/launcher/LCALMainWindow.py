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

import string
import subprocess

import munch

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ...Assets import *
from ...I18n import *
from ...Util import *

from ..LCAComboBox import *
from ..LCAMainWindow import *
from ..LCASideTabWidget import *
from ...common.LCAProjectWatcher import *
from ...models.LCAProjectFileModel import *

class LCALMainWindow (LCAMainWindow):
	
	__LAUNCHBTN_STYLESHEET = 'QPushButton { font-size: 14pt; font-weight: bold; padding: 0.2em; }'
	
	def _initialize_window (self) -> None:
		self.setWindowIcon(Assets.QIcon('icons/assistant.ico'))
		self.setWindowTitle(I18n(self).title)
		self.resize(500, 300)
		self.__project_watcher = LCAProjectWatcher()

	def _setup_layout (self) -> None:
		central_widget = LCASideTabWidget()
		for tab in ('home', 'configure', 'schedule', 'multicast', 'thumbnail', 'render'):
			central_widget.addWidget(
				getattr(self, f'__build_{tab}_tab')(),
				I18n(self).tabs[tab].title,
				f'icons/{tab}.ico'
			)
		central_widget.setCurrentIndex(0)
		self.setCentralWidget(central_widget)

	def __build_home_tab (self) -> QWidget:
		if tab_widget := QTabWidget():
			if general_tab_widget := QWidget():
				general_tab_layout = QVBoxLayout(general_tab_widget)
				if intro_label := QLabel(I18n(self).tabs.home.intro):
					intro_label.setWordWrap(True)
				general_tab_layout.addWidget(intro_label)
				general_tab_layout.addStretch(1)
				if contact_label := QLabel(I18n(self).tabs.home.contact):
					contact_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
					contact_label.setOpenExternalLinks(True)
					contact_label.setWordWrap(True)
				general_tab_layout.addWidget(contact_label)
			tab_widget.addTab(general_tab_widget, I18n(self).tabs.home.tabs.general)
			if license_tab_widget := QTextBrowser():
				license_tab_widget.setReadOnly(True)
				license_tab_widget.setOpenExternalLinks(True)
				license_tab_widget.setHtml(Assets.text('license-apgl-3.0.html'))
			tab_widget.addTab(license_tab_widget, I18n(self).tabs.home.tabs.license)
			if credits_tab_widget := QTextBrowser():
				credits_tab_widget.setReadOnly(True)
				credits_tab_widget.setOpenExternalLinks(True)
				credits_tab_widget.setHtml(Assets.text('credits.html'))
			tab_widget.addTab(credits_tab_widget, I18n(self).tabs.home.tabs.credits)
		return tab_widget
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if content_label := QLabel(I18n(self).tabs.home.intro):
			content_label.setWordWrap(True)
		layout.addWidget(content_label)
		layout.addStretch(1)
		if license_label := QLabel(I18n(self).tabs.home.license):
			license_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
			license_label.setOpenExternalLinks(True)
			license_label.setWordWrap(True)
		layout.addWidget(license_label)
		if contact_label := QLabel(I18n(self).tabs.home.contact):
			contact_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
			contact_label.setOpenExternalLinks(True)
			contact_label.setWordWrap(True)
		layout.addWidget(contact_label)
		return widget

	def __build_configure_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if content_label := QLabel(I18n(self).tabs.configure.intro):
			content_label.setWordWrap(True)
		layout.addWidget(content_label)
		layout.addStretch(1)
		if launch_btn := QPushButton(I18n(self).tabs.configure.launch):
			launch_btn.setStyleSheet(self.__LAUNCHBTN_STYLESHEET)
			launch_btn.clicked.connect(self.__evt_configure_launched)
		layout.addWidget(launch_btn)
		return widget

	def __build_schedule_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if content_label := QLabel(I18n(self).tabs.schedule.intro):
			content_label.setWordWrap(True)
		layout.addWidget(content_label)
		layout.addStretch(1)
		if launch_btn := QPushButton(I18n(self).tabs.schedule.launch):
			launch_btn.setStyleSheet(self.__LAUNCHBTN_STYLESHEET)
			launch_btn.clicked.connect(self.__evt_schedule_launched)
		layout.addWidget(launch_btn)
		return widget

	def __build_multicast_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if content_label := QLabel(I18n(self).tabs.multicast.intro):
			content_label.setWordWrap(True)
		layout.addWidget(content_label)
		layout.addStretch(1)
		if multicast_selector := LCAComboBox():
			self.__multicast_selector = multicast_selector
			multicast_selector.setPlaceholderText(I18n(self).tabs.multicast.selector_placeholder)
			self.__project_watcher.directoryChanged.connect(self.__rebuild_multicast_selector)
			self.__project_watcher.fileChanged.connect(self.__rebuild_multicast_selector)
		layout.addWidget(multicast_selector)
		if launch_btn := QPushButton(I18n(self).tabs.multicast.launch):
			self.__multicast_launch_btn = launch_btn
			launch_btn.setStyleSheet(self.__LAUNCHBTN_STYLESHEET)
			launch_btn.clicked.connect(self.__evt_multicast_launched)
		layout.addWidget(launch_btn)
		self.__rebuild_multicast_selector()
		multicast_selector.currentDataChanged.connect(lambda : launch_btn.setEnabled(True))
		return widget

	def __build_thumbnail_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if content_label := QLabel(I18n(self).tabs.thumbnail.intro):
			content_label.setWordWrap(True)
		layout.addWidget(content_label)
		layout.addStretch(1)
		if launch_btn := QPushButton(I18n(self).tabs.thumbnail.launch):
			launch_btn.setStyleSheet(self.__LAUNCHBTN_STYLESHEET)
			launch_btn.clicked.connect(self.__evt_thumbnail_launched)
		layout.addWidget(launch_btn)
		return widget

	def __build_render_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if content_label := QLabel(I18n(self).tabs.render.intro):
			content_label.setWordWrap(True)
		layout.addWidget(content_label)
		layout.addStretch(1)
		if launch_btn := QPushButton(I18n(self).tabs.render.launch):
			launch_btn.setStyleSheet(self.__LAUNCHBTN_STYLESHEET)
			launch_btn.clicked.connect(self.__evt_render_launched)
		layout.addWidget(launch_btn)
		return widget

	def __rebuild_multicast_selector (self) -> None:
		self.__multicast_launch_btn.setEnabled(False)
		with QSignalBlocker(self.__multicast_selector):
			self.__multicast_selector.clear()
			for series_id, entry_number in LCAProjectFileModel.get_existing_slugs_split():
				try:
					series = Settings().series_from_id(series_id)
					self.__multicast_selector.addItem(
						f'{series.name} #{entry_number}',
						LCAProjectFileModel.slug(series_id, entry_number),
					)
				except ValueError:
					continue

	def __evt_configure_launched (self) -> None:
		Util.launch_new_instance('configure')

	def __evt_schedule_launched (self) -> None:
		Util.launch_new_instance('schedule')

	def __evt_multicast_launched (self) -> None:
		Util.launch_new_instance('multicast', [self.__multicast_selector.currentData()])

	def __evt_edit_launched (self) -> None:
		Util.launch_new_instance('edit', [self.__edit_combo.currentData()])

	def __evt_thumbnail_launched (self) -> None:
		Util.launch_new_instance('thumbnail', [])

	def __evt_render_launched (self) -> None:
		Util.launch_new_instance('render', [self.__render_combo.currentData()])

