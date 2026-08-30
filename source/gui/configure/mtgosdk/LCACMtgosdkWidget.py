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
from PySide6.QtWidgets import *

from ....Assets import *
from ....Config import *
from ....I18n import *
from ....Settings import *

from ...LCAWidget import *
from ...LCAPopupMessage import *
from ....threads.configure.LCACMtgosdkInstallTaskThread import *

class LCACMtgosdkWidget (LCAWidget):
	
	__install_mtgosdk_thread: LCACMtgosdkInstallTaskThread

	def _setup_layout (self) -> None:
		layout = QVBoxLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		if info_lbl := QLabel(I18n(self).info):
			info_lbl.setWordWrap(True)
		layout.addWidget(info_lbl)
		if install_lbl := QLabel(I18n(self).install):
			install_lbl.setWordWrap(True)
		layout.addWidget(install_lbl)
		for disclaimer in I18n(self).disclaimer:
			if disclaimer_lbl := QLabel(f'<html><b>{disclaimer}</b></html>'):
				disclaimer_lbl.setWordWrap(True)
				disclaimer_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
				disclaimer_lbl.setOpenExternalLinks(True)
			layout.addWidget(disclaimer_lbl)
		if install_btn := QPushButton(' ' + I18n(self).install_btn):
			install_btn.setProperty('css_class', 'big')
			install_btn.setIcon(Assets.QIcon('external/icons/mtgosdk.png'))
			install_btn.clicked.connect(self.__evt_install_clicked)
		layout.addWidget(install_btn)
		if remove_btn := QPushButton(I18n(self).remove_btn):
			remove_btn.setStyleSheet('font-size: 13pt;')
			remove_btn.clicked.connect(self.__evt_remove_clicked)
		layout.addWidget(remove_btn)
		layout.addStretch()

	def __evt_install_clicked (self) -> None:
		if LCAPopupMessage.warning(
			I18n(self).confirm,
			QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
		) != QMessageBox.StandardButton.Ok:
			return
		logger.info('Installing MTGOSDK')
		self.setEnabled(False)
		self.__install_mtgosdk_thread = LCACMtgosdkInstallTaskThread()
		self.__install_mtgosdk_thread.complete.connect(self.__slot_install_complete)
		self.__install_mtgosdk_thread.start()

	@Slot(bool)
	def __slot_install_complete (self, success: bool) -> None:
		self.setEnabled(True)
		if success:
			LCAPopupMessage.info(I18n(self).install_success)
		else:
			LCAPopupMessage.error(I18n(self).install_failed)

	def __evt_remove_clicked (self) -> None:
		if LCAPopupMessage.warning(
			I18n(self).remove_confirm,
			QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
		) != QMessageBox.StandardButton.Ok:
			return
		logger.info('Removing MTGOSDK')
		try:
			path = pathlib.Path(Config().integrations.local.mtgosdk.install_folder).resolve()
			if path.is_dir():
				shutil.rmtree(str(path))
				LCAPopupMessage.info(I18n(self).remove_success)
			else:
				LCAPopupMessage.info(I18n(self).remove_notneeded)
		except Exception as e:
			logger.exception(e)
			LCAPopupMessage.error(I18n(self).remove_failed)

