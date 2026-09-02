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

from ....I18n import *
from ....Settings import *

from ...LCALabel import *
from ...LCASeparator import *
from ...LCAWidget import *

class LCACObsWidget (LCAWidget):

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		layout.addWidget(LCALabel(I18n(self).info)
		if grid_widget := QWidget():
			grid_layout = QGridLayout(grid_widget)
			grid_layout.addWidget(LCALabel(I18n(self).connect.host), 0, 1, alignment = Qt.AlignHCenter)
			grid_layout.addWidget(LCALabel(I18n(self).connect.port), 0, 2, alignment = Qt.AlignHCenter)
			grid_layout.addWidget(LCALabel(I18n(self).connect.pswd), 0, 3, alignment = Qt.AlignHCenter)
			grid_layout.addWidget(LCASeparator.horizontal(),           1, 0, 1, 4)
			grid_layout.addWidget(LCALabel(I18n(self).instances.record + ' '), 2, 0, alignment = Qt.AlignRight)
			grid_layout.addWidget(LCALabel(I18n(self).instances.stream + ' '), 3, 0, alignment = Qt.AlignRight) # TODO do i need this?
			grid_layout.addWidget(LCALabel(I18n(self).instances.video  + ' '), 4, 0, alignment = Qt.AlignRight)
			grid_layout.addWidget(LCALabel(I18n(self).instances.clip   + ' '), 5, 0, alignment = Qt.AlignRight)
			for i, instance in enumerate(('record', 'stream', 'video', 'clip')):
				for p, property in enumerate(('host', 'port', 'pswd')):
					line_edit = QLineEdit()
					Settings().bind(line_edit, f'integrations.obs.{instance}.{property}')
					grid_layout.addWidget( line_edit, i + 2, p + 1 )
		layout.addWidget(grid_widget)
		layout.addStretch(1)

