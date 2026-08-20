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
  "#""

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Assets import *
from ...Config import *
from ...I18n import *
from ...Settings import *
from ...Util import *

from .LCAMMainWindow import *
from ..LCAComboBox import *
from ..LCAWidget import *
from ...models.LCAProjectFileModel import *
from ...threads.multicast.LCAMObsRecordPuppeteerWorkerObject import *

class LCAMSegmentTrackerWidget (LCAWidget):

	__window: LCAMMainWindow
	__worker: LCAMObsRecordPuppeteerWorkerObject
	__project: LCAProjectFileModel
	
	def __init__ (self,
		window: LCAMMainWindow,
		worker: LCAMObsRecordPuppeteerWorkerObject,
		project: LCAProjectFileModel,
	):
		self.__window = window
		self.__worker = worker
		self.__project = project
		super().__init__()
		worker.on_connected.connect(self.__slot_on_connected)
		worker.on_scene_changed.connect(self.__slot_on_scene_changed)

	def _setup_layout (self) -> None:
		hwrapper_layout = QHBoxLayout(self)
		if vwrapper_widget := QWidget():
			vwrapper_layout = QVBoxLayout(vwrapper_widget)
			if widget := QFrame():
				widget.setProperty('css_class', 'accent_bordered')
				layout = QVBoxLayout(widget)
				layout.addWidget(QLabel(
					f'<h3 style="text-align: center;">{Settings().series_from_id(self.__project.series_id).name} #{self.__project.entry_number}</h3>'
				))
				if segment_cbo := LCAComboBox():
					self.__segment_cbo = segment_cbo
					for segment in Settings().series_from_id(self.__project.series_id).segments:
						# TODO do this more intelligently, accounting for existing recorded segments
						segment_cbo.addItem(f'{segment.name} #1' if segment.repeatable else segment.name, segment.id)
					segment_cbo.currentDataChanged.connect(self.__evt_segment_changed)
				layout.addWidget(segment_cbo, 1)
				if controls_widget := QWidget():
					controls_layout = QHBoxLayout(controls_widget)
					controls_layout.setContentsMargins(0, 0, 0, 0)
					if start_btn := QPushButton(I18n(self).buttons.start):
						self.__start_btn = start_btn
					controls_layout.addWidget(start_btn, 1)
					if stop_btn := QPushButton(I18n(self).buttons.stop):
						self.__stop_btn = stop_btn
					controls_layout.addWidget(stop_btn, 1)
				layout.addWidget(controls_widget, 1)
			vwrapper_layout.addWidget(widget)
		hwrapper_layout.addWidget(vwrapper_widget)

	def __evt_segment_changed (self, segment_id: str) -> None:
		segment = Settings().series_segment_from_id(self.__project.series_id, segment_id)
		self.__window.setEnabled(False)
		self.__window.obs().do_scene_change.emit(segment.obs_scene_name)

	@Slot(bool)
	def __slot_on_connected (self, success: bool) -> None:
		self.__evt_segment_changed(self.__segment_cbo.currentData())

	@Slot(str)
	def __slot_on_scene_changed (self, scene_name: str) -> None:
		self.__window.setEnabled(True)

