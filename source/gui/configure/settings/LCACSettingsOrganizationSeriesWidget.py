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

from .LCACSettingsOrganizationSeriesSegmentWidget import LCACSettingsOrganizationSeriesSegmentWidget
from .LCACSettingsOrganizationSeriesVariantWidget import LCACSettingsOrganizationSeriesVariantWidget
from ..LCACFormatHelperWidget import LCACFormatHelperWidget
from ...LCALabel import LCALabel
from ...LCAListCreatorWidget import LCAListCreatorWidget
from ...LCASeparator import LCASeparator
from ...LCATabbedDataViewWidget import LCATabbedDataViewWidget
from ...LCATabbedDataViewPanelWidget import LCATabbedDataViewPanelWidget
from ...LCATableModel import LCATableModel
from ...LCAToggleButtonGroupWidget import LCAToggleButtonGroupWidget
from ....common.LCATextTemplate import LCATextTemplate

class LCACSettingsOrganizationSeriesWidget (LCATabbedDataViewPanelWidget):

	__CONTENT_TYPES = ('stream', 'video', 'clip')
	
	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		tab_widget = QTabWidget()
		for tab in ('general', 'variants', 'segments', 'output', 'formatting',):
			tab_widget.addTab(
				getattr(self, f'__build_{tab}_tab')(),
				I18n(self).tabs[tab].tab_title
			)
		layout.addWidget(tab_widget)
		self._finalize_mapper()

	def __build_general_tab (self) -> QWidget:
		widget = QWidget()
		layout = QFormLayout(widget)
		layout.setSpacing(layout.spacing() * 2)
		if name_edit := QLineEdit():
			name_edit.setReadOnly(False)
			self._mapper.addMapping(name_edit, self.model.get_column_index('name'))
		layout.addRow(I18n(self).tabs.general.name, name_edit)
		if id_edit := QLineEdit():
			id_edit.setReadOnly(True)
			self._mapper.addMapping(id_edit, self.model.get_column_index('id'))
		layout.addRow(I18n(self).tabs.general.id, id_edit)
		if streamduration_spin := QSpinBox():
			streamduration_spin.setMinimum(15)
			streamduration_spin.setMaximum(60 * 48)
			streamduration_spin.setSingleStep(15)
			self._mapper.addMapping(streamduration_spin, self.model.get_column_index('stream_duration'))
		layout.addRow(I18n(self).tabs.general.stream_duration, streamduration_spin)
		return widget

	def __build_variants_tab (self) -> QWidget:
		return LCATabbedDataViewWidget(
			LCATableModel( Settings().SeriesModel.VariantModel, lambda : Settings().series[self._model_row].variants, Settings ),
			LCACSettingsOrganizationSeriesVariantWidget,
			I18n(self).tabs.variants.typename,
			'name'
		)

	def __build_segments_tab (self) -> QWidget:
		return LCATabbedDataViewWidget(
			LCATableModel( Settings().SeriesModel.SegmentModel, lambda : Settings().series[self._model_row].segments, Settings ),
			LCACSettingsOrganizationSeriesSegmentWidget,
			I18n(self).tabs.segments.typename,
			'name'
		)

	def __build_output_tab (self) -> QWidget:
		widget = QWidget()
		layout = QFormLayout(widget)
		if enabledoutputs_widget := QWidget():
			enabledoutputs_layout = QHBoxLayout(enabledoutputs_widget)
			enabledoutputs_layout.setContentsMargins(0, 0, 0, 0)
			enabledoutputs_layout.addWidget(LCALabel(I18n(self).tabs.output.supported_outputs + ' '))
			self.__enabledoutputs_checkboxes = {}
			for i, output in enumerate(self.__CONTENT_TYPES):
				output_checkbox = QCheckBox(I18n(self).tabs.output.output_types[output] + ' ')
				self.__enabledoutputs_checkboxes[output] = output_checkbox
				output_checkbox.checkStateChanged.connect(
					lambda state, i=i: self.__videostream_tabwidget.widget(i).setEnabled(state == Qt.CheckState.Checked)
				)
				self._mapper.addMapping(output_checkbox, self.model.get_column_index(f'{output}.enabled'), b'checked')
				enabledoutputs_layout.addWidget(output_checkbox)
			enabledoutputs_layout.addStretch()
		layout.addWidget(enabledoutputs_widget)
		self.__content_to_cbos = {}
		if videostream_tabwidget := QTabWidget():
			self.__videostream_tabwidget = videostream_tabwidget
			for content_type in self.__CONTENT_TYPES:
				if content_widget := QWidget():
					content_layout = QVBoxLayout(content_widget)
					if content_tabwidget := QTabWidget():
						for content_tab_name in (
							('metadata', 'publishing', 'rendering') if content_type in ('video', 'clip')
							else ('metadata', 'publishing')
						):
							content_tabwidget.addTab(
								getattr(self, f'__build_content_{content_tab_name}_tab')(content_type),
								I18n(self).tabs.output.tabs[content_tab_name].tab_title
							)
					content_layout.addWidget(content_tabwidget)
				videostream_tabwidget.addTab(content_widget, I18n(self).tabs.output.output_types[content_type])
		layout.addRow(videostream_tabwidget)
		self.__rebuild_streamvideoclipto_comboboxes()
		Settings().signals().changed.connect(self.__rebuild_streamvideoclipto_comboboxes)
		return widget

	def __build_content_metadata_tab (self, content_type: str) -> QWidget:
		widget = QWidget()
		layout = QFormLayout(widget)
		if contenttitle_widget := QWidget():
			contenttitle_layout = QHBoxLayout(contenttitle_widget)
			contenttitle_layout.setContentsMargins(0, 0, 0, 0)
			if content_title := QLineEdit():
				self._mapper.addMapping(content_title, self.model.get_column_index(f'{content_type}.title_template'))
			contenttitle_layout.addWidget(content_title)
			contenttitle_layout.addWidget( LCACFormatHelperWidget(
				getattr(LCATextTemplate.VariableGroup, content_type.upper()),
				content_title,
				Qt.Orientation.Horizontal,
			) )
		layout.addRow(I18n(self).tabs.output.tabs.metadata.content_title, contenttitle_widget)
		if content_desc := QPlainTextEdit():
			if content_desclbl_widget := QWidget():
				content_desclbl_layout = QVBoxLayout(content_desclbl_widget)
				content_desclbl_layout.setContentsMargins(0, 0, 0, 0)
				content_desclbl_layout.addSpacing(content_desclbl_layout.spacing())
				content_desclbl_layout.addWidget(LCALabel(I18n(self).tabs.output.tabs.metadata.description))
				content_desclbl_layout.addSpacing(content_desclbl_layout.spacing())
				content_desclbl_layout.addWidget( LCACFormatHelperWidget(
					getattr(LCATextTemplate.VariableGroup, content_type.upper()),
					content_desc,
					Qt.Orientation.Vertical,
				) )
				content_desclbl_layout.addStretch()
			self._mapper.addMapping(content_desc, self.model.get_column_index(f'{content_type}.description_template'))
		layout.addRow(content_desclbl_widget, content_desc)
		return widget

	def __build_content_publishing_tab (self, content_type: str) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.addWidget(LCALabel(I18n(self).tabs.output.tabs.publishing.publish_to))
		if content_to := QComboBox(self):
			self.__content_to_cbos[content_type] = content_to
			content_to.currentIndexChanged.connect(
				lambda i, l_content_type = content_type : self.__content_to_index_changed(i, l_content_type)
			)
			content_to.setItemDelegate(QStyledItemDelegate(content_to))
		layout.addWidget(content_to)
		layout.addSpacing(layout.spacing())
		layout.addWidget(LCALabel(I18n(self).tabs.output.tabs.publishing.playlists))
		get_playlists = lambda : { playlist.id: playlist.title for playlist in Settings().integrations.youtube.playlists }
		if playlists_widget := LCAListCreatorWidget(LCAListCreatorWidget.Mode.COMBO, get_playlists()):
			self._mapper.addMapping(playlists_widget, self.model.get_column_index(f'{content_type}.add_to_playlists'))
			Settings().signals().changed.connect(lambda : playlists_widget.set_possible_selections(get_playlists()))
			playlists_widget.changed.connect(self._mapper.submit)
		layout.addWidget(playlists_widget)
		layout.addStretch()
		return widget

	def __build_content_rendering_tab (self, content_type: str) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.addWidget(LCALabel(I18n(self).tabs.output.tabs.rendering.start_scene))
		if start_scene := QLineEdit():
			self._mapper.addMapping(start_scene, self.model.get_column_index(f'{content_type}.starting_obs_scene'))
		layout.addWidget(start_scene)
		layout.addSpacing(layout.spacing())
		layout.addWidget(LCALabel(I18n(self).tabs.output.tabs.rendering.time_on_start_scene))
		if start_scene_time := QDoubleSpinBox():
			start_scene_time.setDecimals(2)
			start_scene_time.setMinimum(0)
			start_scene_time.setPrefix(I18n(self).tabs.output.tabs.rendering.time_on_start_scene_prefix)
			start_scene_time.setSuffix(I18n(self).tabs.output.tabs.rendering.time_on_start_scene_suffix)
			start_scene_time.setSingleStep(0.1)
			self._mapper.addMapping(start_scene_time, self.model.get_column_index(f'{content_type}.time_on_starting_obs_scene'))
		layout.addWidget(start_scene_time)
		layout.addWidget(LCASeparator.horizontal())
		layout.addWidget(LCALabel(I18n(self).tabs.output.tabs.rendering.autoeditor_margin))
		if autoeditor_margin := QDoubleSpinBox():
			autoeditor_margin.setDecimals(2)
			autoeditor_margin.setMinimum(0)
			autoeditor_margin.setPrefix(I18n(self).tabs.output.tabs.rendering.autoeditor_margin_prefix)
			autoeditor_margin.setSuffix(I18n(self).tabs.output.tabs.rendering.autoeditor_margin_suffix)
			autoeditor_margin.setSingleStep(0.1)
			self._mapper.addMapping(autoeditor_margin, self.model.get_column_index(f'{content_type}.autoeditor_margin'))
		layout.addWidget(autoeditor_margin)
		layout.addStretch()
		return widget

	def __build_formatting_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if tab_widget := QTabWidget():
			if decklists_widget := QWidget():
				decklists_layout = QVBoxLayout(decklists_widget)
				decklists_layout.addWidget(LCALabel(I18n(self).tabs.formatting.decklists.info))
				if decklists_tabwidget := QTabWidget():
					for decklists_type in self.__CONTENT_TYPES:
						if decklist_widget := QWidget():
							decklist_layout = QFormLayout(decklist_widget)
							if decklist_separator_widget := QPlainTextEdit():
								doc = decklist_separator_widget.document()
								fm = QFontMetrics(doc.defaultFont())
								margins = decklist_separator_widget.contentsMargins()
								decklist_separator_widget.setFixedHeight(
									fm.lineSpacing() * 5 +
									(doc.documentMargin() + decklist_separator_widget.frameWidth()) * 2 +
									margins.top() + margins.bottom()
								)
								decklist_separator_widget.setPlainText(self.model.data((
									self._model_row,
									f'{decklists_type}.decklist_separator'
								)))
								self._mapper.addMapping(
									decklist_separator_widget,
									self.model.get_column_index(f'{decklists_type}.decklist_separator')
								)
							decklist_layout.addRow(
								I18n(self).tabs.formatting.decklists[decklists_type].separator,
								decklist_separator_widget
							)
							if decklist_template := QPlainTextEdit():
								if decklist_templatelbl_widget := QWidget():
									decklist_templatelbl_layout = QVBoxLayout(decklist_templatelbl_widget)
									decklist_templatelbl_layout.setContentsMargins(0, 0, 0, 0)
									decklist_templatelbl_layout.addWidget(QLabel(
										I18n(self).tabs.formatting.decklists[decklists_type].decklist
									))
									decklist_templatelbl_layout.addSpacing(decklist_templatelbl_layout.spacing() / 2)
									decklist_templatelbl_layout.addWidget( LCACFormatHelperWidget(
										LCATextTemplate.VariableGroup.DECKLISTS,
										decklist_template,
										Qt.Orientation.Vertical,
									) )
									decklist_templatelbl_layout.addStretch()
								decklist_template.setPlainText(self.model.data((
									self._model_row,
									f'{decklists_type}.decklist_template'
								)))
								self._mapper.addMapping(decklist_template, self.model.get_column_index(f'{decklists_type}.decklist_template'))
							decklist_layout.addRow(decklist_templatelbl_widget, decklist_template)
						decklists_tabwidget.addTab(decklist_widget, I18n(self).tabs.formatting.decklists[decklists_type].tab_title)
					decklists_layout.addWidget(decklists_tabwidget)
			tab_widget.addTab(decklists_widget, I18n(self).tabs.formatting.decklists.tab_title)
			if timestamps_widget := QWidget():
				timestamps_layout = QFormLayout(timestamps_widget)
			tab_widget.addTab(timestamps_widget, I18n(self).tabs.formatting.timestamps.tab_title)
		layout.addWidget(tab_widget)
		return widget

	def __rebuild_streamvideoclipto_comboboxes (self) -> None:
		for content_type in self.__CONTENT_TYPES:
			combobox = self.__content_to_cbos[content_type]
			key = f'{content_type}.publish_to_membership_id'
			combobox.blockSignals(True)
			combobox.clear()
			combobox.addItem(I18n(self).tabs.output.membership.public, '~public')
			for tier in reversed(Settings().membership_tiers):
				combobox.addItem(tier.name + ' ' + I18n(self).tabs.output.membership.and_up, tier.id)
			try:
				id_to_select = self.model.data(self.model.index(self._model_row, self.model.get_column_index(key)))
			except IndexError:
				return # This series has been removed
			i = combobox.findData(id_to_select)
			if i == -1:
				i = 0
			combobox.setCurrentIndex(i)
			combobox.blockSignals(False)

	def __content_to_index_changed (self, i: int, content_type: str) -> None:
		self.model.setData(
			self.model.index(self._model_row, self.model.get_column_index(f'{content_type}.publish_to_membership_id')),
			self.__content_to_cbos[content_type].currentData()
		)

