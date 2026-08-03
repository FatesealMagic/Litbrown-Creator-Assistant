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

from .LCACSettingsOrganizationSeriesVariantWidget import *
from ..LCACFormatHelperWidget import *
from ...LCATabbedDataViewWidget import *
from ...LCATabbedDataViewPanelWidget import *
from ...LCAToggleButtonGroupWidget import *
from ....common.LCATextTemplate import *

class LCACSettingsOrganizationSeriesWidget (LCATabbedDataViewPanelWidget):
	
	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		tab_widget = QTabWidget()
		for tab in ('general', 'variants', 'videoinfo', 'formatting',):
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
			#streamduration_spin.valueChanged.connect(lambda val : self._mapper.submit())
		layout.addRow(I18n(self).tabs.general.stream_duration, streamduration_spin)
		return widget

	def __build_variants_tab (self) -> QWidget:
		return LCATabbedDataViewWidget(
			LCATableModel( Settings().SeriesModel.VariantModel, lambda : Settings().series[self._model_row].variants, Settings ),
			LCACSettingsOrganizationSeriesVariantWidget,
			I18n(self).tabs.variants.typename,
			'name'
		)

	def __build_videoinfo_tab (self) -> QWidget:
		widget = QWidget()
		layout = QFormLayout(widget)
		#layout.setSpacing(layout.spacing() * 2)
		'''if format := LCAToggleButtonGroupWidget():
			format.addButton(I18n(self).tabs.videoinfo.longform, 'long')
			format.addButton(I18n(self).tabs.videoinfo.shortform, 'short')
			self._mapper.addMapping(format, self.model.get_column_index('video_format'))
			format.signal_changed.connect(self._mapper.submit)
		layout.addRow(I18n(self).tabs.videoinfo.format, format)'''
		if enabledoutputs_widget := QWidget():
			enabledoutputs_layout = QHBoxLayout(enabledoutputs_widget)
			enabledoutputs_layout.setContentsMargins(0, 0, 0, 0)
			enabledoutputs_layout.addWidget(QLabel(I18n(self).tabs.videoinfo.supported_outputs + ' '))
			self.__enabledoutputs_checkboxes = {}
			for i, output in enumerate(('stream', 'video', 'clip')):
				output_checkbox = QCheckBox(I18n(self).tabs.videoinfo[f'{output}info_tab_title'])
				self.__enabledoutputs_checkboxes[output] = output_checkbox
				output_checkbox.checkStateChanged.connect(
					lambda state, i=i: self.__videostream_tabwidget.widget(i).setEnabled(state == Qt.CheckState.Checked)
				)
				self._mapper.addMapping(output_checkbox, self.model.get_column_index(f'{output}.enabled'), b'checked')
				enabledoutputs_layout.addWidget(output_checkbox)
			enabledoutputs_layout.addStretch()
		layout.addWidget(enabledoutputs_widget)
		if videostream_tabwidget := QTabWidget():
			self.__videostream_tabwidget = videostream_tabwidget
			if stream_widget := QWidget():
				stream_layout = QFormLayout(stream_widget)
				stream_layout.setSpacing(stream_layout.spacing() * 2)
				if streamtitle_widget := QWidget():
					streamtitle_layout = QHBoxLayout(streamtitle_widget)
					streamtitle_layout.setContentsMargins(0, 0, 0, 0)
					if stream_title := QLineEdit():
						self._mapper.addMapping(stream_title, self.model.get_column_index('stream.title_template'))
					streamtitle_layout.addWidget(stream_title)
					streamtitle_layout.addWidget( LCACFormatHelperWidget(
						LCATextTemplate.VariableGroup.STREAM,
						stream_title,
						Qt.Orientation.Horizontal,
					) )
				stream_layout.addRow(I18n(self).tabs.videoinfo.stream_title, streamtitle_widget)
				if stream_to := QComboBox():
					self.__stream_to = stream_to
					stream_to.currentIndexChanged.connect(self.__stream_to_index_changed)
					stream_to.setItemDelegate(QStyledItemDelegate(stream_to))
				stream_layout.addRow(I18n(self).tabs.videoinfo.stream_to, stream_to)
				if stream_desc := QPlainTextEdit():
					if stream_desclbl_widget := QWidget():
						stream_desclbl_layout = QVBoxLayout(stream_desclbl_widget)
						stream_desclbl_layout.setContentsMargins(0, 0, 0, 0)
						stream_desclbl_layout.addWidget(QLabel(I18n(self).tabs.videoinfo.stream_desc))
						stream_desclbl_layout.addSpacing(stream_desclbl_layout.spacing() / 2)
						stream_desclbl_layout.addWidget( LCACFormatHelperWidget(
							LCATextTemplate.VariableGroup.STREAM,
							stream_desc,
							Qt.Orientation.Vertical,
						) )
						stream_desclbl_layout.addStretch()
					self._mapper.addMapping(stream_desc, self.model.get_column_index('stream.description_template'))
				stream_layout.addRow(stream_desclbl_widget, stream_desc)
				stream_widget.setEnabled(self.__enabledoutputs_checkboxes['stream'].isChecked())
			videostream_tabwidget.addTab(stream_widget, I18n(self).tabs.videoinfo.streaminfo_tab_title)
			if video_widget := QWidget():
				video_layout = QFormLayout(video_widget)
				video_layout.setSpacing(video_layout.spacing() * 2)
				if videotitle_widget := QWidget():
					videotitle_layout = QHBoxLayout(videotitle_widget)
					videotitle_layout.setContentsMargins(0, 0, 0, 0)
					if video_title := QLineEdit():
						self._mapper.addMapping(video_title, self.model.get_column_index('video.title_template'))
					videotitle_layout.addWidget(video_title)
					videotitle_layout.addWidget( LCACFormatHelperWidget(
						LCATextTemplate.VariableGroup.VIDEO,
						video_title,
						Qt.Orientation.Horizontal,
					) )
				video_layout.addRow(I18n(self).tabs.videoinfo.video_title, videotitle_widget)
				if video_to := QComboBox():
					self.__video_to = video_to
					video_to.currentIndexChanged.connect(self.__video_to_index_changed)
					video_to.setItemDelegate(QStyledItemDelegate(video_to))
				video_layout.addRow(I18n(self).tabs.videoinfo.video_to, video_to)
				if video_desc := QPlainTextEdit():
					if video_desclbl_widget := QWidget():
						video_desclbl_layout = QVBoxLayout(video_desclbl_widget)
						video_desclbl_layout.setContentsMargins(0, 0, 0, 0)
						video_desclbl_layout.addWidget(QLabel(I18n(self).tabs.videoinfo.video_desc))
						video_desclbl_layout.addSpacing(video_desclbl_layout.spacing() / 2)
						video_desclbl_layout.addWidget( LCACFormatHelperWidget(
							LCATextTemplate.VariableGroup.VIDEO,
							video_desc,
							Qt.Orientation.Vertical,
						) )
						video_desclbl_layout.addStretch()
					self._mapper.addMapping(video_desc, self.model.get_column_index('video.description_template'))
				video_layout.addRow(video_desclbl_widget, video_desc)
				video_widget.setEnabled(self.__enabledoutputs_checkboxes['video'].isChecked())
			videostream_tabwidget.addTab(video_widget, I18n(self).tabs.videoinfo.videoinfo_tab_title)
			if clip_widget := QWidget():
				clip_layout = QFormLayout(clip_widget)
				clip_layout.setSpacing(clip_layout.spacing() * 2)
				if cliptitle_widget := QWidget():
					cliptitle_layout = QHBoxLayout(cliptitle_widget)
					cliptitle_layout.setContentsMargins(0, 0, 0, 0)
					if clip_title := QLineEdit():
						self._mapper.addMapping(clip_title, self.model.get_column_index('clip.title_template'))
					cliptitle_layout.addWidget(clip_title)
					cliptitle_layout.addWidget( LCACFormatHelperWidget(
						LCATextTemplate.VariableGroup.CLIP,
						clip_title,
						Qt.Orientation.Horizontal,
					) )
				clip_layout.addRow(I18n(self).tabs.videoinfo.clip_title, cliptitle_widget)
				if clip_to := QComboBox():
					self.__clip_to = clip_to
					clip_to.currentIndexChanged.connect(self.__clip_to_index_changed)
					clip_to.setItemDelegate(QStyledItemDelegate(clip_to))
				clip_layout.addRow(I18n(self).tabs.videoinfo.clip_to, clip_to)
				if clip_desc := QPlainTextEdit():
					if clip_desclbl_widget := QWidget():
						clip_desclbl_layout = QVBoxLayout(clip_desclbl_widget)
						clip_desclbl_layout.setContentsMargins(0, 0, 0, 0)
						clip_desclbl_layout.addWidget(QLabel(I18n(self).tabs.videoinfo.clip_desc))
						clip_desclbl_layout.addSpacing(clip_desclbl_layout.spacing() / 2)
						clip_desclbl_layout.addWidget( LCACFormatHelperWidget(
							LCATextTemplate.VariableGroup.CLIP,
							clip_desc,
							Qt.Orientation.Vertical,
						) )
						clip_desclbl_layout.addStretch()
					self._mapper.addMapping(clip_desc, self.model.get_column_index('clip.description_template'))
				clip_layout.addRow(clip_desclbl_widget, clip_desc)
				clip_widget.setEnabled(self.__enabledoutputs_checkboxes['clip'].isChecked())
			videostream_tabwidget.addTab(clip_widget, I18n(self).tabs.videoinfo.clipinfo_tab_title)
			self.__rebuild_streamvideoclipto_comboboxes()
			Settings().signals().changed.connect(self.__rebuild_streamvideoclipto_comboboxes)
		layout.addRow(videostream_tabwidget)
		return widget

	def __build_formatting_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		if tab_widget := QTabWidget():
			if decklists_widget := QWidget():
				decklists_layout = QVBoxLayout(decklists_widget)
				if decklist_help_lbl := QLabel(I18n(self).tabs.formatting.decklists.info):
					decklist_help_lbl.setWordWrap(True)
				decklists_layout.addWidget(decklist_help_lbl)
				if decklists_tabwidget := QTabWidget():
					for decklists_type in ('stream', 'video', 'clip'):
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
		for combobox, key in (
			(self.__stream_to, 'stream.publish_to_membership_id'),
			(self.__video_to,  'video.publish_to_membership_id'),
			(self.__clip_to,   'clip.publish_to_membership_id'),
		):
			combobox.blockSignals(True)
			combobox.clear()
			combobox.addItem(I18n(self).tabs.videoinfo.membership_public, '~public')
			#combobox.insertSeparator(1)
			for tier in reversed(Settings().membership_tiers):
				combobox.addItem(tier.name + ' ' + I18n(self).tabs.videoinfo.membership_andup, tier.id)
			try:
				id_to_select = self.model.data(self.model.index(self._model_row, self.model.get_column_index(key)))
			except IndexError:
				return # This series has been removed
			i = combobox.findData(id_to_select)
			if i == -1:
				i = 0
			combobox.setCurrentIndex(i)
			combobox.blockSignals(False)

	def __stream_to_index_changed (self, i: int) -> None:
		logger.debug(i)
		self.model.setData(
			self.model.index(self._model_row, self.model.get_column_index('stream.publish_to_membership_id')),
			self.__stream_to.currentData()
		)

	def __video_to_index_changed (self, i: int) -> None:
		logger.debug(i)
		self.model.setData(
			self.model.index(self._model_row, self.model.get_column_index('video.publish_to_membership_id')),
			self.__video_to.currentData()
		)

	def __clip_to_index_changed (self, i: int) -> None:
		logger.debug(i)
		self.model.setData(
			self.model.index(self._model_row, self.model.get_column_index('clip.publish_to_membership_id')),
			self.__clip_to.currentData()
		)

