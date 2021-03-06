"""
Life
Copyright (C) 2020 MrRandom#9258

Life is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

Life is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with Life. If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import time
import typing

import aiohttp
import aredis
import asyncpg
import discord
from discord.ext import commands

from config import config
from utilities import context, help, objects, utils


class Life(commands.AutoShardedBot):

    def __init__(self, loop) -> None:
        super().__init__(command_prefix=self.get_prefix, reconnect=True, help_command=help.HelpCommand(), loop=loop,
                         activity=discord.Streaming(name=f'{config.Config(bot=self).prefix}help', url='https://www.twitch.tv/mrrandoooom'))

        self.text_permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True,
                                                    read_message_history=True, external_emojis=True, add_reactions=True)
        self.voice_permissions = discord.Permissions(connect=True, speak=True)

        self.log = logging.getLogger('bot')
        self.start_time = time.time()

        self.session = aiohttp.ClientSession(loop=self.loop)
        self.config = config.Config(bot=self)
        self.utils = utils.Utils(bot=self)

        self.commands_not_allowed_dms = {}

        self.guild_blacklist = {}
        self.default_guild_config = objects.DefaultGuildConfig()
        self.guild_configs = {}

        self.user_blacklist = {}
        self.default_user_config = objects.DefaultUserConfig()
        self.user_configs = {}

        self.time_format = '%A %d %B %Y at %H:%M'

        self.lavalink = None
        self.redis = None
        self.db = None

    def get_user_config(self, user: typing.Union[discord.User, discord.Member]) -> typing.Union[objects.DefaultUserConfig, objects.UserConfig]:
        return self.user_configs.get(user.id, self.default_user_config)

    def get_guild_config(self, guild: discord.Guild) -> typing.Union[objects.DefaultGuildConfig, objects.GuildConfig]:
        return self.guild_configs.get(guild.id, self.default_guild_config)

    async def get_context(self, message: discord.Message, *, cls=context.Context) -> context.Context:
        return await super().get_context(message, cls=cls)

    async def can_run_commands(self, ctx: context.Context) -> bool:

        if ctx.author.id in self.user_blacklist.keys() and ctx.command.name not in {'help', 'support'}:
            raise commands.CheckFailure(f'You are blacklisted from this bot for the following reason:\n\n`{self.user_blacklist[ctx.author.id]}`')

        if not ctx.guild and ctx.command.qualified_name in self.commands_not_allowed_dms:
            raise commands.NoPrivateMessage()

        needed_perms = {perm: value for perm, value in dict(self.text_permissions).items() if value is True}
        current_perms = dict(ctx.channel.permissions_for(ctx.guild.me)) if ctx.guild else dict(ctx.channel.me.permissions_in(ctx.channel))

        if ctx.command.cog and ctx.command.cog == self.get_cog('Music') and ctx.author.voice is not None:
            needed_perms.update({perm: value for perm, value in dict(self.voice_permissions).items() if value is True})
            current_perms.update({perm: value for perm, value in getattr(ctx.author.voice, 'channel', None).permissions_for(ctx.guild.me) if value is True})

        missing = [perm for perm, value in needed_perms.items() if current_perms[perm] != value]
        if missing:
            raise commands.BotMissingPermissions(missing)

        return True

    async def get_prefix(self, message: discord.Message) -> list:

        if not message.guild:
            return commands.when_mentioned_or(self.config.prefix, '')(self, message)

        guild_config = self.guild_configs.get(message.guild.id)
        if not guild_config:
            return commands.when_mentioned_or(self.config.prefix)(self, message)

        return commands.when_mentioned_or(self.config.prefix, *guild_config.prefixes)(self, message)

    async def is_owner(self, user: discord.User) -> bool:
        return user.id in self.config.owner_ids

    async def start(self, *args, **kwargs) -> None:

        try:
            db = await asyncpg.create_pool(**self.config.postgresql)
        except Exception as e:
            print(f'\n[POSTGRESQL] An error occurred while connecting to PostgreSQL: {e}')
        else:
            print(f'\n[POSTGRESQL] Connected to the PostgreSQL database.')
            self.db = db

        try:
            redis = aredis.StrictRedis(**self.config.redis)
        except aredis.ConnectionError:
            print(f'[REDIS] An error occurred while connecting to Redis.\n')
        else:
            print(f'[REDIS] Connected to Redis.\n')
            self.redis = redis

        for extension in self.config.extensions:
            try:
                self.load_extension(extension)
                print(f'[EXTENSIONS] Loaded - {extension}')
            except commands.ExtensionNotFound:
                print(f'[EXTENSIONS] Extension not found - {extension}')
            except commands.NoEntryPointError:
                print(f'[EXTENSIONS] No entry point - {extension}')
            except commands.ExtensionFailed as error:
                print(f'[EXTENSIONS] Failed - {extension} - Reason: {error}')

        self.commands_not_allowed_dms = {
            'join', 'play', 'leave', 'skip', 'pause', 'unpause', 'seek', 'volume', 'now_playing', 'queue', 'shuffle', 'clear', 'reverse', 'loop', 'remove', 'move',
            'musicinfo',

            'tag', 'tag raw', 'tag create', 'tag edit', 'tag claim', 'tag alias', 'tag transfer', 'prefix delete', 'tag search', 'tag list', 'tag all', 'tag info',
            'icon', 'server', 'channels', 'member'

            'prefix add', 'prefix delete', 'prefix clear', 'config colour set', 'config colour clear'
        }

        self.add_check(self.can_run_commands)

        await super().start(*args, **kwargs)

    async def close(self) -> None:

        print("\n[BOT] Closing bot down.")

        print("[DB] Closing database connection.")
        await self.db.close()

        print("[CS] Closing aiohttp client session.")
        await self.session.close()

        print("Bye bye!")
        await super().close()
