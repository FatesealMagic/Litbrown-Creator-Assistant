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
import io
import os
import pathlib
import shutil
import stat
import zipfile

from loguru import logger
import requests

from ...Config import *
from ...Settings import *

from ..LCATaskThread import *

class LCACShotcutInstallTaskThread (LCATaskThread):

	def _run (self,
		platform: str,
	) -> None:
		with contextlib.suppress(FileNotFoundError):
			for root, dirs, files in os.walk(Config().integrations.local.shotcut.install_folder):
				for object in files + dirs:
					os.chmod(os.path.join(root, object), stat.S_IWRITE)
			os.chmod(Config().integrations.local.shotcut.install_folder, stat.S_IWRITE)
			shutil.rmtree(Config().integrations.local.shotcut.install_folder)
		pathlib.Path(Config().integrations.local.shotcut.install_folder).mkdir(parents = True, exist_ok = True)
		rsp = requests.get(Config().integrations.local.shotcut.dlinfo_uri)
		if not 200 <= rsp.status_code <= 299:
			raise RuntimeError(f'Shotcut dlinfo failed with response code {rsp.status_code}')
		for entry in rsp.json()['assets']:
			if platform in entry['name'] and entry['name'].endswith('.zip'):
				rsp = requests.get(entry['browser_download_url'])
				if not 200 <= rsp.status_code <= 299:
					raise RuntimeError(f'Shotcut download at url {entry['browser_download_url']} returned unexpected status code {rsp.status_code}')
				zip = zipfile.ZipFile(io.BytesIO(rsp.content))
				zip.extractall(Config().integrations.local.shotcut.install_folder)
				zip.close()
				return
		raise RuntimeError('Could not find download candidate')

