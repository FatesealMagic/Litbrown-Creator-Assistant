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

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..Config import *
from ..I18n import *
from ..Assets import *
from ..Settings import *
from ..Util import *

from .LCATableModel import *
from .LCAWidget import *

class LCATabbedDataViewPanelWidget (LCAWidget):

	def __init__ (self,
		model: LCATableModel,
		row: int,
		*args, **kwargs
	):
		self.model = model
		self._mapper = QDataWidgetMapper()
		self._model_row = row
		self._mapper.setModel(self.model)
		self._mapper.setCurrentModelIndex(self.model.index(row, 0))
		super().__init__(*args, **kwargs)

	def _finalize_mapper (self) -> None:
		self._mapper.setCurrentIndex(self._model_row)

	def set_model_row (self, row: int) -> None:
		self._model_row = row

