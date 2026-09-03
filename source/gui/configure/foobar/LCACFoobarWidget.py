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
from ....Util import *

from ...LCAFilePickerWidget import *
from ...LCALabel import *
from ...LCASeparator import *
from ...LCAWidget import *

class LCACFoobarWidget (LCAWidget):

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		layout.addWidget(LCALabel(I18n(self).info))
		layout.addWidget(LCALabel(I18n(self).install_foobar))
		layout.addWidget(LCALabel(I18n(self).install_beefweb))
		layout.addWidget(LCASeparator.horizontal())
		layout.addWidget(LCALabel(I18n(self).install_location))
		if install_location := LCAFilePickerWidget(
			Settings().integrations.foobar.install_location,
			LCAFilePickerWidget.Mode.OpenFile,
		):
			Settings().bind(install_location, 'integrations.foobar.install_location')
		layout.addWidget(install_location)
		layout.addWidget(LCALabel(I18n(self).beefweb_port))
		if beefweb_port := QSpinBox():
			beefweb_port.setRange(0, 65535)
			Settings().bind(beefweb_port, 'integrations.foobar.beefweb_port')
		layout.addWidget(beefweb_port)
		layout.addWidget(LCALabel(I18n(self).additional_arguments))
		if additional_arguments := QLineEdit():
			Settings().bind(additional_arguments, 'integrations.foobar.additional_arguments')
		layout.addWidget(additional_arguments)
		layout.addStretch(1)

