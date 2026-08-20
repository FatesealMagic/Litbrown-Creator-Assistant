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

from collections.abc import Callable
import enum
import string

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ..Config import *
from ..I18n import *
from ..Assets import *
from ..Settings import *
from ..Util import *

from .LCAWidget import *
from ..threads.LCATaskThread import *
from ..integrations.LCAIntegration import *

class LCATaskTrackerWidget (LCAWidget):
	
	complete = Signal(bool)
	error    = Signal(Exception)
	result   = Signal(object)
	update   = Signal(str)
	progress = Signal(float)
	
	class Status (enum.Enum):
		DISABLED = 'disabled'
		STAGED   = 'staged'
		UNSTAGED = 'unstaged'
		SKIPPED  = 'skipped'
		RUNNING  = 'running'
		SUCCESS  = 'success'
		ERROR    = 'error'

	PROGRESS_STYLE = string.Template('''
		QProgressBar {
			background-color: ${bg};
			border: 3px solid ${border};
			border-radius: 6px;
			color: ${color};
			font-weight: bold;
			text-align: center;
		} QProgressBar:chunk {
			background-color: ${chunk};
		}
	''')

	def __init__ (self,
		label: str,
		thread_factory: Callable[[], [LCATaskThread]],
		integration: type[LCAIntegration],
		*args, **kwargs
	):
		self.__label = label
		self.__thread_factory = thread_factory
		self.__integration = integration
		super().__init__(*args, **kwargs)

	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		layout.setContentsMargins(layout.spacing() / 2, layout.spacing() / 2, layout.spacing() / 2, layout.spacing() / 2)
		if actionbtn := QPushButton():
			self.__actionbtn = actionbtn
			actionbtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
			actionbtn.clicked.connect(self.__evt_actionbtn_clicked)
		layout.addWidget(actionbtn, 1)
		layout.addSpacing(layout.spacing())
		if status_widget := QWidget():
			status_layout = QVBoxLayout(status_widget)
			status_layout.setContentsMargins(0, 0, 0, 0)
			if label := QLabel(self.__label):
				label.setAlignment(Qt.AlignCenter)
				font = label.font()
				font.setPointSize(font.pointSize() * 1.4)
				font.setWeight(QFont.Weight.Bold)
				label.setFont(font)
			status_layout.addWidget(label, alignment = Qt.AlignCenter)
			if progressbar := QProgressBar():
				self.__progressbar = progressbar
				self.__progressbar.setTextVisible(True)
				font = progressbar.font()
				font.setPointSize(font.pointSize() * 1.2)
				font.setWeight(QFont.Weight.Bold)
				progressbar.setFont(font)
				self.__set_progressbar_stopped()
			status_layout.addWidget(progressbar)
		layout.addWidget(status_widget, 4)
		self.__set_status(self.Status.STAGED if self.__integration.is_initialized() else self.Status.DISABLED)
		Settings().signals().changed.connect(self.__keep_status_consistent_with_integration_state)
		
	def __get_progress_style_params (self, status: Status) -> None:
		return {
			self.Status.DISABLED: {
				'bg':     '#000',
				'border': '#f66',
				'color':  '#f66',
				'chunk':  '#f66',
			},
			self.Status.STAGED: {
				'bg':     '#8F8FDC',
				'border': '#8F8FDC',
				'color':  'black',
				'chunk':  '#8F8FDC',
			},
			self.Status.UNSTAGED: {
				'bg':     '#666',
				'border': '#666',
				'color':  'white',
				'chunk':  '#666',
			},
			self.Status.SKIPPED: {
				'bg':     '#333',
				'border': '#333',
				'color':  '#CCC',
				'chunk':  '#333',
			},
			self.Status.RUNNING: {
				'bg':     '#58DEDE',
				'border': '#00a8a8',
				'color':  'black',
				'chunk':  '#00a8a8',
			},
			self.Status.SUCCESS: {
				'bg':     '#73f837',
				'border': '#73f837',
				'color':  'black',
				'chunk':  '#73f837',
			},
			self.Status.ERROR: {
				'bg':     '#a80813',
				'border': '#a80813',
				'color':  'white',
				'chunk':  '#a80813',
			},
		}[status]

	def __set_progressbar_stopped (self) -> None:
		self.__progressbar.setRange(0, 100)
		self.__progressbar.setValue(0)

	def __set_progressbar_running (self) -> None:
		self.__progressbar.setRange(0, 0)
		self.__progressbar.setValue(0)

	def __evt_actionbtn_clicked (self) -> None:
		match self.__status:
			case self.Status.DISABLED:
				Util.launch_new_instance('configure', [self.__integration.integration_name()])
			case self.Status.STAGED:
				self.__set_status(self.Status.UNSTAGED)
			case self.Status.UNSTAGED:
				self.__set_status(self.Status.STAGED)
			case self.Status.ERROR:
				self.__set_status(self.Status.RUNNING)

	def __keep_status_consistent_with_integration_state (self) -> None:
		logger.debug('new settings update')
		if self.__status == self.Status.DISABLED and self.__integration.is_initialized():
			self.__set_status(self.Status.STAGED)
		elif self.__status in (self.Status.STAGED, self.Status.UNSTAGED) and not self.__integration.is_initialized():
			self.__set_status(self.Status.DISABLED)
		else:
			logger.debug(self.__status)
			logger.debug(self.__integration.is_initialized())

	def __set_status (self, status: Status) -> None:
		if status == getattr(self, '__status', None):
			return
		self.__status = status
		self.__actionbtn.setText(I18n(self).actionbtn[status.value])
		self.__progressbar.setFormat(I18n(self).progressbar[status.value])
		self.__progressbar.setStyleSheet(self.PROGRESS_STYLE.substitute(**self.__get_progress_style_params(status)))
		self.__actionbtn.setEnabled(status not in (self.Status.SKIPPED, self.Status.RUNNING, self.Status.SUCCESS))
		if status == self.Status.RUNNING:
			self.__set_progressbar_running()
			self.__start_task_thread()

	def execute (self) -> None:
		if self.__status in (self.Status.DISABLED, self.Status.UNSTAGED):
			self.__set_status(self.Status.SKIPPED)
		elif self.__status == self.Status.STAGED:
			self.__set_status(self.Status.RUNNING)

	def __start_task_thread (self) -> None:
		self.__thread = self.__thread_factory()
		logger.info(f'RUNNING TASK: {self.__thread}')
		self.__thread.complete.connect(self.__evt_thread_complete)
		self.__thread.error.connect(self.__evt_thread_error)
		self.__thread.result.connect(self.__evt_thread_result)
		self.__thread.update.connect(self.__evt_thread_update)
		self.__thread.progress.connect(self.__evt_thread_progress)
		self.__thread.start()

	def __evt_thread_complete (self, success: bool) -> None:
		self.complete.emit(success)

	def __evt_thread_error (self, error: Exception) -> None:
		logger.warning(f'{self.__thread} : {type(error)}')
		self.__set_progressbar_stopped()
		self.__set_status(self.Status.ERROR)
		self.error.emit(error)

	def __evt_thread_result (self, result: object) -> None:
		logger.info('Complete: {self.__thread}')
		self.__set_progressbar_stopped()
		self.__set_status(self.Status.SUCCESS)
		self.result.emit(result)

	def __evt_thread_update (self, update: str) -> None:
		self.update.emit(update)

	def __evt_thread_progress (self, progress: float) -> None:
		self.__progressbar.setRange(0, 100)
		self.__progressbar.setValue(100 * progress)
		self.__progressbar.resetFormat()
		self.progress.emit(progress)

