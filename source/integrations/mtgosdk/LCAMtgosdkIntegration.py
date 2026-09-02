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

import functools
import os
import pathlib
import sys

from loguru import logger
import clr_loader
import pythonnet

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *

from ...Config import *
from ...Settings import *

class LCAMtgosdkIntegration (LCAIntegration):

	__client: MTGOSDK.API.Client

	__BINARIES_FOLDER = str(pathlib.Path(Config().integrations.local.mtgosdk.binaries_folder).resolve())

	@classmethod
	def is_initialized (cls) -> bool:
		return pathlib.Path(f'{cls.__BINARIES_FOLDER}/MTGOSDK.dll').is_file()

	@classmethod
	@functools.cache
	def _connect (cls) -> None:
		pythonnet.load(clr_loader.get_coreclr())
		import System
		def assembly_resolver (sender: object, args: System.ResolveEventArgs) -> System.Reflection.RuntimeAssembly | None:
			import System
			path = pathlib.Path(f'{cls.__BINARIES_FOLDER}/{args.Name.split(',')[0].strip()}.dll')
			if path.is_file():
				return System.Reflection.Assembly.LoadFrom(str(path))
			return None
		System.AppDomain.CurrentDomain.AssemblyResolve += assembly_resolver
		for dll in ('WindowsBase', 'PresentationCore', 'PresentationFramework', 'MTGOSDK'):
			System.Reflection.Assembly.LoadFrom(str(pathlib.Path(f'{cls.__BINARIES_FOLDER}/{dll}.dll')))
		import MTGOSDK

	def _disconnect (self) -> None:
		pass

	def __invoke_callback (self,
		callback: typing.Callable,
		args: tuple,
	) -> None:
		try:
			callback(*args)
		except Exception as e:
			logger.exception(e)

	def on_game_joined (self,
		callback: typing.Callable[ [
			MTGOSDK.API.Play.Match,
			MTGOSDK.API.Play.Games.Game,
		], None ],
	) -> None:
		import MTGOSDK; import System
		MTGOSDK.API.Play.EventManager.GameJoined += System.Action[
			MTGOSDK.API.Play.Event,
			MTGOSDK.API.Play.Games.Game,
		]( lambda *args : self.__invoke_callback(callback, args) )
		logger.debug(f'Registered {callback}')

	def on_match_state_changed (self,
		match_: MTGOSDK.API.Play.Match,
		callback: typing.Callable[ [
			MTGOSDK.API.Play.Match,
			MTGOSDK.API.Play.MatchState,
		], None ],
	) -> None:
		import MTGOSDK; import System
		match_.OnMatchStateChanged += System.Action[
			MTGOSDK.API.Play.MatchState,
		]( lambda *args : self.__invoke_callback(callback, (match_,) + args) )
		logger.debug(f'Registered {callback}')

	def on_game_results_changed (self,
		game: MTGOSDK.API.Play.Games.Game,
		callback: typing.Callable[ [
			MTGOSDK.API.Play.Games.Game,
			System.Collections.Generic.IList[MTGOSDK.API.Play.Games.GamePlayerResult],
		], None ],
	) -> None:
		import MTGOSDK; import System
		game.OnGameResultsChanged += System.Action[
			System.Collections.Generic.IList[MTGOSDK.API.Play.Games.GamePlayerResult],
		]( lambda *args : self.__invoke_callback(callback, (game,) + args) )
		logger.debug(f'Registered {callback}')

	def get_username (self) -> str | None:
		import MTGOSDK
		try:
			return MTGOSDK.API.Client().CurrentUser.Name
		except Exception as e:
			logger.exception(e)
			return None

	@LCAIntegration.in_context
	def listen_until_mtgo_closed (self, should_continue: typing.Callable[[], bool]) -> None:
		import MTGOSDK
		while (abrupt_termination := should_continue()) and MTGOSDK.Core.Remoting.RemoteClient.MTGOProcess():
			time.sleep(0.05)
		logger.debug('MTGO closed')
		if abrupt_termination:
			raise LCAIntegrationUnexpectedError

