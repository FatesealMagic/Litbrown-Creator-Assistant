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
import typing

from PySide6.QtWidgets import *

class LCAWidget (QWidget):

	def __init__ (self, parent: QWidget | None = None):
		super().__init__(parent)
		self._setup_layout()

	def _setup_layout (self) -> None:
		raise NotImplementedError

	@contextlib.contextmanager
	def block_signals_recursively (self) -> typing.Self:
		original_block_states = self.__set_signals_blocked_recursive(self)
		try:
			yield self
		finally:
			for obj, blocked in original_block_states.items():
				try:
					obj.blockSignals(blocked)
				except RuntimeError:
					pass

	@classmethod
	def __set_signals_blocked_recursive (cls,
		obj: QObject,
		/,
		block = True,
		*,
		_original_block_states: dict = None,
	) -> dict:
		_original_block_states = _original_block_states or {}
		_original_block_states[obj] = obj.blockSignals(True)
		for child in obj.children():
			cls.__set_signals_blocked_recursive(child, block = block, _original_block_states = _original_block_states)
		return _original_block_states