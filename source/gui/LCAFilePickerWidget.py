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

from ..Config import *
from ..I18n import *
from ..Assets import *
from ..Settings import *
from ..Util import *

from .LCALabel import *
from .LCAWidget import *

class LCAFilePickerWidget (LCAWidget):

	changed = Signal(str)
	
	class Mode:
		OpenFile = 'openfile'
		SaveFile = 'savefile'
		Directory = 'directory'

	__mode: Mode

	def __init__ (self,
		initial_value: str,
		mode: Mode,
		filter: str = '',
		*args, **kwargs
	):
		self.__value = initial_value
		self.__mode = mode
		self.__filter = filter
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		if group_widget := QGroupBox():
			group_layout = QHBoxLayout(group_widget)
			group_layout.setContentsMargins(0, 0, 0, 0)
			group_layout.setSpacing(0)
			#group_layout.addSpacing(group_layout.spacing())
			if file_display := LCALabel(self.__value):
				self.__file_display = file_display
				file_display.setSizePolicy(QSizePolicy.Policy.Ignored, file_display.sizePolicy().verticalPolicy())
			group_layout.addWidget(file_display, 1)
			if picker_btn := QPushButton(' ' + I18n(self).picker_btn):
				picker_btn.setIcon(Assets.QIcon('icons/filepicker.png'))
				picker_btn.clicked.connect(self.__open_picker_dialog)
			group_layout.addWidget(picker_btn, 0)
			#group_layout.addSpacing(group_layout.spacing() / 2)
		layout.addWidget(group_widget)

	def __open_picker_dialog (self) -> None:
		filename = {
			self.Mode.OpenFile:  QFileDialog.getOpenFileName,
			self.Mode.SaveFile:  QFileDialog.getSaveFileName,
			self.Mode.Directory: QFileDialog.getExistingDirectory,
		}[self.__mode](
			parent = QApplication.activeWindow(),
			dir = self.__value,
			options = QFileDialog.Option.DontConfirmOverwrite,
			**({'filter': self.__filter} if self.__mode is not self.Mode.Directory else {})
		)
		if self.__mode is not self.Mode.Directory:
			filename = filename[0]
		logger.debug(filename)
		if filename:
			self.set_value(filename)

	def get_value (self) -> str:
		return self.__value

	def set_value (self, val: str) -> None:
		if self.__value == val:
			return
		self.__value = val
		self.__file_display.setText(val)
		self.changed.emit(val)

	val = Property(
		str,
		fget = get_value,
		fset = set_value,
		notify = changed,
		user = True,
	)

