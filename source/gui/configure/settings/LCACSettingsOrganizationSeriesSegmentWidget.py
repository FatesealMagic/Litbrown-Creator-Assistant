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

from ....Config import *
from ....I18n import *
from ....Assets import *
from ....Settings import *
from ....Util import *

from ..LCACFormatHelperWidget import *
from ...LCAFilePickerWidget import *
from ...LCALabel import *
from ...LCASeparator import *
from ...LCATabbedDataViewPanelWidget import *
from ...LCAToggleButtonGroupWidget import *
from ....common.LCATextTemplate import *

class LCACSettingsOrganizationSeriesSegmentWidget (LCATabbedDataViewPanelWidget):

	def _setup_layout (self) -> None:
		layout = QFormLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		if name_input := QLineEdit():
			self._mapper.addMapping(name_input, self.model.get_column_index('name'))
		layout.addRow(LCALabel(I18n(self).name), name_input)
		if id_input := QLineEdit():
			id_input.setReadOnly(True)
			self._mapper.addMapping(id_input, self.model.get_column_index('id'))
		layout.addRow(LCALabel(I18n(self).id), id_input)
		if repeatable_input := LCAToggleButtonGroupWidget(rows = 1):
			repeatable_input.addButton(I18n(self).repeatable.option_yes, True)
			repeatable_input.addButton(I18n(self).repeatable.option_no,  False)
			self._mapper.addMapping(repeatable_input, self.model.get_column_index('repeatable'))
			repeatable_input.set_value(self.model.data((self._model_row, 'repeatable')))
			repeatable_input.changed.connect(self._mapper.submit)
		layout.addRow(LCALabel(I18n(self).repeatable.label), repeatable_input)
		if obsname_input := QLineEdit():
			self._mapper.addMapping(obsname_input, self.model.get_column_index('obs_scene_name'))
		layout.addRow(LCALabel(I18n(self).obs_scene_name), obsname_input)
		layout.addRow(LCASeparator.horizontal())
		layout.addRow(LCALabel(I18n(self).chapter))
		if chapter_widget := QWidget():
			chapter_layout = QHBoxLayout(chapter_widget)
			chapter_layout.setContentsMargins(0, 0, 0, 0)
			if chapter_input := QLineEdit():
				self._mapper.addMapping(chapter_input, self.model.get_column_index('chapter_name'))
			chapter_layout.addWidget(chapter_input)
			chapter_layout.addWidget( LCACFormatHelperWidget(
				LCATextTemplate.VariableGroup.CHAPTERS,
				chapter_input,
				Qt.Orientation.Horizontal,
			) )
		layout.addRow(chapter_widget)
		self._finalize_mapper()

