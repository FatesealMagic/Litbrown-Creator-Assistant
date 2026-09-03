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
from ...integrations.foobar.LCAFoobarIntegration import *

class LCACFoobarControllerTaskThread (LCATaskThread):

	def _run (self) -> None:
		with LCAFoobarIntegration() as foobar:
			foobar.play_music()
			self.update.emit(True)
			while not self.isInterruptionRequested():
				time.sleep(0.1)
				new_music = foobar.get_current_music()
				if new_music != LCAProjectState().model.music:
					with LCAProjectState() as state:
						state.model.music = new_music
			foobar.stop_music()

