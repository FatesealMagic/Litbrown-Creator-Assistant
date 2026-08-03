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

import functools

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Settings import *

from ..LCAComboBox import *
from ..LCAPopupMessage import *
from ..LCAWidget import *

class LCATSideControlEditorWidget (LCAWidget):

	def __init__ (self, control_index: int, model_modified_callback: typing.Callable[[], Any]):
		self.__control_index = control_index
		self.__model_modified_callback = model_modified_callback
		super().__init__()

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		if btns_widget := QWidget():
			btns_layout = QHBoxLayout(btns_widget)
			btns_layout.setContentsMargins(0, 0, 0, 0)
			if up_btn := QPushButton(' ' + I18n(self).edit_btns.up):
				up_btn.setIcon(Assets.QIcon('icons/up.png'))
				up_btn.setEnabled(self.__control_index != 0)
				up_btn.clicked.connect(self.__evt_move_up)
			btns_layout.addWidget(up_btn)
			if delete_btn := QPushButton(' ' + I18n(self).edit_btns.delete):
				delete_btn.setIcon(Assets.QIcon('icons/minus.png'))
				delete_btn.clicked.connect(self.__evt_delete)
			btns_layout.addWidget(delete_btn)
			if down_btn := QPushButton(' ' + I18n(self).edit_btns.down):
				down_btn.setIcon(Assets.QIcon('icons/down.png'))
				down_btn.setEnabled(self.__control_index != len(Settings().tools.thumbnail.controls) - 1)
				down_btn.clicked.connect(self.__evt_move_down)
			btns_layout.addWidget(down_btn)
		layout.addWidget(btns_widget)
		if top_widget := QWidget():
			top_layout = QHBoxLayout(top_widget)
			top_layout.setContentsMargins(0, 0, 0, 0)
			if name_txt := QLineEdit():
				self.__name_txt = name_txt
				name_txt.setText(Settings().tools.thumbnail.controls[self.__control_index].name)
				name_txt.editingFinished.connect(self.__evt_name_changed)
			top_layout.addWidget(name_txt)
			if type_cbo := LCAComboBox():
				for supported_type in ('mtgcard', 'text', 'number', 'combo', 'checkbox', 'separator'):
					type_cbo.addItem(getattr(I18n(self).supported_types, supported_type), supported_type)
				type_cbo.setData(Settings().tools.thumbnail.controls[self.__control_index].input_type)
				type_cbo.currentDataChanged.connect(self.__evt_type_changed)
			top_layout.addWidget(type_cbo)
		layout.addWidget(top_widget)
		layout.addSpacing(layout.spacing())
		self.__options_widget = None
		self.__build_new_options_widget()

	def __evt_type_changed (self, new_type: str) -> None:
		with Settings():
			Settings().tools.thumbnail.controls[self.__control_index] = {
				'mtgcard':   Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailControlMagicCardSelectorModel,
				'text':      Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailControlTextModel,
				'number':    Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailControlNumberModel,
				'combo':     Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailControlComboModel,
				'checkbox':  Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailControlCheckboxModel,
				'separator': Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailControlSeparatorModel,
			}[new_type](name = self.__name_txt.text())
		self.__build_new_options_widget()

	def __build_new_options_widget (self) -> None:
		if self.__options_widget:
			self.layout().removeWidget(self.__options_widget)
			self.__options_widget.setParent(None)
			self.__options_widget.deleteLater()
		self.__options_widget = QWidget()
		match Settings().tools.thumbnail.controls[self.__control_index].input_type:
			case 'mtgcard':
				pass
			case 'text':
				text_options_layout = QFormLayout(self.__options_widget)
				text_options_layout.setContentsMargins(0, 0, 0, 0)
				if text_default_input := QLineEdit():
					text_default_input.setText(Settings().tools.thumbnail.controls[self.__control_index].default)
					text_default_input.editingFinished.connect(lambda : self.__evt_text_default_changed(text_default_input.text()))
				text_options_layout.addRow(I18n(self).text.default, text_default_input)
			case 'number':
				number_options_layout = QFormLayout(self.__options_widget)
				number_options_layout.setContentsMargins(0, 0, 0, 0)
				for property in ('minimum', 'maximum', 'default'):
					if property_spin := QSpinBox():
						property_spin.setRange(-2147483648, 2147483647)
						property_spin.setValue(getattr(Settings().tools.thumbnail.controls[self.__control_index], property))
						property_spin.valueChanged.connect(
							lambda value, prop = property : self.__evt_number_option_changed(prop, value)
						)
					number_options_layout.addRow(getattr(I18n(self).number, property), property_spin)
			case 'combo':
				combo_options_layout = QVBoxLayout(self.__options_widget)
				combo_options_layout.setContentsMargins(0, 0, 0, 0)
				for i, option in enumerate(Settings().tools.thumbnail.controls[self.__control_index].options):
					if option_widget := QWidget():
						option_layout = QHBoxLayout(option_widget)
						option_layout.setContentsMargins(0, 0, 0, 0)
						if option_input := QLineEdit():
							option_input.setText(option)
							option_input.editingFinished.connect(
								lambda input = option_input, i = i :
									self.__evt_combo_option_changed(i, input.text())
							)
						option_layout.addWidget(option_input)
						if option_delete_btn := QPushButton(''):
							option_delete_btn.setIcon(Assets.QIcon('icons/minus.png'))
							logger.warning(i)
							option_delete_btn.clicked.connect( functools.partial( self.__evt_combo_option_removed, i = i ) )
						option_layout.addWidget(option_delete_btn)
					combo_options_layout.addWidget(option_widget)
				if option_add_btn := QPushButton(' ' + I18n(self).combo.add):
					option_add_btn.setIcon(Assets.QIcon('icons/plus.png'))
					option_add_btn.clicked.connect(self.__evt_combo_option_added)
				combo_options_layout.addWidget(option_add_btn)
			case 'checkbox':
				pass
			case 'separator':
				pass
		self.layout().addWidget(self.__options_widget)

	def __evt_name_changed (self) -> None:
		with Settings():
			Settings().tools.thumbnail.controls[self.__control_index].name = self.__name_txt.text()

	def __evt_text_default_changed (self, value: str) -> None:
		with Settings():
			Settings().tools.thumbnail.controls[self.__control_index].default = value

	def __evt_number_option_changed (self, property: str, value: int) -> None:
		logger.warning(property)
		logger.warning(value)
		with Settings():
			setattr(Settings().tools.thumbnail.controls[self.__control_index], property, value)

	def __evt_combo_option_added (self) -> None:
		with Settings():
			Settings().tools.thumbnail.controls[self.__control_index].options.append(I18n(self).combo.new_default)
		self.__model_modified_callback()

	def __evt_combo_option_removed (self, i: int) -> None:
		logger.warning(i)
		with Settings():
			Settings().tools.thumbnail.controls[self.__control_index].options.pop(i)
		self.__model_modified_callback()

	def __evt_combo_option_changed (self, i: int, val: str) -> None:
		with Settings():
			Settings().tools.thumbnail.controls[self.__control_index].options[i] = val

	def __evt_move_up (self) -> None:
		self.__swap_with_index(self.__control_index - 1)

	def __evt_move_down (self) -> None:
		self.__swap_with_index(self.__control_index + 1)

	def __swap_with_index (self, new_index: int) -> None:
		with Settings():
			temp = Settings().tools.thumbnail.controls[new_index]
			Settings().tools.thumbnail.controls[new_index] = Settings().tools.thumbnail.controls[self.__control_index]
			Settings().tools.thumbnail.controls[self.__control_index] = temp
		self.__model_modified_callback()

	def __evt_delete (self) -> None:
		if LCAPopupMessage.warning(
			I18n(self).warning_delete,
			QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
		) == QMessageBox.StandardButton.Cancel:
			return
		with Settings():
			Settings().tools.thumbnail.controls = \
				Settings().tools.thumbnail.controls[ : self.__control_index ] + \
				Settings().tools.thumbnail.controls[ self.__control_index + 1 : ]
		self.__model_modified_callback()

