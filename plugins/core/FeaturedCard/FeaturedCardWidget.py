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
import pydantic

from PySide6.QtWidgets import *

from source.common.LCAProjectState import LCAProjectState
from source.models.LCAProjectStateModel import LCAProjectStateModel
from source.models.LCAScryfallCardModel import LCAScryfallCardModel
from source.gui.LCAMagicCardSelectorWidget import LCAMagicCardSelectorWidget
from source.gui.LCAPluginWidget import LCAPluginWidget

from .FeaturedCardModel import FeaturedCardModel

class FeaturedCardWidget (LCAPluginWidget):

	def _project_state_type (self) -> type[pydantic.BaseModel]:
		return FeaturedCardModel

	def _initial_project_state_data (self) -> pydantic.BaseModel:
		return FeaturedCardModel()

	def _setup_layout (self) -> None:
		if widget := QWidget():
			layout = QHBoxLayout(widget)
			if card_selector := LCAMagicCardSelectorWidget(single_result = True):
				card_selector.changed.connect(self.__evt_card_selected)
			layout.addWidget(card_selector)
		self.setWidget(widget)
		self._set_project_state_data(None)

	def __evt_card_selected (self, card: LCAScryfallCardModel | None) -> None:
		self._set_project_state_data( FeaturedCardModel( featured = card ) )

