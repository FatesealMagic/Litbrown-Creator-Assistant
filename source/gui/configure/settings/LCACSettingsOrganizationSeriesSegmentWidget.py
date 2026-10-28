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

from ....Config import Config
from ....I18n import I18n
from ....Assets import Assets
from ....Settings import Settings
from ....Util import Util

from ..LCACFormatHelperWidget import LCACFormatHelperWidget
from ...LCAFilePickerWidget import LCAFilePickerWidget
from ...LCALabel import LCALabel
from ...LCAListCreatorWidget import LCAListCreatorWidget
from ...LCASeparator import LCASeparator
from ...LCATabbedDataViewPanelWidget import LCATabbedDataViewPanelWidget
from ...LCAToggleButtonGroupWidget import LCAToggleButtonGroupWidget
from ....common.LCATextTemplate import LCATextTemplate

class LCACSettingsOrganizationSeriesSegmentWidget (LCATabbedDataViewPanelWidget):

	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		tab_widget = QTabWidget()
		for tab in ('general', 'obs', 'video'):
			tab_widget.addTab(
				getattr(self, f'__build_{tab}_tab')(),
				I18n(self).tabs[tab].title,
			)
		layout.addWidget(tab_widget)
		self._finalize_mapper()

	def __build_general_tab (self) -> QWidget:
		widget = QWidget()
		layout = QFormLayout(widget)
		layout.setSpacing(layout.spacing() * 2)
		if name_input := QLineEdit():
			self._mapper.addMapping(name_input, self.model.get_column_index('name'))
		layout.addRow(LCALabel(I18n(self).tabs.general.name), name_input)
		if id_input := QLineEdit():
			id_input.setReadOnly(True)
			self._mapper.addMapping(id_input, self.model.get_column_index('id'))
		layout.addRow(LCALabel(I18n(self).tabs.general.id), id_input)
		if repeatable_input := LCAToggleButtonGroupWidget(rows = 1):
			repeatable_input.addButton(I18n(self).tabs.general.repeatable.option_yes, True)
			repeatable_input.addButton(I18n(self).tabs.general.repeatable.option_no,  False)
			self._mapper.addMapping(repeatable_input, self.model.get_column_index('repeatable'))
			repeatable_input.set_value(self.model.data((self._model_row, 'repeatable')))
			repeatable_input.changed.connect(self._mapper.submit)
		layout.addRow(LCALabel(I18n(self).tabs.general.repeatable.label), repeatable_input)
		return widget

	def __build_obs_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.addWidget(LCALabel(I18n(self).tabs.obs.scene_name))
		if obsname_input := QLineEdit():
			self._mapper.addMapping(obsname_input, self.model.get_column_index('obs_scene_name'))
		layout.addWidget(obsname_input)
		layout.addWidget(LCALabel(I18n(self).tabs.obs.recording_name))
		if recordingname_input := QLineEdit():
			self._mapper.addMapping(recordingname_input, self.model.get_column_index('recording_source_name'))
		layout.addWidget(recordingname_input)
		layout.addWidget(LCASeparator.horizontal())
		layout.addWidget(LCALabel(I18n(self).tabs.obs.adread_scene_names))
		# TODO write and add the selection widget
		if adread_scenes := LCAListCreatorWidget():
			self._mapper.addMapping(adread_scenes, self.model.get_column_index('adread_scene_names'))
			adread_scenes.set_value(self.model.data((self._model_row, 'adread_scene_names')))
			adread_scenes.changed.connect(self._mapper.submit)
		layout.addWidget(adread_scenes)
		layout.addSpacing(layout.spacing())
		layout.addWidget(LCALabel(I18n(self).tabs.obs.adread_selection_behavior.title))
		if selection_behavior := LCAToggleButtonGroupWidget(rows = 1):
			selection_behavior.addButton(I18n(self).tabs.obs.adread_selection_behavior.in_order, 'in_order')
			selection_behavior.addButton(I18n(self).tabs.obs.adread_selection_behavior.random,   'random')
			self._mapper.addMapping(selection_behavior, self.model.get_column_index('adread_selection_behavior'))
			selection_behavior.set_value(self.model.data((self._model_row, 'adread_selection_behavior')))
			selection_behavior.changed.connect(self._mapper.submit)
		layout.addWidget(selection_behavior)
		return widget

	def __build_video_tab (self) -> QWidget:
		widget = QWidget()
		layout = QFormLayout(widget)
		layout.addRow(LCALabel(I18n(self).tabs.video.chapter))
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
		return widget

