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

import json

from loguru import logger

from ..LCATaskThread import LCATaskThread
from ...models.LCAProjectFileModel import LCAProjectFileModel
from ...models.LCAProjectStateModel import LCAProjectStateModel
from ...models.render.LCARPreparedProjectModel import LCARPreparedProjectModel

class LCARProjectPreparerTaskThread (LCATaskThread):

	def _run (self,
		project: LCAProjectFileModel,
	) -> LCARPreparedProjectModel:
		logger.info(f'Preparing project {project.slug()}')
		prepared = LCARPreparedProjectModel(project = project)
		all_state_filenames = project.path_state_all()
		for i, state_filename in enumerate(all_state_filenames):
			self.progress.emit( float(i) / len(all_state_filenames) )
			ts = int(state_filename.stem.split('-')[-1])
			with open(state_filename, 'r', encoding = 'utf-8') as f:
				state_object = json.loads(f.read())
			if not state_object['active']:
				continue
			state_object['project'] = project
			prepared.states[ts] = LCAProjectStateModel(**state_object)
			if prepared.states[ts].mistake_count > len(prepared.markers.mistakes):
				prepared.markers.mistakes.append(ts)
			if prepared.states[ts].muted and (len(prepared.markers.mutes) == 0 or prepared.markers.mutes[-1][1] != 0):
				prepared.markers.mutes.append((ts, 0))
			if not prepared.states[ts].muted and (len(prepared.markers.mutes) > 0 and prepared.markers.mutes[-1][1] == 0):
				prepared.markers.mutes[-1] = (prepared.markers.mutes[-1][0], ts)
			# TODO clips someday
		return prepared

