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
from source.gui.LCASeparator import *
from source.gui.LCAWidget import *

from .ResultButton import *

class SingleMatchTrackerWidget (LCAWidget):

	__match_number: int
	__match_result_btn: ResultButton
	__game_result_btns: list[ResultButton]

	def __init__ (self,
		match_number: int,
	):
		self.__match_number = match_number
		super().__init__()
	
	def _setup_layout (self) -> None:
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(
			QLabel(f'<html><h3>{I18n(self).match} #{self.__match_number + 1}</h3></html>'),
			alignment = Qt.AlignmentFlag.AlignHCenter,
		)
		if match_result_btn := ResultButton():
			self.__match_result_btn = match_result_btn
			match_result_btn.changed.connect(self.__evt_match_result_changed)
		layout.addWidget(match_result_btn)
		layout.addWidget(
			QLabel(', '.join(self.__get_match_ref().opponents)),
			alignment = Qt.AlignmentFlag.AlignHCenter,
		)
		if deckname_input := QLineEdit():
			deckname_input.setPlaceholderText(I18n(self).archetype)
			deckname_input.editingFinished.connect( lambda : self.__evt_archetype_edited(deckname_input.text()) )
		layout.addWidget(deckname_input)
		self.__game_result_btns = []
		for i in range(self.__get_match_ref().best_of):
			layout.addWidget(LCASeparator.horizontal())
			if game_result_btn := ResultButton():
				self.__game_result_btns.append(game_result_btn)
				game_result_btn.setEnabled(False)
				game_result_btn.changed.connect(lambda val, l_i = i : self.__evt_game_result_changed(i, val))
			layout.addWidget(game_result_btn)
			if notes_input := QLineEdit():
				notes_input.setPlaceholderText(I18n(self).notes)
				notes_input.editingFinished.connect(
					lambda l_input = notes_input, l_i = i : self.__evt_game_notes_edited(l_i, l_input.text())
				)
			layout.addWidget(notes_input)
		layout.addStretch()
		self.__evt_model_updated(LCAProjectState().model)
		LCAProjectState().updated_model.connect(self.__evt_model_updated)

	def __evt_model_updated (self, _) -> None:
		self.__match_result_btn.set_value(self.__get_match_ref().victory)
		for i, game in enumerate(self.__get_match_ref().games):
			self.__game_result_btns[i].setEnabled(True)
			self.__game_result_btns[i].set_value(game.victory)

	def __evt_match_result_changed (self, val: bool | None) -> None:
		if self.__get_match_ref().victory == val:
			return
		with LCAProjectState():
			self.__get_match_ref().victory = val

	def __evt_game_result_changed (self, game_index: int, val: bool | None) -> None:
		if len(self.__get_match_ref().games) <= game_index:
			return
		if self.__get_match_ref().games[game_index].victory == val:
			return
		with LCAProjectState():
			self.__get_match_ref().games[game_index].victory = val

	def __evt_archetype_edited (self, archetype: str) -> None:
		with LCAProjectState():
			self.__get_match_ref().archetype = archetype

	def __evt_game_notes_edited (self, game_index: int, notes: str) -> None:
		with LCAProjectState():
			self.__get_match_ref().games[game_index].notes = notes

	def __get_match_ref (self) -> LCAProjectStateModel.Mtgo.Match:
		return LCAProjectState().model.mtgo.matches[self.__match_number]

