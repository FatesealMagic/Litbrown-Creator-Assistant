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
import http.server

from ....Settings import *

from .LCADHttpRequestHandler import *

class LCADThreadingHttpServer (http.server.ThreadingHTTPServer):
	
	pid_deque: collections.deque[int]

	def __init__ (self, pid_deque: collections.deque[int]):
		self.pid_deque = pid_deque
		super().__init__( ('', Config().network.port), LCADHttpRequestHandler )

