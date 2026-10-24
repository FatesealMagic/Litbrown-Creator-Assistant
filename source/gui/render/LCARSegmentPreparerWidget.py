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

import pathlib
import subprocess
import xml.etree.ElementTree

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from ...Assets import Assets
from ...Config import Config
from ...I18n import I18n
from ...Settings import Settings
from ...Util import Util

from ..LCALabel import LCALabel
from ..LCAPopupMessage import LCAPopupMessage
from ..LCATaskTrackerWidget import LCATaskTrackerWidget
from ..LCAWidget import LCAWidget
from ...integrations.autoeditor.LCAAutoeditorIntegration import LCAAutoeditorIntegration
from ...integrations.shotcut.LCAShotcutIntegration import LCAShotcutIntegration
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...threads.render.LCARFootagePreparerTaskThread import LCARFootagePreparerTaskThread
from ...threads.render.LCARSegmentMelterTaskThread import LCARSegmentMelterTaskThread

class LCARSegmentPreparerWidget (QStackedWidget):

	complete = Signal(bool)

	__project: LCAProjectFileModel
	__segment_slug: str
	__segment_id: str
	__segment_number: int
	__shotcut_path: pathlib.Path
	__mistake_watcher: QFileSystemWatcher

	def __init__ (self,
		project: LCAProjectFileModel,
		segment_slug: str,
	):
		super().__init__()
		self.__project = project
		self.__segment_slug = segment_slug
		self.__segment_id, self.__segment_number = LCAProjectFileModel.split_slug(segment_slug)
		self.__shotcut_path = self.__project.path_shotcut(segment_id = self.__segment_id, segment_number = self.__segment_number)
		if autoeditor_widget := LCATaskTrackerWidget(
			label = Settings().series_segment_from_id(self.__project.series_id, self.__segment_id).name +
				(f' #{self.__segment_number}' if self.__segment_number else '') +
				' | ' + I18n(self).autoeditor_task,
			thread_factory = lambda : LCARFootagePreparerTaskThread(
				project = self.__project,
				segment_slug = self.__segment_slug,
			),
			integration = LCAAutoeditorIntegration,
			not_unstagable = True,
		):
			autoeditor_widget.result.connect(self.__evt_autoeditor_success)
		self.addWidget(autoeditor_widget)

	def launch_autoeditor (self) -> None:
		logger.warning(self.__segment_slug)
		self.widget(0).execute()
		if self.widget(0).status == LCATaskTrackerWidget.Status.SKIPPED:
			self.complete.emit(True)

	def __evt_autoeditor_success (self, _) -> None:
		if widget := QWidget():
			layout = QHBoxLayout(widget)
			layout.setContentsMargins(0, 0, 0, 0)
			layout.addWidget(LCALabel(
				'<html><h3>' +
				Settings().series_segment_from_id(self.__project.series_id, self.__segment_id).name +
				(f' #{self.__segment_number}' if self.__segment_number else '') +
				'</h3></html>'
			), 7)
			if mistake_label := LCALabel():
				self.__mistake_label = mistake_label
			layout.addWidget(mistake_label, 2)
			if shotcut_btn := QPushButton(' ' + I18n(self).open_shotcut):
				shotcut_btn.setIcon(Assets.QIcon('external/icons/shotcut.png'))
				shotcut_btn.clicked.connect(self.__evt_open_shotcut)
			layout.addWidget(shotcut_btn, 2)
		self.addWidget(widget)
		self.setCurrentIndex(1)
		if mistake_watcher := QFileSystemWatcher():
			self.__mistake_watcher = mistake_watcher
			mistake_watcher.addPath(str(self.__shotcut_path.resolve()))
			mistake_watcher.fileChanged.connect(self.__update_mistake_count)
		self.__update_mistake_count()
		
	def __update_mistake_count (self) -> None:
		logger.debug(f'Updating mistake count for segment {self.__segment_slug}')
		mlt = xml.etree.ElementTree.parse(str(self.__shotcut_path.resolve()))
		num_mistakes = len(mlt.getroot().findall('./tractor[@id="tractor0"]/properties[@name="shotcut:markers"]/properties'))
		if num_mistakes:
			self.__mistake_label.setText(f'<html><b>\u26A0\uFE0F{num_mistakes}</b></html>')
		else:
			self.__evt_no_mistakes()

	def __evt_open_shotcut (self) -> None:
		if LCAShotcutIntegration.is_initialized():
			subprocess.Popen([Config().integrations.local.shotcut.shotcut_executable_location, str(self.__shotcut_path.resolve())])
		else:
			LCAPopupMessage.warning(I18n(self).errors.shotcut_not_installed)
			Util.launch_new_instance('config', ['shotcut'])

	def __evt_no_mistakes (self) -> None:
		if melt_widget := LCATaskTrackerWidget(
			label = Settings().series_segment_from_id(self.__project.series_id, self.__segment_id).name +
				(f' #{self.__segment_number}' if self.__segment_number else '') +
				' | ' + I18n(self).melt_task,
			thread_factory = lambda : LCARSegmentMelterTaskThread(
				project = self.__project,
				segment_slug = self.__segment_slug,
			),
			integration = LCAShotcutIntegration,
			not_unstagable = True,
		):
			melt_widget.result.connect(self.__evt_melt_success)
			melt_widget.execute()
		self.addWidget(melt_widget)
		self.setCurrentIndex(2)

	def __evt_melt_success (self) -> None:
		self.complete.emit(True)

