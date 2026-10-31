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

import time

from loguru import logger
import discord
import discord.ext.tasks

from ...Settings import Settings

from ..LCATaskThread import LCATaskThread

class LCADDiscordBotTaskThread (LCATaskThread):

	class _DiscordBot (discord.Client):

		async def on_ready (self) -> None:
			logger.info(f'Discord bot logged in as {self.user}')
			self.assign_roles.start()

		@discord.ext.tasks.loop(seconds = 5.0)
		async def assign_roles (self) -> None:
			if len(self.guilds) != 1:
				logger.warning(f'Discord bot enabled on {len(self.guilds)} servers (needs exactly one)')
				return
			if not len(Settings().membership_tiers):
				logger.info('No membership tiers to manage')
				return
			tier_roles = [
				discord.utils.get(self.guilds[0].roles, name = tier.discord_managed_role_name)
				for tier in Settings().membership_tiers
			]
			for member in self.guilds[0].members:
				member_tier_index = self.__get_user_tier_index(member)
				await self.__assign_roles_to_member(member, tier_roles[:member_tier_index])
				await self.__unassign_roles_from_member(member, tier_roles[member_tier_index:])

		def __get_user_tier_index (self, member: discord.Member) -> int:
			ret = 0
			for i, tier in enumerate(Settings().membership_tiers):
				for role in member.roles:
					if role.name in tier.discord_remote_role_names:
						ret = max(ret, i + 1)
			return ret

		async def __assign_roles_to_member (self, member: discord.Member, roles: list[discord.Role]) -> None:
			if roles_to_assign := (set(roles) - set(member.roles)):
				logger.info(f'Add roles to {member}: {roles_to_assign}')
				await member.add_roles(*list(roles_to_assign))

		async def __unassign_roles_from_member (self, member: discord.Member, roles: list[discord.Role]) -> None:
			if roles_to_unassign := set(member.roles).intersection(set(roles)):
				logger.info(f'Remove roles from {member}: {roles_to_unassign}')
				await member.remove_roles(*list(roles_to_unassign))

	def _run (self) -> None:
		intents = discord.Intents.default()
		intents.members = True
		while True:
			try:
				self._DiscordBot(intents = intents).run(Settings().integrations.discord.token)
				break
			except discord.errors.LoginFailure:
				logger.warning('Discord refused login, trying again in 5 seconds...')
				time.sleep(5)

