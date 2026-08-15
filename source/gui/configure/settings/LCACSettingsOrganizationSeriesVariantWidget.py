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

from ...LCAFilePickerWidget import *
from ...LCATabbedDataViewPanelWidget import *

class LCACSettingsOrganizationSeriesVariantWidget (LCATabbedDataViewPanelWidget):

	def _setup_layout (self) -> None:
		layout = QFormLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		if name_input := QLineEdit():
			self._mapper.addMapping(name_input, self.model.get_column_index('name'))
		layout.addRow(QLabel(I18n(self).name), name_input)
		if id_input := QLineEdit():
			id_input.setReadOnly(True)
			self._mapper.addMapping(id_input, self.model.get_column_index('id'))
		layout.addRow(QLabel(I18n(self).id), id_input)
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
		layout.addRow(QLabel(I18n(self).mtgformat), mtgformat)
		if desc_edit := QPlainTextEdit():
			# TODO this is a hack, figure out why the description is overwritten to '' when the next statement is removed
			desc_edit.setPlainText(self.model.data(self.model.createIndex(
				self._mapper.currentIndex(), self.model.get_column_index('description')
			)))
			self._mapper.addMapping(desc_edit, self.model.get_column_index('description'))
		layout.addRow(QLabel(I18n(self).desc), desc_edit)
		self._finalize_mapper()

