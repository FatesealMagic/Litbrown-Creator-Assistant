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

import contextlib
import os
import pathlib
import shutil
import subprocess

from loguru import logger

from ...Config import *
from ...Settings import *

from ..LCATaskThread import *

class LCACMtgosdkInstallTaskThread (LCATaskThread):

	def _run (self) -> None:
		self.__run_command('winget source update')
		self.__run_command('winget install Microsoft.Dotnet.SDK.10', valid_return_codes = (2316632107,))
		with contextlib.suppress(FileNotFoundError):
			shutil.rmtree(Config().integrations.local.mtgosdk.install_folder)
		pathlib.Path(Config().integrations.local.mtgosdk.install_folder).mkdir(parents = True, exist_ok = True)
		try:
			os.chdir(Config().integrations.local.mtgosdk.install_folder)
			self.__run_command('dotnet new classlib --framework net10.0')
			with open(f'{Config().integrations.local.mtgosdk.install_folder}.csproj', 'w') as f:
				f.write(Config().integrations.local.mtgosdk.csproj)
			self.__run_command('dotnet add package MTGOSDK')
			self.__run_command('dotnet publish -c Release -r win-x64 --self-contained true')
		finally:
			os.chdir('..')
		
	def __run_command (self, command: str, *, valid_return_codes: tuple[int, ...] = ()) -> None:
		result = subprocess.run(command)
		if result.returncode and result.returncode not in valid_return_codes:
			raise RuntimeError(f'{command} {result.returncode}')

