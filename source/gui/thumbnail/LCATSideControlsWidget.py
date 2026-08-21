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
import pathlib
import re

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
from ..LCASeparator import *
from ..LCATableModel import *
from ..LCAToggleButtonGroupWidget import *
from ..LCAWidget import *
from ...models.thumbnail.LCATThumbnailModel import *

class LCATSideControlsWidget (LCAWidget):
	
	__IMPORTANT_BUTTONS_STYLESHEET = 'font-size: 14pt; font-weight: bold;'
	
	__model: LCATableModel[LCATThumbnailModel]
	__mapper: QDataWidgetMapper
	
	__topbar_widget: QStackedWidget
	__profile_carousel_widget: LCACarouselWidget
	__side_scroll: QScrollArea
	
	def __init__ (self, model: LCATableModel[LCATThumbnailModel], *args, **kwargs):
		self.__model = model
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		self.setProperty('css_class', 'accent_bordered')
		self.__mapper = QDataWidgetMapper(self)
		self.__mapper.setModel(self.__model)
		layout = QVBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		if topbar_widget := QStackedWidget():
			self.__topbar_widget = topbar_widget
			topbar_widget.setStyleSheet(self.__IMPORTANT_BUTTONS_STYLESHEET)
			if using_widget := QWidget():
				using_layout = QHBoxLayout(using_widget)
				using_layout.setContentsMargins(0, 0, 0, 0)
				if profile_carousel_widget := LCACarouselWidget():
					self.__profile_carousel_widget = profile_carousel_widget
					self.__rebuild_profile_carousel_widget()
					profile_carousel_widget.set_value(0)
					profile_carousel_widget.changed.connect(self.__build_display_widget)
				using_layout.addWidget(profile_carousel_widget, 1)
				if add_btn := QPushButton():
					add_btn.setIcon(Assets.QIcon('icons/plus.png'))
					add_btn.clicked.connect(self.__evt_add_profile)
				using_layout.addWidget(add_btn, 0)
				if unlock_btn := QPushButton():
					unlock_btn.setIcon(Assets.QIcon('icons/edit.png'))
					unlock_btn.clicked.connect(self.__show_edit_panel)
				using_layout.addWidget(unlock_btn, 0)
				if del_btn := QPushButton():
					del_btn.setIcon(Assets.QIcon('icons/minus.png'))
					del_btn.clicked.connect(self.__evt_del_profile)
				using_layout.addWidget(del_btn, 0)
			topbar_widget.addWidget(using_widget)
			if editing_widget := QWidget():
				editing_layout = QHBoxLayout(editing_widget)
				editing_layout.setContentsMargins(0, 0, 0, 0)
				if back_btn := QPushButton(' ' + I18n(self).top_buttons.back):
					back_btn.setIcon(Assets.QIcon('icons/undo.png'))
					back_btn.setProperty('css_class', 'big')
					back_btn.clicked.connect(self.__show_display_panel)
				editing_layout.addWidget(back_btn)
				if export_btn := QPushButton(' ' + I18n(self).top_buttons.export):
					export_btn.setIcon(Assets.QIcon('icons/load.png'))
					export_btn.clicked.connect(self.__evt_export)
				editing_layout.addWidget(export_btn)
				if import_btn := QPushButton(' ' + I18n(self).top_buttons.import_):
					import_btn.setIcon(Assets.QIcon('icons/save.png'))
					import_btn.clicked.connect(self.__evt_import)
				editing_layout.addWidget(import_btn)
				if new_btn := QPushButton(' ' + I18n(self).top_buttons.new):
					new_btn.setIcon(Assets.QIcon('icons/plus.png'))
					new_btn.setProperty('css_class', 'big')
					new_btn.clicked.connect(self.__add_new_control)
				editing_layout.addWidget(new_btn)
			topbar_widget.addWidget(editing_widget)
		layout.addWidget(topbar_widget, 0)
		if side_scroll := QScrollArea():
			self.__side_scroll = side_scroll
			side_scroll.setWidgetResizable(True)
			side_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		layout.addWidget(side_scroll, 1)
		self.__show_display_panel()

	def __build_display_widget (self, profile_index: int) -> None:
		self.__reset_thumbnail_user_info()
		if display_widget := QWidget():
			display_layout = QVBoxLayout(display_widget)
			for control in Settings().tools.thumbnail.profiles[profile_index].controls:
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
							control_layout.addWidget(LCASeparator.horizontal())
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

	def __build_edit_widget (self, profile_index: int) -> None:
		if edit_widget := QWidget():
			edit_layout = QVBoxLayout(edit_widget)
			for control_index, control in enumerate(Settings().tools.thumbnail.profiles[profile_index].controls):
				if edit_layout.count():
					edit_layout.addWidget(LCASeparator.horizontal())
				edit_layout.addWidget( LCATSideControlEditorWidget(
					profile_index,
					control_index,
					lambda : self.__build_edit_widget(self.__profile_carousel_widget.get_value()),
				) )
			edit_layout.addStretch()
		self.__side_scroll.setWidget(edit_widget)
			
	def __rebuild_profile_carousel_widget (self) -> None:
		with QSignalBlocker(self.__profile_carousel_widget):
			self.__profile_carousel_widget.clear()
			for profile_index, profile in enumerate(Settings().tools.thumbnail.profiles):
				name_edit = QLineEdit(profile.name)
				name_edit.editingFinished.connect(
					lambda edit = name_edit, i = profile_index : self.__evt_profile_name_changed(edit.text(), i)
				)
				self.__profile_carousel_widget.addItem(name_edit, profile_index, margins = False, alignment = Qt.Alignment())

	def __evt_add_profile (self) -> None:
		with Settings():
			Settings().tools.thumbnail.profiles.append(
				Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailProfileModel(name = I18n(self).default_profile_name)
			)
		self.__rebuild_profile_carousel_widget()
		self.__profile_carousel_widget.set_value(len(Settings().tools.thumbnail.profiles) - 1)

	def __evt_del_profile (self) -> None:
		if LCAPopupMessage.warning(
			I18n(self).del_profile,
			QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
		) == QMessageBox.StandardButton.Cancel:
			return
		old_index = self.__profile_carousel_widget.get_value()
		with Settings():
			Settings().tools.thumbnail.profiles.pop( old_index )
		old_index = min(old_index, len(Settings().tools.thumbnail.profiles) - 1)
		self.__rebuild_profile_carousel_widget()
		self.__profile_carousel_widget.set_value(old_index)

	def __evt_profile_name_changed (self, text: str, i: int) -> None:
		with Settings():
			Settings().tools.thumbnail.profiles[i].name = text
		self.__update_thumbnail_user_profile_name(text)

	def __show_display_panel (self) -> None:
		self.__build_display_widget(self.__profile_carousel_widget.get_value())
		self.__topbar_widget.setCurrentIndex(0)

	def __show_edit_panel (self) -> None:
		self.__build_edit_widget(self.__profile_carousel_widget.get_value())
		self.__topbar_widget.setCurrentIndex(1)

	def __add_new_control (self) -> None:
		with Settings():
			Settings().tools.thumbnail.profiles[self.__profile_carousel_widget.get_value()].controls.append(
				Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailProfileModel.ToolsThumbnailControlTextModel(
					name = I18n(self).default_control_name
				)
			)
		self.__build_edit_widget(self.__profile_carousel_widget.get_value())

	def __reset_thumbnail_user_info (self) -> None:
		self.__model.setData((0, 'user'), {
			'Profile': Settings().tools.thumbnail.profiles[self.__profile_carousel_widget.get_value()].name,
		})

	def __update_thumbnail_user_info (self, info_update: dict) -> None:
		self.__model.setData((0, 'user'), self.__model.data((0, 'user')) | {
			k.lower().replace(' ', '-'): v for k, v in info_update.items()
		})

	def __update_thumbnail_user_profile_name (self, new_name: str) -> None:
		self.__model.setData((0, 'user'), self.__model.data((0, 'user')) | {'Profile': new_name})

	def __evt_export (self) -> None:
		profile = Settings().tools.thumbnail.profiles[self.__profile_carousel_widget.get_value()]
		filename, _ = QFileDialog.getSaveFileName(
			self,
			I18n(self).export.title + profile.name,
			f'{re.sub(Config().disallowed_filename_characters_regex, '', profile.name).lower()}.json',
			I18n(self).export.filter,
		)
		if not filename:
			return
		logger.info(f'Dumping profile {profile.name} as {filename}')
		filename = pathlib.Path(filename)
		filename.parent.mkdir(parents = True, exist_ok = True)
		with open(filename, 'w', encoding = 'utf-8') as f:
			f.write(profile.model_dump_json())

	def __evt_import (self) -> None:
		filename, _ = QFileDialog.getOpenFileName(
			self,
			I18n(self).import_.title,
			'',
			I18n(self).import_.filter,
		)
		if not filename:
			return
		logger.info(f'Attempting to read profile located at: {filename}')
		try:
			with open(filename, encoding = 'utf-8') as f:
				profile = Settings().ToolsModel.ToolsThumbnailModel.ToolsThumbnailProfileModel(**json.loads(f.read()))
		except Exception as e:
			logger.exception(e)
			return
		with Settings():
			Settings().tools.thumbnail.profiles.append(profile)
		self.__rebuild_profile_carousel_widget()
		self.__profile_carousel_widget.set_value(len(Settings().tools.thumbnail.profiles) - 1)
		self.__topbar_widget.setCurrentIndex(0)

