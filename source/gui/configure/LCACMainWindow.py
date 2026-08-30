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

import importlib

from loguru import logger

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ...Config import *
from ...I18n import *
from ...Assets import *

from ..LCAMainWindow import *
from ..LCASideTabWidget import *
from ..LCATabbedDataViewWidget import *
from .settings.LCACSettingsLCAWidget import *
from .settings.LCACSettingsMembershipTierWidget import *
from .settings.LCACSettingsOrganizationSeriesWidget import *
from .settings.LCACSettingsAffiliatesWidget import *

class LCACMainWindow (LCAMainWindow):
	
	__TAB_NAMES = (
		'youtube', 'twitch', 'patreon', 'discord', 'bluesky', 'twitter', 'reddit', 'moxfield',
		'mtgosdk', 'obs', 'shotcut', 'vlc',
	)
	
	def _initialize_window (self) -> None:
		self.setWindowIcon(Assets.QIcon('icons/configure.ico'))
		self.setWindowTitle(I18n(self).title)
		self.resize(800, 800)

	def _setup_layout (self) -> None:
		central_widget = LCASideTabWidget()
		central_widget.addWidget(self.__build_settings_tab(), I18n(self).tabs.settings.title, f'icons/settings.png')
		for tab in self.__TAB_NAMES:
			module_name = f'.{tab.lower()}.LCAC{tab.title()}Widget'
			tab_module = importlib.import_module(module_name, __name__.rpartition('.')[0])
			central_widget.addWidget(
				getattr(tab_module, module_name.split('.')[-1])(),
				I18n(self).tabs[tab],
				f'external/icons/{tab}.png'
			)
		logger.debug(Util.app_args())
		if Util.app_args() and (tab_name := Util.app_args()[0].lower()) in self.__TAB_NAMES:
			central_widget.setCurrentIndex(self.__TAB_NAMES.index(tab_name) + 1)
		else:
			central_widget.setCurrentIndex(0)
		self.setCentralWidget(central_widget)

	def __build_settings_tab (self) -> QWidget:
		settings_widget = QTabWidget()
		for tab in ('lcasettings', 'membership', 'organization', 'affiliates'):
			settings_widget.addTab( getattr(self, f'__build_settings_{tab}_tab')(), I18n(self).tabs.settings.tabs[tab].title )
		return settings_widget

	def __build_settings_lcasettings_tab (self) -> QWidget:
		return LCACSettingsLCAWidget()

	def __build_settings_membership_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.setSpacing(layout.spacing() * 2)
		if info_lbl := QLabel(I18n(self).tabs.settings.tabs.membership.info):
			info_lbl.setWordWrap(True)
		layout.addWidget(info_lbl)
		layout.addWidget(LCATabbedDataViewWidget(
			LCATableModel( Settings().MembershipTierModel, lambda : Settings().membership_tiers, Settings ),
			LCACSettingsMembershipTierWidget,
			I18n(self).tabs.settings.tabs.membership.typename,
			margin = 0,
			
		))
		return widget

	def __build_settings_organization_tab (self) -> QWidget:
		widget = QWidget()
		layout = QVBoxLayout(widget)
		layout.setSpacing(layout.spacing() * 2)
		layout.addWidget( LCATabbedDataViewWidget(
			LCATableModel( Settings().SeriesModel, lambda : Settings().series, Settings ),
			LCACSettingsOrganizationSeriesWidget,
			I18n(self).tabs.settings.tabs.organization.typename,
			margin = 0,
		) )
		return widget

	def __build_settings_affiliates_tab (self) -> QWidget:
		return LCACSettingsAffiliatesWidget()

