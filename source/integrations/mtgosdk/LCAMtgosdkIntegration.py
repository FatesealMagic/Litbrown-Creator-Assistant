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
import typing

from loguru import logger
import clr_loader
import pythonnet

from ..LCAIntegration import *
from ..LCAIntegrationErrors import *
from ...common.LCASingleton import LCASingleton

from ...Config import *
from ...Settings import *

class LCAMtgosdkIntegration (LCAIntegration, metaclass = LCASingleton):

	# See __evt_ callbacks below for proper type hint signatures
	class _Signals (QObject):
		on_game_joined = Signal(object, object)
		on_match_state_changed = Signal(object, object)
		on_game_results_changed = Signal(object, object)
		on_message_received = Signal(object, object)

	__BINARIES_FOLDER = str(pathlib.Path(Config().integrations.local.mtgosdk.binaries_folder).resolve())

	__signals = _Signals()

	@property
	def signals (self) -> _Signals:
		return self.__signals

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

	@LCAIntegration.in_context
	def listen_until_mtgo_closed (self, should_continue: typing.Callable[[], bool]) -> None:
		import MTGOSDK
		self.__establish_mtgo_global_callbacks()
		while (abrupt_termination := should_continue()) and MTGOSDK.Core.Remoting.RemoteClient.MTGOProcess():
			time.sleep(0.05)
		logger.info('MTGO closed')
		if abrupt_termination:
			raise LCAIntegrationUnexpectedError

	@staticmethod
	def __callback (func: typing.Callable) -> typing.Callable:
		@functools.wraps(func)
		def wrapper (self, *args, **kwargs) -> typing.Any:
			try:
				return func(self, *args, **kwargs)
			except Exception as e:
				logger.exception(e)
		return wrapper

	def __establish_mtgo_global_callbacks (self) -> None:
		import MTGOSDK
		import System
		MTGOSDK.API.Play.EventManager.GameJoined += System.Action[
			MTGOSDK.API.Play.Event,
			MTGOSDK.API.Play.Games.Game,
		]( self.__evt_game_joined )
		MTGOSDK.API.Play.Match.MatchStateChanged += System.Action[
			MTGOSDK.API.Play.Match,
			MTGOSDK.API.Play.MatchState,
		]( self.__evt_match_state_changed )
		MTGOSDK.API.Play.Games.Game.GameResultsChanged += System.Action[
			MTGOSDK.API.Play.Games.Game,
			System.Collections.Generic.IList[MTGOSDK.API.Play.Games.GamePlayerResult],
		]( self.__evt_game_results_changed )
		MTGOSDK.API.Chat.Channel.MessageReceived += System.Action[
			MTGOSDK.API.Chat.Channel,
			MTGOSDK.API.Chat.Message,
		]( self.__evt_message_received )

	@__callback
	def __evt_game_joined (self,
		event: MTGOSDK.API.Play.Event,
		game: MTGOSDK.API.Play.Games.Game,
	) -> None:
		self.signals.on_game_joined.emit(event, game)

	@__callback
	def __evt_match_state_changed (self,
		match_: MTGOSDK.API.Play.Match,
		match_state: MTGOSDK.API.Play.MatchState,
	) -> None:
		self.signals.on_match_state_changed.emit(match_, match_state)

	@__callback
	def __evt_game_results_changed (self,
		game: MTGOSDK.API.Play.Games.Game,
		results: System.Collections.Generic.IList[MTGOSDK.API.Play.Games.GamePlayerResult],
	) -> None:
		self.signals.on_game_results_changed.emit(game, results)

	@__callback
	def __evt_message_received (self,
		channel: MTGOSDK.API.Chat.Channel,
		message: MTGOSDK.API.Chat.Message,
	) -> None:
		self.signals.on_message_received.emit(channel, message)

	def get_username (self) -> str | None:
		import MTGOSDK
		try:
			return MTGOSDK.API.Client().CurrentUser.Name
		except Exception as e:
			logger.exception(e)
			return None

