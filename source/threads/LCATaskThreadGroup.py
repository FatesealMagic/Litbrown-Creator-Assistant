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

import typing

from PySide6.QtCore import *

from .LCATaskThread import *

class LCATaskThreadGroup (QObject):
	
	complete = Signal(bool)
	error    = Signal(tuple) # [LCATaskThread, Exception, dict[LCATaskThread, object]]
	result   = Signal(dict) # [LCATaskThread, object]

	__threads: tuple[LCATaskThread]
	__results: dict[LCATaskThread, object]
	__handlers: list[tuple[Signal, typing.Callable[[object | Exception], None]]]
	
	NO_RESULT = QObject()

	def __init__ (self, threads: list[LCATaskThread] | tuple[LCATaskThread]):
		super().__init__()
		self.__threads = tuple(threads)
		self.__results = {thread: self.NO_RESULT for thread in threads}
		self.__handlers = []
		self.__setup_thread_signal_connections()

	def __setup_thread_signal_connections (self) -> None:
		for thread in self.__threads:
			result = lambda val, thread = thread : self.__evt_thread_result(val, thread)
			error  = lambda e,   thread = thread : self.__evt_thread_error (e,   thread)
			thread.result.connect(result)
			thread.error.connect(error)
			self.__handlers.append((thread.result, result))
			self.__handlers.append((thread.error, error))

	def __teardown_thread_signal_connections (self) -> None:
		for signal, handler in self.__handlers:
			try:
				signal.disconnect(handler)
			except RuntimeWarning:
				pass
		self.__handlers = []

	def __evt_thread_result (self, val: object, thread: LCATaskThread) -> None:
		self.__results[thread] = val
		for _, result in self.__results.items():
			if result is self.NO_RESULT:
				break
		else:
			self.__teardown_thread_signal_connections()
			self.result.emit(self.__results)
			self.complete.emit(True)

	def __evt_thread_error (self, e: Exception, thread: LCATaskThread) -> None:
		self.__results[thread] = e
		self.__teardown_thread_signal_connections()
		self.error.emit((thread, e, self.__results))
		self.complete.emit(False)

	def start (self) -> None:
		if self.__threads:
			for thread in self.__threads:
				thread.start()
		else:
			self.result.emit(self.__results)
			self.complete.emit(True)

