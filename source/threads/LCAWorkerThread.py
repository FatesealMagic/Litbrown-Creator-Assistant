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

from PySide6.QtCore import *

from .LCAWorkerObject import *

class LCAWorkerThread (QThread):

	worker: LCAWorkerObject

	def __init__ (self, worker: LCAWorkerObject):
		super().__init__()
		self.worker = worker
		worker.moveToThread(self)
		worker.construct.connect(worker.slot_construct)
		worker.destruct.connect(worker.slot_destruct)

	def start (self) -> None:
		super().start()
		self.worker.construct.emit()

	def quit (self) -> None:
		self.worker.destruct.emit()
		super().quit()

