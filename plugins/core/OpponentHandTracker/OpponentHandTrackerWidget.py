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
from source.I18n import I18n
from source.common.LCAProjectState import LCAProjectState
from source.gui.LCALabel import LCALabel
from source.gui.LCAMagicCardSelectorWidget import LCAMagicCardSelectorWidget
from source.gui.LCAPluginWidget import LCAPluginWidget
from source.integrations.mtgosdk.LCAMtgosdkIntegration import LCAMtgosdkIntegration
from source.models.LCAProjectStateModel import LCAProjectStateModel
from source.models.LCAScryfallCardModel import LCAScryfallCardModel
from source.threads.LCATaskThreadGroup import LCATaskThreadGroup
from source.threads.common.LCAScryfallSearchTaskThread import LCAScryfallSearchTaskThread

from .OpponentHandTrackerModel import OpponentHandTrackerModel

class OpponentHandTrackerWidget (LCAPluginWidget):

	__stacked_widget: QStackedWidget
	__hand_tracker: QListWidget
	__potential_new_hand: list[str] | None = None
	__potential_hand_tracker: QListWidget
	__scryfall_search_thread_group: LCATaskThreadGroup

	def _project_state_type (self) -> type[pydantic.BaseModel]:
		return OpponentHandTrackerModel

	def _initial_project_state_data (self) -> pydantic.BaseModel:
		return OpponentHandTrackerModel()

	def _setup_layout (self) -> None:
		self.__stacked_widget = QStackedWidget()
		if tracker_widget := QWidget():
			tracker_layout = QVBoxLayout(tracker_widget)
			if hand_tracker := QListWidget():
				self.__hand_tracker = hand_tracker
				hand_tracker.itemActivated.connect(self.__evt_item_removed)
				for card in self._get_project_state_data().hand:
					hand_tracker.addItem(card.name.split(' // ')[0])
			tracker_layout.addWidget(hand_tracker)
			if card_selector := LCAMagicCardSelectorWidget(single_result = True):
				card_selector.changed.connect(self.__evt_card_selected)
			tracker_layout.addWidget(card_selector)
		self.__stacked_widget.addWidget(tracker_widget)
		if approver_widget := QWidget():
			approver_layout = QVBoxLayout(approver_widget)
			approver_layout.addWidget(LCALabel(I18n(self).approve.ask))
			if potential_hand_tracker := QListWidget():
				self.__potential_hand_tracker = potential_hand_tracker
			approver_layout.addWidget(potential_hand_tracker)
			if approver_yes_btn := QPushButton(I18n(self).approve.approve):
				approver_yes_btn.clicked.connect(lambda : self.__evt_approve_potential_hand(self.__potential_new_hand))
			approver_layout.addWidget(approver_yes_btn)
			if approver_no_btn := QPushButton(I18n(self).approve.deny):
				approver_no_btn.clicked.connect(self.__evt_deny_potential_hand)
			approver_layout.addWidget(approver_no_btn)
		self.__stacked_widget.addWidget(approver_widget)
		self.setWidget(self.__stacked_widget)
		self.__setup_mtgo_hooks()

	def __evt_card_selected (self, card: LCAScryfallCardModel | None) -> None:
		if not card:
			return
		self.__hand_tracker.addItem(card.name.split(' // ')[0])
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
		self.__potential_new_hand = hand
		self.__potential_hand_tracker.clear()
		for card_name in hand:
			self.__potential_hand_tracker.addItem(card_name)
		self.__stacked_widget.setCurrentIndex(1)

	def __evt_discard_multiple_cards (self, m: re.Match) -> None:
		raise NotImplementedError

	def __evt_discard_one_card (self, m: re.Match) -> None:
		self.__evt_discard( [m.group(2)] )

	def __evt_discard (self, cards: list[str]) -> None:
		for card_name in cards:
			items = self.__hand_tracker.findItems(card_name.split(' // ')[0], Qt.MatchFlag.MatchExactly)
			if items:
				self.__remove_item(self.__hand_tracker.row(items[-1]))

	def __evt_approve_potential_hand (self, hand: list[str]) -> None:
		self.setEnabled(False)
		self.__scryfall_search_thread_group = LCATaskThreadGroup(
			LCAScryfallSearchTaskThread(query = cardname, unique = 'cards') for cardname in set(hand)
		)
		self.__scryfall_search_thread_group.result.connect( lambda result : self.__evt_approve_hand_with_data(hand, result) )
		self.__scryfall_search_thread_group.complete.connect( lambda _ : self.setEnabled(True) )
		self.__scryfall_search_thread_group.start()

	def __evt_approve_hand_with_data (self,
		hand: list[str],
		all_results: dict[LCAScryfallSearchTaskThread, list[LCAScryfallCardModel]]
	) -> None:
		hand_data = []
		self.__hand_tracker.clear()
		for card_name in hand:
			self.__hand_tracker.addItem(card_name)
			for results in all_results.items():
				for card in results:
					if card.name.split(' // ')[0] == card_name:
						hand_data.append(card)
						break
				else:
					break
		self._set_project_state_data( OpponentHandTrackerModel(hand = hand_data) )
		self.__stacked_widget.setCurrentIndex(0)

	def __evt_deny_potential_hand (self) -> None:
		self.__stacked_widget.setCurrentIndex(0)

