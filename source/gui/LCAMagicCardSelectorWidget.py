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

from .LCACardDisplayWidget import *
from .LCACarouselWidget import *
from .LCALabel import *
from .LCAWidget import *
from ..models.LCAScryfallCardModel import *
from ..threads.common.LCAScryfallSearchTaskThread import *

class LCAMagicCardSelectorWidget (LCAWidget):
	
	changed = Signal(object) # LCAScryfallCardModel | None

	__single_result: bool
	__search_results: list[LCAScryfallCardModel] = []

	def __init__ (self,
		/, *,
		single_result: bool = False,
	):
		self.__single_result = single_result
		super().__init__()

	def _setup_layout (self) -> None:
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		if stacked_widget := QStackedWidget():
			self.__stacked_widget = stacked_widget
			if cardsearch_widget := QWidget():
				cardsearch_layout = QVBoxLayout(cardsearch_widget)
				cardsearch_layout.setContentsMargins(0, 0, 0, 0)
				if cardsearchbar_widget := QWidget():
					cardsearchbar_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
					cardsearchbar_layout = QHBoxLayout(cardsearchbar_widget)
					cardsearchbar_layout.setContentsMargins(0, 0, 0, 0)
					if scryfallsearch_input := QLineEdit():
						self.__scryfallsearch_input = scryfallsearch_input
						scryfallsearch_input.editingFinished.connect(
							lambda input = scryfallsearch_input : self.__do_scryfall_search(scryfallsearch_input.text())
						)
						scryfallsearch_input.setPlaceholderText(I18n(self).search_placeholder)
					cardsearchbar_layout.addWidget(scryfallsearch_input)
					if scryfallsearch_btn := QPushButton(''):
						self.__scryfallsearch_btn = scryfallsearch_btn
						scryfallsearch_btn.setIcon(Assets.QIcon('icons/advance.png'))
						scryfallsearch_btn.clicked.connect(
							lambda input = scryfallsearch_input : self.__do_scryfall_search(scryfallsearch_input.text())
						)
					cardsearchbar_layout.addWidget(scryfallsearch_btn)
					if clearvalue_btn := QPushButton(''):
						self.__clearvalue_btn = clearvalue_btn
						clearvalue_btn.setIcon(Assets.QIcon('icons/close.png'))
						clearvalue_btn.clicked.connect(self.__evt_clearvalue_clicked)
						clearvalue_btn.hide()
					cardsearchbar_layout.addWidget(clearvalue_btn)
				cardsearch_layout.addWidget(cardsearchbar_widget)
				if cardsearch_results := QListWidget():
					self.__cardsearch_results = cardsearch_results
					cardsearch_results.itemActivated.connect(
						lambda item : self.__evt_card_selected(item.text())
					)
				cardsearch_layout.addWidget(cardsearch_results)
			stacked_widget.addWidget(cardsearch_widget)
			if printsearch_widget := QWidget():
				printsearch_layout = QVBoxLayout(printsearch_widget)
				printsearch_layout.setContentsMargins(0, 0, 0, 0)
				if printname_widget := QWidget():
					printname_layout = QHBoxLayout(printname_widget)
					printname_layout.setContentsMargins(0, 0, 0, 0)
					if backtocardsearch_btn := QPushButton():
						backtocardsearch_btn.setIcon(Assets.QIcon('icons/undo.png'))
						backtocardsearch_btn.clicked.connect(self.__evt_backtocardsearch_clicked)
					printname_layout.addWidget(backtocardsearch_btn)
					if cardname_lbl := LCALabel():
						self.__cardname_lbl = cardname_lbl
						cardname_lbl.setStyleSheet('font-weight: bold; font-style: italic;')
						cardname_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
					printname_layout.addWidget(cardname_lbl, 1)
					if newface_btn := QPushButton():
						self.__newface_btn = newface_btn
						newface_btn.setIcon(Assets.QIcon('icons/flip.png'))
						newface_btn.clicked.connect(self.__evt_newface)
					printname_layout.addWidget(newface_btn)
				printsearch_layout.addWidget(printname_widget)
				if printcarousel_widget := LCACarouselWidget():
					self.__printcarousel_widget = printcarousel_widget
					printcarousel_widget.changed.connect( self.__evt_carousel_updated )
				printsearch_layout.addWidget(printcarousel_widget)
				if setname_lbl := LCALabel():
					self.__setname_lbl = setname_lbl
					setname_lbl.setStyleSheet('font-style: italic;')
					setname_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
				printsearch_layout.addWidget(setname_lbl)
			stacked_widget.addWidget(printsearch_widget)
		layout.addWidget(stacked_widget)

	def __do_scryfall_search (self, query: text) -> None:
		if not query:
			return
		self.setEnabled(False)
		self.__cardsearch_results.clear()
		self.__search_results = []
		self.__search_thread = LCAScryfallSearchTaskThread(
			query = query,
			unique = 'cards' if self.__single_result else 'prints',
		)
		self.__search_thread.error.connect( self.__evt_search_thread_error )
		self.__search_thread.update.connect( self.__evt_search_thread_update )
		self.__search_thread.complete.connect( self.__evt_search_thread_complete )
		self.__search_thread.start()

	def __evt_search_thread_error (self, e: Exception):
		self.__cardsearch_results.addItem(str(e))

	def __evt_search_thread_update (self, cards: list[LCAScryfallCardModel]):
		self.__search_results += cards
		for card in cards:
			if not self.__cardsearch_results.findItems(card.name, Qt.MatchFlag.MatchExactly):
				self.__cardsearch_results.addItem(card.name)

	def __evt_search_thread_complete (self, success: bool) -> None:
		self.__cardsearch_results.setEnabled(success)
		self.setEnabled(True)
		if success and self.__cardsearch_results.count() == 1:
			self.__cardsearch_results.setCurrentRow(0)
			self.__evt_card_selected(self.__cardsearch_results.currentItem().text())

	def __evt_card_selected (self, cardname: str) -> None:
		if self.__single_result:
			for card in self.__search_results:
				if card.name == self.__cardsearch_results.currentItem().text():
					self.__scryfallsearch_btn.hide()
					self.__clearvalue_btn.show()
					self.changed.emit(card)
					return
		else:
			self.__printcarousel_widget.clear()
			for card_printing in self.__search_results:
				if card_printing.name == self.__cardsearch_results.currentItem().text():
					stacked = QStackedWidget()
					stacked.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
					stacked.setProperty('css_class', 'card_display')
					stacked.addWidget( LCACardDisplayWidget(card_printing) )
					if card_printing.card_faces:
						for i in range(1, len(card_printing.card_faces)):
							copy = card_printing.model_copy(deep = True)
							copy.lca_selected_face = i
							stacked.addWidget( LCACardDisplayWidget(copy) )
					self.__printcarousel_widget.addItem( stacked, card_printing )
			self.__stacked_widget.setCurrentIndex(1)

	def __evt_carousel_updated (self, card: LCAScryfallCardModel | None) -> None:
		logger.debug(card.set_name if card else 'NONE')
		if card:
			self.__cardname_lbl.setText(card.name.split(' // ')[card.lca_selected_face])
			self.__setname_lbl.setText(card.set_name)
			self.__newface_btn.setEnabled(bool(card.card_faces))
		if self.__printcarousel_widget.currentWidget():
			with QSignalBlocker(self.__printcarousel_widget.currentWidget()):
				self.__printcarousel_widget.currentWidget().setCurrentIndex(0)
		self.changed.emit(card)

	def __evt_backtocardsearch_clicked (self) -> None:
		self.__stacked_widget.setCurrentIndex(0)
		self.__printcarousel_widget.clear()

	def __evt_newface (self) -> None:
		self.__printcarousel_widget.currentWidget().setCurrentIndex(
			(self.__printcarousel_widget.currentWidget().currentIndex() + 1) % self.__printcarousel_widget.currentWidget().count()
		)
		card = self.__printcarousel_widget.currentWidget().currentWidget().card
		self.__cardname_lbl.setText(card.name.split(' // ')[card.lca_selected_face])
		self.changed.emit(card)

	def __evt_clearvalue_clicked (self) -> None:
		self.__scryfallsearch_input.setText('')
		self.__cardsearch_results.clear()
		self.__scryfallsearch_btn.show()
		self.__clearvalue_btn.hide()
		self.changed.emit(None)

