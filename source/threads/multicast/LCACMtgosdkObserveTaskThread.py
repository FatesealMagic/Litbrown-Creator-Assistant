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

import time

from loguru import logger

from ..LCATaskThread import *
from ...integrations.mtgosdk.LCAMtgosdkIntegration import *

class LCACMtgosdkObserveTaskThread (LCATaskThread):

	__sdk: LCAMtgosdkIntegration

	def _run (self) -> None:
		with LCAMtgosdkIntegration() as sdk:
			self.__sdk = sdk
			sdk.on_game_joined(self.__evt_game_joined)
			self.update.emit(True)
			sdk.listen_until_mtgo_closed()

	def __evt_game_joined (self,
		mtgo_match: MTGOSDK.API.Play.Match,
		mtgo_game: MTGOSDK.API.Play.Games.Game,
	) -> None:
		try:
			if mtgo_game.Status == 'Finished': # TODO check if game ID is already in the state model
				return
			logger.info(f'{mtgo_game.Id} {mtgo_game.Status} {list(mtgo_game.WinningPlayers)}')
			self.__sdk.on_game_results_changed(mtgo_game, self.__evt_game_results_changed)
			logger.info('after register')
		except Exception as e:
			logger.exception(e)

	def __evt_game_results_changed (self,
		mtgo_game: MTGOSDK.API.Play.Games.Game,
		mtgo_results: System.Collections.Generic.IList[MTGOSDK.API.Play.Games.GamePlayerResult],
	) -> None:
		logger.info('In game results changed')
		logger.info(type(mtgo_game))
		logger.info(type(mtgo_results))
		for result in list(mtgo_results):
			logger.info(f'{result.Player.Name} {result.Player.Result}')

