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

from ....Assets import Assets
from ....Config import Config
from ....I18n import I18n
from ....Settings import Settings
from ....Util import Util

from ...LCAFilePickerWidget import LCAFilePickerWidget
from ...LCALabel import LCALabel
from ...LCAListCreatorWidget import LCAListCreatorWidget
from ...LCATabbedDataViewPanelWidget import LCATabbedDataViewPanelWidget

class LCACSettingsOrganizationSeriesVariantWidget (LCATabbedDataViewPanelWidget):

	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		tab_widget = QTabWidget()
		for tab in ('metadata', 'publishing'):
			tab_widget.addTab(
				getattr(self, f'__build_{tab}_tab')(),
				I18n(self).tabs[tab].title,
			)
		layout.addWidget(tab_widget)
		self._finalize_mapper()

	def __build_metadata_tab (self) -> QWidget:
		widget = QWidget()
		layout = QFormLayout(widget)
		layout.setSpacing(layout.spacing() * 2)
		if name_input := QLineEdit():
			self._mapper.addMapping(name_input, self.model.get_column_index('name'))
		layout.addRow(LCALabel(I18n(self).tabs.metadata.name), name_input)
		if id_input := QLineEdit():
			id_input.setReadOnly(True)
			self._mapper.addMapping(id_input, self.model.get_column_index('id'))
		layout.addRow(LCALabel(I18n(self).tabs.metadata.id), id_input)
		if mtgformat := QComboBox():
			mtgformat.setEditable(True)
			mtgformat.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
			for fmt in Config().mtg.formats:
				if fmt:
					mtgformat.addItem(fmt)
				else:
					mtgformat.insertSeparator(mtgformat.count())
			self._mapper.addMapping(mtgformat, self.model.get_column_index('mtgformat'), b'currentText')
			mtgformat.currentTextChanged.connect(self._mapper.submit)
		layout.addRow(LCALabel(I18n(self).tabs.metadata.mtgformat), mtgformat)
		if desc_edit := QPlainTextEdit():
			desc_edit.setPlainText(self.model.data(self.model.createIndex(
				self._mapper.currentIndex(), self.model.get_column_index('description')
			)))
			self._mapper.addMapping(desc_edit, self.model.get_column_index('description'))
		layout.addRow(LCALabel(I18n(self).tabs.metadata.desc), desc_edit)
		return widget

	def __build_publishing_tab (self) -> QWidget:
		widget = QWidget()
		layout = QHBoxLayout(widget)
		if tab_widget := QTabWidget():
			get_playlists = lambda : { playlist.id: playlist.title for playlist in Settings().integrations.youtube.playlists }
			for output_type in ('stream', 'video', 'clip'):
				output_widget = QWidget()
				output_layout = QVBoxLayout(output_widget)
				output_layout.addWidget(LCALabel(I18n(self).tabs.publishing.playlist_ids))
				if playlists_widget := LCAListCreatorWidget(LCAListCreatorWidget.Mode.COMBO, get_playlists()):
					self._mapper.addMapping(playlists_widget, self.model.get_column_index(f'publishing.{output_type}.youtube_playlist_ids'))
					Settings().signals().changed.connect(lambda : playlists_widget.set_possible_selections(get_playlists()))
					playlists_widget.changed.connect(self._mapper.submit)
				output_layout.addWidget(playlists_widget)
				tab_widget.addTab( output_widget, getattr(I18n(self).tabs.publishing.output_types, output_type) )
		layout.addWidget(tab_widget)
		return widget

