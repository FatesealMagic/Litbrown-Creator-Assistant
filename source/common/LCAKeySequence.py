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

from PySide6.QtGui import QKeySequence

class LCAKeySequence (QKeySequence):

	__PYSIDE_TO_PYNPUT_REMOVALS = (
		'num',
	)

	__PYSIDE_TO_PYNPUT_MAPPING = {

		'alt':       '<alt>',
		'backspace': '<backspace>',
		'capslock':  '<caps_lock>',
		'meta':      '<cmd>',
		'ctrl':      '<ctrl>',
		'del':       '<delete>',
		'down':      '<down>',
		'end':       '<end>',
		'enter':     '<enter>',
		'return':    '<enter>',
		'esc':       '<esc>',
		'home':      '<home>',
		'left':      '<left>',
		'pgdown':    '<page_down>',
		'pgup':      '<page_up>',
		'right':     '<right>',
		'shift':     '<shift>',
		' ':         '<space>',
		'tab':       '<tab>',
		'up':        '<up>',

		'media play': '<media_play_pause>',
		'media pause': '<media_play_pause>',
		'media stop': '<media_stop>',
		'volume mute': '<media_volume_mute>',
		'volume down': '<media_volume_down>',
		'volume up': '<media_volume_up>',
		'media previous': '<media_previous>',
		'media next': '<media_next>',

		'ins':        '<insert>',
		'menu':       '<menu>',
		'numlock':    '<num_lock>',
		'pause':      '<pause>',
		'print':      '<print_screen>',
		'space':      '<space>',
		'scrolllock': '<scroll_lock>',
		
		'f1':        '<f1>',
		'f2':        '<f2>',
		'f3':        '<f3>',
		'f4':        '<f4>',
		'f5':        '<f5>',
		'f6':        '<f6>',
		'f7':        '<f7>',
		'f8':        '<f8>',
		'f9':        '<f9>',
		'f10':       '<f10>',
		'f11':       '<f11>',
		'f12':       '<f12>',
		'f13':       '<f13>',
		'f14':       '<f14>',
		'f15':       '<f15>',
		'f16':       '<f16>',
		'f17':       '<f17>',
		'f18':       '<f18>',
		'f19':       '<f19>',
		'f20':       '<f20>',
		'f21':       '<f21>',
		'f22':       '<f22>',
		'f23':       '<f23>',
		'f24':       '<f24>',

	}

	def to_keyboard_string (self) -> None:
		ret = []
		for part in self.toString().lower().split('+'):
			if part in self.__PYSIDE_TO_PYNPUT_REMOVALS:
				continue
			ret.append(self.__PYSIDE_TO_PYNPUT_MAPPING.get(part, part))
		return '+'.join(ret)

