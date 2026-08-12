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
from ...LCAFilePickerWidget import *

class LCACSettingsLCAWidget (LCAWidget):
	
	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		if tabs := QTabWidget():
			for tab in ('general', 'schedule', 'multicast', 'edit', 'thumbnail', 'render'):
				tabs.addTab( getattr(self, f'__build_{tab}_tab')(), I18n(self).tabs[tab].title )
		layout.addWidget(tabs)

	def __build_general_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.addWidget(QLabel(I18n(self).tabs.general.project_location))
		if projectdir_location := LCAFilePickerWidget(
			Settings().tools.general.projects_location,
			LCAFilePickerWidget.Mode.Directory,
		):
			Settings().bind(projectdir_location, 'tools.general.projects_location')
		layout.addWidget(projectdir_location)
		layout.addWidget(LCASeparator.horizontal())
		layout.addWidget(QLabel(I18n(self).tabs.general.www_location))
		if wwwdir_location := LCAFilePickerWidget(
			Settings().tools.general.www_directory,
			LCAFilePickerWidget.Mode.Directory,
		):
			Settings().bind(wwwdir_location, 'tools.general.www_directory')
		layout.addWidget(wwwdir_location)
		layout.addWidget(LCASeparator.horizontal())
		layout.addWidget(QLabel(I18n(self).tabs.general.color_slider))
		if color_slider := QSlider(Qt.Orientation.Horizontal):
			color_slider.setMaximum(359)
			color_slider.setProperty('css_class', 'rainbow')
			Settings().bind(color_slider, 'tools.general.accent_hue')
		layout.addWidget(color_slider)
		layout.addWidget(LCASeparator.horizontal())
		'''if timedisplay_cbo := LCAComboBox():
			for text, val in (('9:23 AM', 'h:mm AP'), ('09:23', 'hh:mm')):
				timedisplay_cbo.addItem(text, val)
			timedisplay_cbo.setCurrentIndex(timedisplay_cbo.findData(Settings().tools.general.time_display_format))
			Settings().signals().changed.connect(lambda : 
		layout.addRow(
			'asdf'
		)'''
		layout.addStretch()
		return widget

	def __build_schedule_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.addWidget(QLabel(I18n(self).tabs.schedule.lbl_htmlrenderfile))
		if renderfile_location := QLineEdit():
			Settings().bind(renderfile_location, 'tools.schedule.render_file')
		layout.addWidget(renderfile_location)
		layout.addSpacing(layout.spacing())
		layout.addWidget(QLabel(I18n(self).tabs.schedule.lbl_functocall))
		if functocall_line := QLineEdit(Settings().tools.schedule.render_function):
			functocall_line.setValidator(QRegularExpressionValidator(QRegularExpression('^[_$a-zA-Z][_$a-zA-Z0-9]*$')))
			Settings().bind(functocall_line, 'tools.schedule.render_function')
		layout.addWidget(functocall_line)
		layout.addSpacing(layout.spacing())
		layout.addWidget(QLabel(I18n(self).tabs.schedule.lbl_outputfile))
		if outputfile_location := LCAFilePickerWidget(
			Settings().tools.schedule.output_file,
			LCAFilePickerWidget.Mode.SaveFile,
			'PNG Image Files (*.png)',
		):
			Settings().bind(outputfile_location, 'tools.schedule.output_file')
		layout.addWidget(outputfile_location)
		layout.addStretch()
		return widget

	def __build_multicast_tab (self) -> QWidget:
		return QLabel('multicast')

	def __build_edit_tab (self) -> QWidget:
		return QLabel('edit')

	def __build_thumbnail_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.addWidget(QLabel(I18n(self).tabs.thumbnail.render_file))
		if render_file_input := QLineEdit():
			Settings().bind(render_file_input, 'tools.thumbnail.render_file')
		layout.addWidget(render_file_input)
		layout.addSpacing(layout.spacing())
		layout.addWidget(QLabel(I18n(self).tabs.thumbnail.render_func))
		if render_func_input := QLineEdit():
			Settings().bind(render_func_input, 'tools.thumbnail.render_func')
		layout.addWidget(render_func_input)
		layout.addStretch()
		return widget

	def __build_render_tab (self) -> QWidget:
		return QLabel('render')

