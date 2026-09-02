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
from ...common.LCAProjectState import *
from ...models.LCAProjectStateModel import *
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
		match_model = LCAProjectState().model.mtgo_match_from_id(mtgo_match.Id)
		if match_model:
			game_model = LCAProjectState().model.mtgo_game_from_id(mtgo_game.Id)
			if game_model:
				if str(mtgo_game.Status) == 'Finished':
					victory = self.__sdk.get_username() in [winner.Name for winner in list(mtgo_game.WinningPlayers)]
					with LCAProjectState() as state:
						game_model.victory = victory
				return
			logger.info(f'Started MTGO game ({mtgo_game.Id}) within existing match ({mtgo_match.Id})')
			game_model = LCAProjectStateModel.Mtgo.Match.Game(
				id = mtgo_game.Id,
			)
			self.__sdk.on_game_results_changed(mtgo_game, self.__evt_game_results_changed)
			with LCAProjectState() as state:
				match_model.games.append(game_model)
			return
		logger.info(f'Started MTGO game ({mtgo_game.Id}) within new match ({mtgo_match.Id})')
		match_model = LCAProjectStateModel.Mtgo.Match(
			id = mtgo_match.Id,
			best_of = mtgo_match.MaxGames,
			opponents = [ player.Name for player in list(mtgo_game.Players) if player.Name != self.__sdk.get_username() ],
			games = [ LCAProjectStateModel.Mtgo.Match.Game(
				id = mtgo_game.Id,
			) ],
		)
		self.__sdk.on_match_state_changed(mtgo_match, self.__evt_match_state_changed)
		self.__sdk.on_game_results_changed(mtgo_game, self.__evt_game_results_changed)
		with LCAProjectState() as state:
			state.model.mtgo.matches.append(match_model)

	def __evt_match_state_changed (self,
		mtgo_match: MTGOSDK.API.Play.Match,
		mtgo_match_state: MTGOSDK.API.Play.MatchState,
	) -> None:
		logger.warning(f'in match state changed: {mtgo_match_state}')
		if not len(list(mtgo_match.WinningPlayers)) and not len(list(mtgo_match.LosingPlayers)):
			return
		match_model = LCAProjectState().model.mtgo_match_from_id(mtgo_match.Id)
		if not match_model:
			return
		victory = self.__sdk.get_username() in [winner.Name for winner in list(mtgo_match.WinningPlayers)]
		if victory != match_model.victory:
			with LCAProjectState() as state:
				match_model.victory = victory

	def __evt_game_results_changed (self,
		mtgo_game: MTGOSDK.API.Play.Games.Game,
		mtgo_results: System.Collections.Generic.IList[MTGOSDK.API.Play.Games.GamePlayerResult],
	) -> None:
		victory = self.__sdk.get_username() in [result.Player for result in list(mtgo_results) if str(result.Result) == 'Win']
		game_model = LCAProjectState().model.mtgo_game_from_id(mtgo_game.Id)
		if not game_model:
			return
		with LCAProjectState() as state:
			game_model.victory = victory

