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
from ...I18n import I18n
from ...Settings import Settings

from .LCARSegmentPreparerWidget import LCARSegmentPreparerWidget
from ..LCAConnectionLabelWidget import LCAConnectionLabelWidget
from ..LCAContentDetailsEditingWidget import LCAContentDetailsEditingWidget
from ..LCALabel import LCALabel
from ..LCAMainWindow import LCAMainWindow
from ..LCAPopupMessage import LCAPopupMessage
from ..LCASeparator import LCASeparator
from ..LCASideTabWidget import LCASideTabWidget
from ..LCATableModel import LCATableModel
from ..LCATaskTrackerWidget import LCATaskTrackerWidget
from ...integrations.autoeditor.LCAAutoeditorIntegration import LCAAutoeditorIntegration
from ...integrations.youtube.LCAYoutubeIntegration import LCAYoutubeIntegration
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...threads.LCAWorkerThread import LCAWorkerThread
from ...threads.render.LCARFinalRenderWorkerObject import LCARFinalRenderWorkerObject
from ...threads.render.LCARFootagePreparerTaskThread import LCARFootagePreparerTaskThread
from ...threads.render.LCARYoutubeVideoPublishTaskThread import LCARYoutubeVideoPublishTaskThread

class LCARMainWindow (LCAMainWindow):

	__TAB_NAMES = ('prepare', 'render', 'review', 'publish')

	__project: LCAProjectFileModel
	__model: LCATableModel[LCAProjectFileModel]
	__prepare_scroll_area: QScrollArea
	__start_render_btn: QPushButton
	__preparer_widgets: list[LCARSegmentPreparerWidget]
	__render_scroll_area: QScrollArea
	__start_review_btn: QPushButton
	__render_thread: LCAWorkerThread[LCARFinalRenderWorkerObject] | None = None
	__details_widget: LCAContentDetailsEditingWidget
	__youtube_publish_private: LCATaskTrackerWidget
	__youtube_publish_unlisted: LCATaskTrackerWidget | None = None

	def _initialize_window (self) -> None:
		if len(sys.argv) <= 2:
			LCAPopupMessage.error(I18n(self).errors.need_slug)
			sys.exit()
		self.setWindowIcon(Assets.QIcon('icons/render.ico'))
		self.__project = LCAProjectFileModel.from_slug(sys.argv[2])
		self.__model = LCATableModel(LCAProjectFileModel, lambda : [self.__project], self.__project)
		self.setWindowTitle(f'{I18n(self).title} | {Settings().series_from_id(self.__project.series_id).name} #{self.__project.entry_number}')
		self.resize(710, 900)

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
		if val and preparer in self.__preparer_widgets:
			self.__preparer_widgets.remove(preparer)
		if not val and preparer not in self.__preparer_widgets:
			self.__preparer_widgets.append(preparer)
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
		self.__reset_render_scroll_area()
		self.__restart_render_btn.setEnabled(True)
		self.__start_review_btn.setEnabled(False)
		self.__render_thread = LCAWorkerThread(LCARFinalRenderWorkerObject(self.__project))
		self.__render_thread.worker.task_started.connect(self.__evt_render_task_started)
		self.__render_thread.worker.task_success.connect(self.__evt_render_task_success)
		self.__render_thread.worker.task_failure.connect(self.__evt_render_task_failure)
		self.__render_thread.worker.complete.connect(self.__evt_render_complete)
		self.__render_thread.start()
		logger.debug('after render thread start')

	def __build_render_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if scroll_area := QScrollArea():
			self.__render_scroll_area = scroll_area
			scroll_area.setWidgetResizable(True)
			scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
			scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
			self.__reset_render_scroll_area()
		layout.addWidget(scroll_area)
		if btns_widget := QWidget():
			btns_layout = QHBoxLayout(btns_widget)
			btns_layout.setContentsMargins(0, 0, 0, 0)
			if restart_render_btn := QPushButton(' ' + I18n(self).tabs.render.restart_render):
				self.__restart_render_btn = restart_render_btn
				restart_render_btn.setProperty('css_class', 'big')
				restart_render_btn.setIcon(Assets.QIcon('icons/refresh.png'))
				restart_render_btn.clicked.connect(self.__evt_restart_render)
			btns_layout.addWidget(restart_render_btn)
			if start_review_btn := QPushButton(' ' + I18n(self).tabs.render.start_review):
				self.__start_review_btn = start_review_btn
				start_review_btn.setEnabled(False)
				start_review_btn.setProperty('css_class', 'big')
				start_review_btn.setIcon(Assets.QIcon('icons/advance.png'))
				start_review_btn.clicked.connect(self.__evt_start_review_clicked)
			btns_layout.addWidget(start_review_btn)
		layout.addWidget(btns_widget)
		return widget

	def __reset_render_scroll_area (self) -> None:
		old_widget = self.__render_scroll_area.takeWidget()
		if old_widget:
			old_widget.deleteLater()
		scroll_widget = QWidget()
		scroll_layout = QVBoxLayout(scroll_widget)
		scroll_layout.addStretch()
		self.__render_scroll_area.setWidget(scroll_widget)

	def __evt_restart_render (self) -> None:
		if self.__render_thread:
			self.__restart_render_btn.setEnabled(False)
			self.__render_thread.requestInterruption()
		else:
			self.__evt_start_render()

	def __evt_start_review_clicked (self) -> None:
		self.__regenerate_video_texts()
		self.__details_widget.refresh()
		self.centralWidget().setCurrentIndex(2)

	def __evt_render_task_started (self, task: str) -> None:
		label = LCALabel(f'\u23F3 {getattr(I18n(self).tabs.render.tasks, task)}')
		label.setObjectName(task)
		self.__render_scroll_area.widget().layout().addWidget(label)

	def __evt_render_task_success (self, task: str) -> None:
		self.findChild(LCALabel, name = task).setText(f'\u2705 {getattr(I18n(self).tabs.render.tasks, task)}')

	def __evt_render_task_failure (self, task: str) -> None:
		self.findChild(LCALabel, name = task).setText(f'\u274C {getattr(I18n(self).tabs.render.tasks, task)}')

	def __evt_render_complete (self) -> None:
		self.__render_thread.quit()
		self.__render_thread.wait()
		self.__render_thread = None
		if self.__restart_render_btn.isEnabled():
			self.__start_review_btn.setEnabled(True)
		else:
			self.__evt_start_render()

	def __build_review_tab (self) -> QWidget:
		mapper = QDataWidgetMapper(self)
		mapper.setModel(self.__model)
		mapper.setCurrentIndex(0)
		self.__mapper = mapper
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if title_hook := QLineEdit():
			mapper.addMapping(title_hook, self.__model.get_column_index('video.title_hook'))
			title_hook.setPlaceholderText(I18n(self).tabs.review.placeholder_title_hook)
			title_hook.editingFinished.connect(self.__regenerate_video_texts)
		layout.addWidget(title_hook)
		if description_hook := QLineEdit():
			mapper.addMapping(description_hook, self.__model.get_column_index('video.description_hook'))
			description_hook.setPlaceholderText(I18n(self).tabs.review.placeholder_description_hook)
			description_hook.editingFinished.connect(self.__regenerate_video_texts)
		layout.addWidget(description_hook)
		if details_widget := LCAContentDetailsEditingWidget(self.__model, 'video'):
			self.__details_widget = details_widget
		layout.addWidget(details_widget)
		if publish_btn := QPushButton(' ' + I18n(self).tabs.review.publish):
			publish_btn.setProperty('css_class', 'big')
			publish_btn.setIcon(Assets.QIcon('icons/advance.png'))
			publish_btn.clicked.connect(self.__evt_display_publish_clicked)
		layout.addWidget(publish_btn)
		mapper.revert()
		self.__regenerate_video_texts()
		return widget

	def __regenerate_video_texts (self) -> None:
		with self.__project:
			self.__project.generate_content_texts('video')
		self.__details_widget.reload_content_texts()

	def __evt_display_publish_clicked (self) -> None:
		self.centralWidget().setCurrentIndex(3)

	def __build_publish_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if publish_scrollarea := QScrollArea():
			publish_scrollarea.setWidgetResizable(True)
			publish_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
			publish_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
			if publish_widget := QWidget():
				publish_layout = QVBoxLayout(publish_widget)
				if youtube_widget := QWidget():
					youtube_layout = QVBoxLayout(youtube_widget)
					youtube_layout.setSpacing(youtube_layout.spacing() * 2)
					youtube_layout.addWidget(LCAConnectionLabelWidget('youtube'))
					if youtube_publish_private := LCATaskTrackerWidget(
						label = I18n(self).tabs.publish.youtube_publish_private.title,
						thread_factory = lambda : LCARYoutubeVideoPublishTaskThread(
							project = self.__project,
							privacy = 'private',
						),
						integration = LCAYoutubeIntegration,
					):
						self.__youtube_publish_private = youtube_publish_private
						youtube_publish_private.error.connect(
							lambda e : self.__evt_publish_error(e, 'youtube_publish_private')
						)
						youtube_publish_private.result.connect(
							lambda r : self.__evt_publish_result(r,  'youtube_publish_private')
						)
					youtube_layout.addWidget(youtube_publish_private)
					if Settings().series_from_id(self.__project.series_id).video.publish_to_membership_id != '~public':
						if youtube_publish_unlisted := LCATaskTrackerWidget(
							label = I18n(self).tabs.publish.youtube_publish_unlisted.title,
							thread_factory = lambda : LCARYoutubeVideoPublishTaskThread(
								project = self.__project,
								privacy = 'unlisted',
							),
							integration = LCAYoutubeIntegration,
						):
							self.__youtube_publish_unlisted = youtube_publish_unlisted
							youtube_publish_unlisted.error.connect(
								lambda e : self.__evt_publish_error(e, 'youtube_publish_unlisted')
							)
							youtube_publish_unlisted.result.connect(
								lambda r : self.__evt_publish_result(r,  'youtube_publish_unlisted')
							)
						youtube_layout.addWidget(youtube_publish_unlisted)
				publish_layout.addWidget(youtube_widget)
				publish_layout.addStretch()
			publish_scrollarea.setWidget(publish_widget)
		layout.addWidget(publish_scrollarea)
		if publish_btn := QPushButton(' ' + I18n(self).tabs.publish.publish):
			publish_btn.setProperty('css_class', 'big')
			publish_btn.setIcon(Assets.QIcon('icons/advance.png'))
			publish_btn.clicked.connect(self.__evt_start_publish)
		layout.addWidget(publish_btn)
		return widget

	def __evt_start_publish (self) -> None:
		self.__youtube_publish_private.execute()
		if self.__youtube_publish_unlisted:
			self.__youtube_publish_unlisted.execute()

	def __evt_publish_error (self,
		e: Exception,
		key: str,
	) -> None:
		logger.warning(key)

	def __evt_publish_result (self,
		result: object,
		key: str,
	) -> None:
		logger.info(key)

