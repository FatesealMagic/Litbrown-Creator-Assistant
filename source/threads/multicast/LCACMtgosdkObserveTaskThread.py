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
		logger.info(f'{mtgo_match.Id} {mtgo_match.Token}')
		if str(mtgo_game.Status) == 'Finished': # TODO check if game ID is already in the state model
			logger.info(f'{list(mtgo_game.Players)} {list(mtgo_game.WinningPlayers)}')
		logger.info(f'{mtgo_game.Id} {mtgo_game.Status} {list(mtgo_game.WinningPlayers)}')
		self.__sdk.on_game_results_changed(mtgo_game, self.__evt_game_results_changed)
		logger.info('after register')

		for match_model in LCAProjectState().model.mtgo.matches:
			if match_model.id == mtgo_match.Id:
				for game_model in match_model.games:
					if game_model.id == mtgo_game.Id:
						if str(mtgo_game.Status) == 'Finished':
							winners = [winner.Name for winner in list(mtgo_game.WinningPlayers)]
							losers = [player for player in match_model.players if player not in winners]
							with LCAProjectState() as state:
								game_model.winners = winners
								game_model.losers = losers
						return
				logger.info(f'Started MTGO game ({mtgo_game.Id}) within existing match ({mtgo_match.Id})')
				game_model = LCAProjectStateModel.Mtgo.Match.Game(
					id = mtgo_game.Id,
				)
				self.__sdk.on_game_results_changed(mtgo_game, self.__evt_game_results_changed)
				with LCAProjectState() as state:
					match_model.games.append(game_model)
				return
		logger.info(f'Started MTGO game({mtgo_game.Id}) within new match ({mtgo_match.Id})')
		match_model = LCAProjectStateModel.Mtgo.Match(
			id = mtgo_match.Id,
			best_of = mtgo_match.MaxGames,
			players = [ player.Name for player in list(mtgo_game.Players) ],
			games = [ LCAProjectStateModel.Mtgo.Match.Game(
				id = mtgo_game.Id,
			) ],
		)
		self.__sdk.on_game_results_changed(mtgo_game, self.__evt_game_results_changed)
		with LCAProjectState() as state:
			state.model.mtgo.matches.append(match_model)

	def __evt_game_results_changed (self,
		mtgo_game: MTGOSDK.API.Play.Games.Game,
		mtgo_results: System.Collections.Generic.IList[MTGOSDK.API.Play.Games.GamePlayerResult],
	) -> None:
		winners = [result.Player for result in list(mtgo_results) if str(result.Result) == 'Win']
		losers = [result.Player for result in list(mtgo_results) if str(result.Result) == 'Loss']
		for match_model in LCAProjectState().model.mtgo.matches:
			if match_model.id == mtgo_game.Match.Id:
				for game_model in match_model.games:
					if game_model.id == mtgo_game.Id:
						with LCAProjectState() as state:
							game_model.winners = winners
							game_model.losers = losers

