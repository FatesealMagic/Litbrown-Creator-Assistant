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

from ...Config import *
from ...I18n import *
from ...Assets import *
from ...Settings import *
from ...Util import *

from .LCATSideControlEditorWidget import *
from ..LCAMagicCardSelectorWidget import *
from ..LCATableModel import *
from ..LCAToggleButtonGroupWidget import *
from ..LCAWidget import *
from ...models.thumbnail.LCATThumbnailModel import *

class LCATSideControlsWidget (LCAWidget):
	
	__IMPORTANT_BUTTONS_STYLESHEET = 'font-size: 14pt; font-weight: bold;'
	
	__model: LCATableModel[LCATThumbnailModel]
	__mapper: QDataWidgetMapper
	
	def __init__ (self, model: LCATableModel[LCATThumbnailModel], *args, **kwargs):
		self.__model = model
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		self.setProperty('css_class', 'accent_bordered')
		self.__mapper = QDataWidgetMapper(self)
		self.__mapper.setModel(self.__model)
		layout = QVBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		if topbar_widget := QWidget():
			topbar_widget.setStyleSheet(self.__IMPORTANT_BUTTONS_STYLESHEET)
			topbar_layout = QHBoxLayout(topbar_widget)
			topbar_layout.setContentsMargins(0, 0, 0, 0)
			if unlock_btn := QPushButton(I18n(self).top_buttons.unlock):
				self.__unlock_btn = unlock_btn
				unlock_btn.clicked.connect(self.__show_edit_panel)
			topbar_layout.addWidget(unlock_btn)
			if back_btn := QPushButton(' ' + I18n(self).top_buttons.back):
				self.__back_btn = back_btn
				back_btn.setIcon(Assets.QIcon('icons/undo.png'))
				back_btn.setProperty('css_class', 'big')
				back_btn.clicked.connect(self.__show_display_panel)
			topbar_layout.addWidget(back_btn)
			if save_btn := QPushButton(' ' + I18n(self).top_buttons.save):
				self.__save_btn = save_btn
				save_btn.setIcon(Assets.QIcon('icons/load.png'))
			topbar_layout.addWidget(save_btn)
			if load_btn := QPushButton(' ' + I18n(self).top_buttons.load):
				self.__load_btn = load_btn
				load_btn.setIcon(Assets.QIcon('icons/save.png'))
			topbar_layout.addWidget(load_btn)
			if new_btn := QPushButton(' ' + I18n(self).top_buttons.new):
				self.__new_btn = new_btn
				new_btn.setIcon(Assets.QIcon('icons/plus.png'))
				new_btn.setProperty('css_class', 'big')
				new_btn.clicked.connect(self.__add_new_control)
			topbar_layout.addWidget(new_btn)
		layout.addWidget(topbar_widget)
		if side_scroll := QScrollArea():
			self.__side_scroll = side_scroll
			side_scroll.setWidgetResizable(True)
			side_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		layout.addWidget(side_scroll)
		self.__show_display_panel() # TODO show edit if empty

	def __build_display_widget (self) -> None:
		if display_widget := QWidget():
			display_layout = QVBoxLayout(display_widget)
			for control in Settings().tools.thumbnail.controls:
				if control_widget := QWidget():
					control_layout = QVBoxLayout(control_widget)
					match control.input_type:
						case 'checkbox':
							if checkbox_widget := QCheckBox(control.name):
								checkbox_widget.setStyleSheet('font-weight: bold;')
								checkbox_widget.checkStateChanged.connect(
									lambda state, name = control.name :
										self.__update_thumbnail_user_info({name: state == Qt.CheckState.Checked})
								)
							self.__update_thumbnail_user_info({control.name: False})
							control_layout.addWidget(checkbox_widget)
						case 'separator':
							control_layout.addSpacing(control_layout.spacing())
							control_layout.addWidget(self._build_hsep())
							if control_name := QLabel(control.name):
								control_name.setWordWrap(True)
								control_name.setStyleSheet('font-size: 13pt; font-weight: bold;')
							control_layout.addWidget(control_name, alignment = Qt.AlignCenter)
						case _:
							if control_name := QLabel(control.name):
								control_name.setWordWrap(True)
								control_name.setStyleSheet('font-weight: bold;')
							control_layout.addWidget(control_name)
					match control.input_type:
						case 'mtgcard':
							control_mtgcard_input = LCAMagicCardSelectorWidget()
							control_mtgcard_input.changed.connect(
								lambda value, name = control.name :
									self.__update_thumbnail_user_info({name: value})
							)
							self.__update_thumbnail_user_info({control.name: None})
							control_layout.addWidget(control_mtgcard_input)
						case 'text':
							control_text_input = QLineEdit()
							control_text_input.setText(control.default)
							control_text_input.textChanged.connect(
								lambda value, name = control.name :
									self.__update_thumbnail_user_info({name: value})
							)
							self.__update_thumbnail_user_info({control.name: control.default})
							control_layout.addWidget(control_text_input)
						case 'number':
							control_number_spin_input = QSpinBox()
							control_number_slider_input = QSlider()
							control_number_spin_input.setRange(control.minimum, control.maximum)
							control_number_spin_input.setValue(control.default)
							control_number_spin_input.valueChanged.connect(
								lambda value, name = control.name :
									self.__update_thumbnail_user_info({name: value})
							)
							control_number_spin_input.valueChanged.connect(
								lambda value, slider = control_number_slider_input :
									slider.setValue(value) if slider.value() != value else None
							)
							control_number_slider_input.setOrientation(Qt.Orientation.Horizontal)
							control_number_slider_input.setMinimum(control.minimum)
							control_number_slider_input.setMaximum(control.maximum)
							control_number_slider_input.setValue(control.default)
							control_number_slider_input.valueChanged.connect(
								lambda value, name = control.name :
									self.__update_thumbnail_user_info({name: value})
							)
							control_number_slider_input.valueChanged.connect(
								lambda value, spin = control_number_spin_input :
									spin.setValue(value) if spin.value() != value else None
							)
							self.__update_thumbnail_user_info({control.name: control.default})
							control_layout.addWidget(control_number_spin_input)
							control_layout.addWidget(control_number_slider_input)
						case 'combo':
							control_combo_input = LCAComboBox()
							for option in control.options:
								control_combo_input.addItem(option, option)
							control_combo_input.currentDataChanged.connect(
								lambda value, name = control.name :
									self.__update_thumbnail_user_info({name: value})
							)
							self.__update_thumbnail_user_info({control.name: control.options[0] if control.options else ''})
							control_layout.addWidget(control_combo_input)
						case 'checkbox':
							pass
						case 'separator':
							pass
				display_layout.addWidget(control_widget)
			display_layout.addStretch()
		self.__side_scroll.setWidget(display_widget)

	def __show_display_panel (self) -> None:
		self.__build_display_widget()
		self.__unlock_btn.setVisible(True)
		self.__back_btn.setVisible(False)
		self.__save_btn.setVisible(False)
		self.__load_btn.setVisible(False)
		self.__new_btn.setVisible(False)

	def __show_edit_panel (self) -> None:
		self.__build_edit_widget()
		self.__unlock_btn.setVisible(False)
		self.__back_btn.setVisible(True)
		self.__save_btn.setVisible(True)
		self.__load_btn.setVisible(True)
		self.__new_btn.setVisible(True)

	def __build_edit_widget (self) -> None:
		if edit_widget := QWidget():
			edit_layout = QVBoxLayout(edit_widget)
			for i, control in enumerate(Settings().tools.thumbnail.controls):
				if edit_layout.count():
					edit_layout.addWidget(self._build_hsep())
				edit_layout.addWidget( LCATSideControlEditorWidget(i, self.__build_edit_widget) )
			edit_layout.addStretch()
		self.__side_scroll.setWidget(edit_widget)
			
	def __add_new_control (self) -> None:
		with Settings():
			Settings().tools.thumbnail.controls.append(
				Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailControlTextModel(name = I18n(self).default_name)
			)
		self.__build_edit_widget()

	def __update_thumbnail_user_info (self, info_update: dict) -> None:
		self.__model.setData((0, 'user'), self.__model.data((0, 'user')) | info_update)

