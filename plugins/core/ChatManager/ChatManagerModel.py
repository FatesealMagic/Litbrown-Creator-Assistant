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

import pydantic

class ChatManagerModel (pydantic.BaseModel, validate_assignment = True, extra = 'forbid'):
	width: int = 300
	banned_timestamps: list[int] = []

	class Message (pydantic.BaseModel, validate_assignment = True, extra = 'forbid'):
		timestamp: str
		message: str
		screenshot: str
		platform_name: typing.Literal['youtube', 'twitch', 'patreon']
		platform_message_id: str
		platform_user_id: str
	messages: list[Message] = []

