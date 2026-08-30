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

import collections
import requests
import sys
import time

import filelock
from loguru import logger
import psutil

from ...Config import *

from ..LCAMainUtility import *
from ...threads.daemon.http_server.LCADHttpServerThread import *

class LCADMainUtility (LCAMainUtility):
	
	def run (self) -> None:
		try:
			with filelock.FileLock(Config().tools.daemon.filelock, timeout = 0):
				popen = Util.launch_new_instance('launcher')
				pid_deque = collections.deque([popen.pid])
				server_thread = LCADHttpServerThread(pid_deque)
				server_thread.start()
				while len(pid_deque):
					time.sleep(0.2)
					pids_to_remove = []
					for pid in pid_deque:
						if not psutil.pid_exists(pid):
							pids_to_remove.append(pid)
					for pid in pids_to_remove:
						logger.info(f'PID {pid} dead, no longer watching')
						try:
							while True:
								pid_deque.remove(pid)
						except ValueError:
							pass
				logger.info('All PIDs dead, shutting down')
		except filelock.Timeout:
			logger.warning(f'Daemon already spun up, shutting down')
		except Exception as e:
			logger.exception(e)

