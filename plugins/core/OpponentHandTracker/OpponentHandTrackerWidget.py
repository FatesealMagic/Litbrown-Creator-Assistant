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

import re

from loguru import logger
import pydantic

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from source.Config import Config
from source.common.LCAProjectState import LCAProjectState
from source.gui.LCAMagicCardSelectorWidget import LCAMagicCardSelectorWidget
from source.gui.LCAPluginWidget import LCAPluginWidget
from source.integrations.mtgosdk.LCAMtgosdkIntegration import LCAMtgosdkIntegration
from source.models.LCAProjectStateModel import LCAProjectStateModel
from source.models.LCAScryfallCardModel import LCAScryfallCardModel
from source.threads.common.LCAScryfallSearchTaskThread import LCAScryfallSearchTaskThread

from .OpponentHandTrackerModel import OpponentHandTrackerModel

class OpponentHandTrackerWidget (LCAPluginWidget):

	__hand_tracker: QListWidget()

	def _project_state_type (self) -> type[pydantic.BaseModel]:
		return OpponentHandTrackerModel

	def _initial_project_state_data (self) -> pydantic.BaseModel:
		return OpponentHandTrackerModel()

	def _setup_layout (self) -> None:
		if widget := QWidget():
			layout = QVBoxLayout(widget)
			if hand_tracker := QListWidget():
				self.__hand_tracker = hand_tracker
				hand_tracker.itemActivated.connect(self.__evt_item_removed)
				for card in self._get_project_state_data().hand:
					hand_tracker.addItem(card.name.split(' // ')[0])
			layout.addWidget(hand_tracker)
			if card_selector := LCAMagicCardSelectorWidget(single_result = True):
				card_selector.changed.connect(self.__evt_card_selected)
			layout.addWidget(card_selector)
		self.setWidget(widget)
		self.__setup_mtgo_hooks()

	def __evt_card_selected (self, card: LCAScryfallCardModel | None) -> None:
		if not card:
			return
		self.__hand_tracker.addItem(card.name.split(' // '))
		state = self._get_project_state_data()
		self._set_project_state_data( OpponentHandTrackerModel(
			hand = state.hand + [card],
		) )

	def __evt_item_removed (self, _ = None) -> None:
		self.__remove_item(self.__hand_tracker.currentRow())

	def __remove_item (self, i: int) -> None:
		item = self.__hand_tracker.takeItem(i)
		del item
		state = self._get_project_state_data()
		self._set_project_state_data( OpponentHandTrackerModel(
			hand = state.hand[ : i ] + state.hand[ i + 1 : ],
		) )

	def __setup_mtgo_hooks (self) -> None:
		LCAMtgosdkIntegration().signals.on_message_received.connect(self.__slot_message_received)

	@Slot(object, object)
	def __slot_message_received (self,
		channel: MTGOSDK.API.Chat.Channel,
		message: MTGOSDK.API.Chat.Message,
	) -> None:
		regexes = Config().integrations.local.mtgosdk.regexes
		logger.debug(message.Text)
		for pattern, callback in [
			(rf'{regexes.player} reveals \d+ cards with {regexes.card}: (.*)\.', self.__evt_revealed_multiple_cards),
			(rf'{regexes.player} reveals {regexes.card} with {regexes.card}\.', self.__evt_revealed_one_card),
			# TODO evt_discard_multiple_cards
			(rf'{regexes.player} discards {regexes.card}\.', self.__evt_discard_one_card),
		]:
			if not (m := re.match(pattern, message.Text)):
				continue
			if m.group(1) == LCAMtgosdkIntegration().get_username():
				break
			callback(m)
			break

	def __evt_revealed_multiple_cards (self, m: re.Match) -> None:
		self.__evt_revealed( [card.group(1) for card in re.finditer(Config().integrations.local.mtgosdk.regexes.card, m.group(3))] )

	def __evt_revealed_one_card (self, m: re.Match) -> None:
		self.__evt_revealed( [m.group(2)] )

	def __evt_revealed (self, hand: list[str]) -> None:
		hand = [card_name.split(' // ')[0] for card_name in hand]
		logger.debug(f'Revealed hand: {hand}')
		logger.warning(' OR '.join([ f'!"{card_name}"' for card_name in set(hand) ]))
		self.__scryfall_search_thread = LCAScryfallSearchTaskThread(
			query = ' OR '.join([ f'!"{card_name}"' for card_name in set(hand) ]),
			unique = 'cards',
		)
		self.__scryfall_search_thread.result.connect(lambda results : self.__evt_set_cards_with_scryfall_data(hand, results))
		self.__scryfall_search_thread.start()

	def __evt_set_cards_with_scryfall_data (self, hand: list[str], results: list[LCAScryfallCardModel]) -> None:
		new_hand = []
		self.__hand_tracker.clear()
		for card_name in hand:
			self.__hand_tracker.addItem(card_name)
			for card in results:
				if card.name.split(' // ') == card_name:
					new_hand.append(card)
					break
		self._set_project_state_data( OpponentHandTrackerModel(
			hand = new_hand,
		) )

	def __evt_discard_multiple_cards (self, m: re.Match) -> None:
		raise NotImplementedError

	def __evt_discard_one_card (self, m: re.Match) -> None:
		self.__evt_discard( [m.group(2)] )

	def __evt_discard (self, cards: list[str]) -> None:
		for card_name in cards:
			items = self.__hand_tracker.findItems(card_name.split(' // ')[0], Qt.MatchFlag.MatchExactly)
			if items:
				self.__remove_item(self.__hand_tracker.row(items[-1]))

