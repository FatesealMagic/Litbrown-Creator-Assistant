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

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtNetwork import *
from PySide6.QtWidgets import *

from ...Settings import *

from ..LCAWidget import *

class LCACConnectionInfoDisplayWidget (LCAWidget):
	
	__integration_name: str
	__profile_pic_url: str = ''
	
	__profilepic_lbl: QLabel
	__display_lbl: QLabel
	__handle_lbl: QLabel

	def __init__ (self, integration_name: str):
		self.__integration_name = integration_name
		super().__init__()

	def _setup_layout (self) -> None:
		layout = QHBoxLayout(self)
		layout.addStretch(1)
		if profilepic_lbl := QLabel():
			self.__profilepic_lbl = profilepic_lbl
			profilepic_lbl.setStyleSheet('QLabel { border-radius: 44px; margin-right: 1em; }')
		layout.addWidget(profilepic_lbl)
		if display_handle_widget := QWidget():
			display_handle_layout = QVBoxLayout(display_handle_widget)
			display_handle_layout.setContentsMargins(0, 0, 0, 0)
			display_handle_layout.setSpacing(0)
			if display_lbl := QLabel():
				self.__display_lbl = display_lbl
				display_lbl.setStyleSheet('QLabel { font-size: 22pt; font-weight: bold; }')
			display_handle_layout.addWidget(display_lbl)
			if handle_lbl := QLabel():
				self.__handle_lbl = handle_lbl
				handle_lbl.setStyleSheet('QLabel { font-size: 16pt; font-weight: bold; }')
			display_handle_layout.addWidget(handle_lbl)
		layout.addWidget(display_handle_widget)
		layout.addStretch(1)
		self.__update_display()
		Settings().signals().changed.connect(self.__update_display)

	def __update_display (self) -> None:
		integration = getattr(Settings().integrations, self.__integration_name)
		if integration.auth:
			self.__handle_lbl.show()
			self.__handle_lbl.setText(integration.handle)
			self.__display_lbl.setText(integration.display_name)
			self.__update_profilepic_lbl(integration.profile_pic_url)
		else:
			self.__profilepic_lbl.clear()
			self.__profilepic_lbl.hide()
			self.__handle_lbl.hide()
			self.__display_lbl.setText(I18n(self).not_connected)

	def __update_profilepic_lbl (self, url: str) -> None:
		dlmanager = QNetworkAccessManager(self)
		dlmanager.finished.connect(self.__show_profilepic_lbl)
		dlmanager.get(QNetworkRequest(url))

	def __show_profilepic_lbl (self, reply: QNetworkReply) -> None:
		if reply.error() != QNetworkReply.NoError:
			logger.warning(f'Error getting {self.__integration_name} profile pic: {reply.error()}')
			return
		in_pixmap = QPixmap()
		in_pixmap.loadFromData(reply.readAll())
		out_pixmap = QPixmap(in_pixmap.size())
		out_pixmap.fill(Qt.transparent)
		painter = QPainter(out_pixmap)
		painter.setRenderHint(QPainter.Antialiasing)
		path = QPainterPath()
		path.addEllipse(0, 0, in_pixmap.size().width(), in_pixmap.size().height())
		painter.setClipPath(path)
		painter.drawPixmap(0, 0, in_pixmap)
		painter.end()
		icon = QIcon(out_pixmap)
		self.__profilepic_lbl.clear()
		self.__profilepic_lbl.show()
		self.__profilepic_lbl.setPixmap(icon.pixmap(QSize(80, 80)))

