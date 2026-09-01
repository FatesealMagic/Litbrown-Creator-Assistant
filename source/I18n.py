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

import os
import pathlib
import typing

from loguru import logger
import munch
import yaml

from .Settings import *

def I18n (
	key: typing.Type | object,
	/, *,
	_i18n_munches = {},
) -> munch.Munch:
	if type(key) not in ('type', 'ObjectType', 'ModelMetaclass'):
		key = type(key)
	split = key.__module__.split('.')
	i18n_key = None if split[0] == 'source' else f'{split[0]}.{split[1]}'
	if i18n_key not in _i18n_munches.keys():
		logger.info(f'Loading I18n for {i18n_key}')
		with open(
			pathlib.Path.cwd() /
				pathlib.Path(f'plugins/{split[0]}/{split[1]}' if split[0] != 'source' else '.') /
				pathlib.Path(f'assets/i18n/{Settings().tools.general.language}.yaml'),
			'r',
			encoding = 'utf-8',
		) as f:
			_i18n_munches[i18n_key] = munch.munchify(yaml.safe_load(f.read()))
	return _i18n_munches[i18n_key][key.__name__]

