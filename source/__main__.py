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
import importlib
import os
import string
import sys

from loguru import logger
import requests

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .Assets import *
from .Config import *
from .I18n import *
from .Settings import *
from .Util import *

from .gui.LCAMainWindow import *
from .cli.LCAMainUtility import *

class LCA:
	
	__LOGGER_FORMAT = f'<green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | ' \
		f'<level>{{level: <8}}</level> | ' \
		f'<magenta>{{process.id: <6}} {Util.app_name().ljust(15)} {{thread.name: <20}}</magenta> | ' \
		f'<cyan>{{name}}</cyan>:<cyan>{{function}}</cyan>:<cyan>{{line}}</cyan> - <level>{{message}}</level>'
	
	__context: filelock.FileLock | contextlib.nullcontext
	__app: QApplication | None = None
	__hue: float = -1.0

	def __init__ (self):
		logger.configure( handlers = [
			{ 'sink': sys.stderr or (lambda msg : None), 'format': self.__LOGGER_FORMAT, },
			{ 'sink': './logs/{time}.log', 'format': self.__LOGGER_FORMAT, 'rotation': '5 MB' },
		] )
		I18n.load(Assets.yaml(f'i18n/{Settings().tools.general.language}.yaml'))
		# TODO can't get this working well with multiple instances running
		# os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = str(Config().network.chromium_debug_port)

	def run (self) -> None:
		logger.info(sys.argv)
		if Util.app_name() != 'daemon':
			self.__notify_daemon_of_pid()
		if Util.app_name() in Util.CLI_TOOLS:
			self.__cli_launch(Util.app_name())
		elif Util.app_name() in Util.GUI_TOOLS:
			self.__gui_launch(Util.app_name())

	def __notify_daemon_of_pid (self) -> None:
		rsp = requests.post(f'http://127.0.0.1:{Config().network.http_serve_port}/-/register-lcapid/{os.getpid()}')
		assert 200 <= rsp.status_code < 300

	def __cli_launch (self, mode: str) -> None:
		self.__app = None
		utility_name = f'LCA{mode[0].upper()}MainUtility'
		utility_module = importlib.import_module(f'source.cli.{mode}.{utility_name}')
		getattr(utility_module, utility_name)().run()

	def __gui_launch (self, mode: str) -> None:
		self.__app = QApplication()
		self.__gui_set_styles()
		window_name = f'LCA{mode[0].upper()}MainWindow'
		window_module = importlib.import_module(f'source.gui.{mode}.{window_name}')
		self.__main_window = getattr(window_module, window_name)()
		self.__main_window.show()
		self.__app.exec()

	def __gui_set_styles (self) -> None:
		self.__app.setStyle('fusion')
		self.__gui_set_font()
		self.__gui_load_colors()
		Settings().signals().changed.connect(self.__gui_load_colors)

	def __gui_set_font (self) -> None:
		font_id = QFontDatabase.addApplicationFontFromData(QByteArray(Assets.binary(
			'font/NotoSans-VariableFont_wdth,wght.ttf'
		)))
		font = QFont(QFontDatabase.applicationFontFamilies(font_id)[0], 11)
		font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
		self.__app.setFont(font)

	def __gui_load_colors (self) -> None:
		if math.fabs(self.__hue - Settings().tools.general.accent_hue) < 0.5:
			return
		self.__hue = Settings().tools.general.accent_hue
		palette = self.__app.palette()
		palette.setColor(QPalette.ColorRole.Light, Util.oklch_to_hex(
			Config().style.action_l, Config().style.action_c, Settings().tools.general.accent_hue
		))
		palette.setColor(QPalette.ColorRole.Mid, Util.oklch_to_hex(
			Config().style.accent_l, Config().style.accent_c, Settings().tools.general.accent_hue
		))
		palette.setColor(QPalette.ColorRole.Link, Util.oklch_to_hex(
			Config().style.accent_l, Config().style.accent_c, Settings().tools.general.accent_hue
		))
		palette.setColor(QPalette.ColorRole.LinkVisited, Util.oklch_to_hex(
			Config().style.accent_l, Config().style.accent_c, Settings().tools.general.accent_hue
		))
		palette.setColor(QPalette.ColorRole.Dark, Util.oklch_to_hex(
			Config().style.hint_l, Config().style.hint_c, Settings().tools.general.accent_hue
		))
		palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(Config().style.foreground_drk))
		self.__app.setPalette(palette)
		# TODO need to recalculate the stylesheet :( this is EXPENSIVE. Find a way around this?
		self.__app.setStyleSheet(string.Template(Assets.text('style/global.qss')).substitute(Config().style.model_dump()))

if __name__ == '__main__':
	LCA().run()

