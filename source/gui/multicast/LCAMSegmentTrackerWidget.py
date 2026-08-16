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

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Assets import *
from ...Config import *
from ...I18n import *
from ...Settings import *
from ...Util import *

from ..LCAComboBox import *
from ..LCAWidget import *
from ...models.LCAProjectFileModel import *

class LCAMSegmentTrackerWidget (LCAWidget):
	
	__project: LCAProjectFileModel
	
	def __init__ (self, project: LCAProjectFileModel):
		self.__project = project
		super().__init__()

	def _setup_layout (self) -> None:
		wrapper_layout = QHBoxLayout(self)
		wrapper_layout.addStretch()
		if widget := QFrame():
			widget.setProperty('css_class', 'accent_bordered')
			layout = QVBoxLayout(widget)
			layout.addStretch()
			if segment_cbo := LCAComboBox():
				for segment in Settings().series_from_id(self.__project.series_id).segments:
					# TODO do this more intelligently, accounting for existing recorded segments
					segment_cbo.addItem(f'{segment.name} #1' if segment.repeatable else segment.name, segment.id)
				segment_cbo.currentDataChanged.connect(self.__evt_segment_changed)
			layout.addWidget(segment_cbo)
			if controls_widget := QWidget():
				controls_layout = QHBoxLayout(controls_widget)
				controls_layout.setContentsMargins(0, 0, 0, 0)
				if start_btn := QPushButton(I18n(self).buttons.start):
					self.__start_btn = start_btn
				controls_layout.addWidget(start_btn)
				if stop_btn := QPushButton(I18n(self).buttons.stop):
					self.__stop_btn = stop_btn
				controls_layout.addWidget(stop_btn)
			layout.addWidget(controls_widget)
			layout.addStretch()
		wrapper_layout.addWidget(widget)
		wrapper_layout.addStretch()

	def __evt_segment_changed (self, segment_id: str) -> None:
		pass

