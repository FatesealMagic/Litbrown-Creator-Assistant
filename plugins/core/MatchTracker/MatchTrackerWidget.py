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

from PySide6.QtWidgets import *

from source.common.LCAProjectState import *
from source.models.LCAProjectStateModel import *
from source.gui.LCACarouselWidget import *
from source.gui.LCAPluginWidget import *

from .SingleMatchTrackerWidget import *

class MatchTrackerWidget (LCAPluginWidget):

	__carousel_widget: LCACarouselWidget

	def _project_state_type (self) -> None:
		return None

	def _initial_project_state_data (self) -> None:
		return None

	def _setup_layout (self) -> None:
		if carousel_widget := LCACarouselWidget(margin = True):
			self.__carousel_widget = carousel_widget
		LCAProjectState().updated_model.connect(self.__evt_state_updated)
		self.__evt_state_updated(LCAProjectState().model)

	def __evt_state_updated (self, state: LCAProjectStateModel) -> None:
		for i in range(self.__carousel_widget.count(), len(state.mtgo.matches)):
			self.setWidget(self.__carousel_widget)
			self.__carousel_widget.addItem( SingleMatchTrackerWidget(i), i, alignment = Qt.Alignment() )
			self.__carousel_widget.set_value(i)

