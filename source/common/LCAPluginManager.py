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

import importlib
import pathlib
import sys

from loguru import logger
import munch
import yaml

from PySide6.QtWidgets import *

from ..Config import *
from ..Settings import *

class LCAPluginManager:

	__loaded_plugins = {}

	@classmethod
	def list_plugins (cls) -> list[tuple[str, str]]:
		ret = []
		for author_path in pathlib.Path(Config().plugins.path).glob('*'):
			if not author_path.is_dir():
				continue
			for plugin_path in author_path.glob('*'):
				if not plugin_path.is_dir():
					continue
				import_path = f'{author_path.name}.{plugin_path.name}'
				try:
					ret.append((import_path, cls.__get_plugin_manifest(import_path).name[Settings().tools.general.language]))
				except Exception as e:
					logger.warning(f'Error loading plugin {import_path}:')
					logger.exception(e)
		logger.debug(ret)
		return sorted(ret)

	@classmethod
	def list_loaded_plugins (cls) -> list[str]:
		return cls.__loaded_plugins.keys()

	@classmethod
	def __get_plugin_manifest (cls, import_path: str) -> munch.Munch:
		with open(
			cls.__get_plugin_file(import_path, f'manifest.yaml'),
			'r',
			encoding = 'utf-8',
		) as f:
			return munch.munchify(yaml.safe_load(f.read()))

	@classmethod
	def is_plugin_loaded (cls, import_path: str) -> bool:
		return import_path in cls.__loaded_plugins.keys()

	@classmethod
	def load_plugin (cls, parent: QWidget, import_path: str) -> LCAMPluginWidget | None:
		try:
			root = pathlib.Path(__file__).parent.parent.parent
			if root not in sys.path:
				sys.path.insert(0, root)
			plugin_path = cls.__get_plugin_file(import_path, '__init__.py')
			spec = importlib.util.spec_from_file_location(import_path, str(plugin_path))
			pkg = importlib.util.module_from_spec(spec)
			sys.modules[import_path] = pkg
			spec.loader.exec_module(pkg)
			cls.__loaded_plugins[import_path] = pkg
			if len(pkg.__all__) != 1:
				raise RuntimeError(f'Plugin attempts to export more than one object or widget: {pkg.__all__}')
			return getattr(pkg, pkg.__all__[0])(
				parent = parent,
				import_path = import_path,
				title = cls.__get_plugin_manifest(import_path).name[Settings().tools.general.language],
			)
		except Exception as e:
			cls.unload_plugin(import_path)
			logger.warning(f'Error loading plugin {import_path}:')
			logger.exception(e)
			return None

	@classmethod
	def unload_plugin (cls, import_path: str) -> None:
		if import_path in cls.__loaded_plugins:
			del cls.__loaded_plugins[import_path]
		logger.debug(cls.__loaded_plugins)
		if import_path in sys.modules:
			del sys.modules[import_path]

	@classmethod
	def __get_plugin_file (cls, import_path: str, filename: str) -> pathlib.Path:
		author, plugin = import_path.split('.')
		return pathlib.Path(f'{Config().plugins.path}/{author}/{plugin}/{filename}')