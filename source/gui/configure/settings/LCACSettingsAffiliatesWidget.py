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
from ....Settings import *
from ....Util import *

from ...LCASeparator import *
from ...LCAWidget import *
from ...LCAConnectionLabelWidget import *

class LCACSettingsAffiliatesWidget (LCAWidget):
	
	__affiliate_edits: dict[str, QLineEdit]
	
	def __init__ (self, *args, **kwargs):
		self.__affiliate_edits = {}
		super().__init__()
		Settings().signals().changed.connect( self.__load_affiliate_codes )
		self.__load_affiliate_codes()
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		if affiliate_widget := QWidget():
			affiliate_layout = QFormLayout(affiliate_widget)
			affiliate_layout.setVerticalSpacing(affiliate_layout.verticalSpacing() * 1)
			affiliate_layout.setHorizontalSpacing(affiliate_layout.horizontalSpacing() * 3)
			for i, affiliate in enumerate(('manapool', 'cardhoarder', 'cardkingdom', 'starcitygames', 'toamagic')):
				if i:
					affiliate_layout.addRow(LCASeparator.horizontal())
				if affiliate_text_widget := QWidget():
					affiliate_text_layout = QVBoxLayout(affiliate_text_widget)
					affiliate_text_layout.setContentsMargins(0, 0, 0, 0)
					affiliate_text_layout.addStretch()
					if affiliate_text := QLineEdit():
						affiliate_text.setPlaceholderText(I18n(self).affiliate_placeholder)
						affiliate_text.editingFinished.connect(self.__save_affiliate_codes)
						self.__affiliate_edits[affiliate] = affiliate_text
					affiliate_text_layout.addWidget(affiliate_text)
					affiliate_text_layout.addStretch()
				affiliate_layout.addRow( LCAConnectionLabelWidget(affiliate), affiliate_text_widget )
		layout.addWidget(affiliate_widget)
		layout.addStretch()

	def __load_affiliate_codes (self) -> None:
		for affiliate, item in Settings().affiliates:
			edit = self.__affiliate_edits[affiliate]
			with QSignalBlocker(edit):
				edit.setText(item.code)

	def __save_affiliate_codes (self) -> None:
		with Settings():
			for affiliate, edit in self.__affiliate_edits.items():
				getattr(Settings().affiliates, affiliate).code = edit.text()

