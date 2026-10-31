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

from ....Assets import Assets
from ....Config import Config
from ....I18n import I18n
from ....Settings import Settings
from ....Util import Util

from ...LCAComboBox import LCAComboBox
from ...LCALabel import LCALabel
from ...LCAListCreatorWidget import LCAListCreatorWidget
from ...LCASeparator import LCASeparator
from ...LCATabbedDataViewPanelWidget import LCATabbedDataViewPanelWidget

class LCACSettingsMembershipTierWidget (LCATabbedDataViewPanelWidget):
	
	__remote_platform_cbos: dict[str, LCAComboBox]
	
	def _setup_layout (self) -> None:
		layout = QFormLayout(self)
		layout.setSpacing(layout.spacing() * 2)
		layout.addRow(LCALabel(I18n(self).remote_tiers.header))
		self.__remote_platform_cbos = {}
		for platform in ('youtube', 'twitch', 'patreon'):
			if cbo := LCAComboBox():
				cbo.currentDataChanged.connect( lambda data, platform = platform : self.__evt_remote_tier_changed(data, platform) )
				self._mapper.addMapping(cbo, self.model.get_column_index(f'remote_ids.{platform}'))
				self.__remote_platform_cbos[platform] = cbo
			layout.addRow(getattr(I18n(self).remote_tiers, platform), cbo)
		Settings().signals().changed.connect( self.__rebuild_remote_tier_cbos )
		self.__rebuild_remote_tier_cbos()
		layout.addRow(LCASeparator.horizontal())
		layout.addRow(LCALabel(I18n(self).associated_discord_role))
		if associated_discord_role_input := QLineEdit():
			self._mapper.addMapping(associated_discord_role_input, self.model.get_column_index('discord_managed_role_name'))
		layout.addRow(associated_discord_role_input)
		layout.addRow(LCALabel(I18n(self).other_discord_roles))
		if other_discord_roles := LCAListCreatorWidget():
			self._mapper.addMapping(other_discord_roles, self.model.get_column_index('discord_remote_role_names'))
			other_discord_roles.set_value(self.model.data((self._model_row, 'discord_remote_role_names')))
			other_discord_roles.changed.connect(self._mapper.submit)
		layout.addRow(other_discord_roles)
		self._finalize_mapper()

	def __rebuild_remote_tier_cbos (self) -> None:
		for platform, cbo in self.__remote_platform_cbos.items():
			cbo.clear()
			cbo.addItem(I18n(self).remote_tiers.no_analogous_tier, None)
			for tier in getattr(Settings().integrations, platform).remote_membership_tiers:
				cbo.addItem(tier.remote_name, tier.remote_id)
			try:
				cbo.setCurrentIndex(cbo.findData(self.model.data([self._model_row, f'remote_ids.{platform}'])))
			except IndexError:
				pass # Tab was just deleted

	def __evt_remote_tier_changed (self, remote_id: str, platform_name: str) -> None:
		pass # logger.debug(f'{remote_id} {platform_name}')

