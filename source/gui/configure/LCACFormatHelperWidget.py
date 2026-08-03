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

import re

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...I18n import *
from ...Assets import *

from ..LCADialog import *
from ..LCAPopupMessage import *
from ..LCAWidget import *
from ...common.LCATextTemplate import *

class LCACFormatHelperWidget (LCAWidget):
	
	class LCACFormatHelperDialog (LCADialog):
		
		def __init__ (self,
			variable_group: LCATextTemplate.VariableGroup,
			connected_input: QLineEdit | QPlainTextEdit,
		*args, **kwargs):
			self.__variable_group = variable_group
			self.__connected_input = connected_input
			super().__init__(modality = Qt.WindowModality.NonModal, *args, **kwargs)
			self.resize(300, 600)
		
		def _setup_layout (self) -> None:
			layout = QVBoxLayout(self)
			for i, lbltext in enumerate(I18n(self).directions):
				lbl = QLabel(lbltext)
				lbl.setWordWrap(True)
				layout.addWidget(lbl)
			if var_cbo := QComboBox():
				for key in LCATextTemplate.vars_for_group(self.__variable_group):
					var_cbo.addItem(f'${{{key}}}')
				var_cbo.currentTextChanged.connect(self.__evt_var_selected)
			layout.addWidget(var_cbo)
			if var_lbl := QLabel(
				LCATextTemplate.vars_and_descriptions_for_group(self.__variable_group)
					[ LCATextTemplate.vars_for_group(self.__variable_group)[0] ]
			):
				self.__var_lbl = var_lbl
				var_lbl.setWordWrap(True)
			layout.addWidget(var_lbl)
			layout.addStretch()
			if close_btn := QPushButton(' ' + I18n(self).close_btn):
				close_btn.setIcon(Assets.QIcon('icons/close.png'))
				close_btn.clicked.connect(self.close)
			layout.addWidget(close_btn)
		
		def __evt_var_selected (self, text: str) -> None:
			self.__var_lbl.setText(LCATextTemplate.vars_and_descriptions_for_group(self.__variable_group)[ text[2:-1] ])

	def __init__ (self,
		variable_group: LCATextTemplate.VariableGroup,
		connected_input: QLineEdit | QPlainTextEdit,
		orientation: Qt.Orientation,
	*args, **kwargs):
		self.__variable_group = variable_group
		self.__connected_input = connected_input
		self.__orientation = orientation
		super().__init__(*args, **kwargs)
		logger.debug('making a formathelperwidget')

	def _setup_layout (self) -> None:
		if self.__orientation == Qt.Orientation.Horizontal:
			layout = QHBoxLayout(self)
		elif self.__orientation == Qt.Orientation.Vertical:
			layout = QVBoxLayout(self)
		else:
			raise ValueError('Orientation must be either horizontal or vertical')
		layout.setContentsMargins(0, 0, 0, 0)
		if help_btn := QPushButton(' ' + I18n(self).help_btn):
			help_btn.setIcon(Assets.QIcon('icons/help.png'))
			help_btn.clicked.connect(self.__evt_help_clicked)
		layout.addWidget(help_btn)
		if validate_btn := QPushButton(' ' + I18n(self).validate_btn):
			validate_btn.setIcon(Assets.QIcon('icons/validate.png'))
			validate_btn.clicked.connect(self.__evt_validate_clicked)
		layout.addWidget(validate_btn)

	def __evt_help_clicked (self) -> None:
		logger.debug('help')
		self.LCACFormatHelperDialog(self.__variable_group, self.__connected_input).show()

	def __evt_validate_clicked (self) -> None:
		try:
			LCATextTemplate(self.__get_connected_text(), self.__variable_group).dry_run()
			LCAPopupMessage.info(I18n(self).success)
		except KeyError as e:
			LCAPopupMessage.warning(f'{I18n(self).keyerror} ${{{e.args[0]}}}')
		except ValueError as e:
			linetxt, coltxt = re.search(r'(\d+)\D+(\d+)', e.args[0]).group(1, 2)
			LCAPopupMessage.warning(f'{I18n(self).valueerror} {I18n(self).valueerror_line} {linetxt}, {I18n(self).valueerror_col} {coltxt}')

	def __get_connected_text (self) -> str:
		return self.__connected_input.toPlainText() \
			if isinstance(self.__connected_input, QPlainTextEdit) \
			else self.__connected_input.text()

