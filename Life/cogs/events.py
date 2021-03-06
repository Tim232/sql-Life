"""
Life
Copyright (C) 2020 MrRandom#9258

Life is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

Life is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with Life. If not, see <https://www.gnu.org/licenses/>.
"""

import collections
from datetime import datetime

import discord
import prettify_exceptions
from discord.ext import commands

from utilities import context, exceptions
from cogs.voice.lavalink.exceptions import NodeNotFound


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.socket_stats = collections.Counter()

        self.bot.mention_channel = None
        self.bot.error_channel = None
        self.bot.log_channel = None
        self.bot.dm_channel = None

    @commands.Cog.listener()
    async def on_ready(self):

        print(f'\n[BOT] The bot is now ready. Name: {self.bot.user} | ID: {self.bot.user.id}\n')
        self.bot.log.info(f'Bot is now ready. Name: {self.bot.user} | ID: {self.bot.user.id}')

        self.bot.mention_channel = self.bot.get_channel(714601090771058719)
        self.bot.error_channel = self.bot.get_channel(728000870230523906)
        self.bot.log_channel = self.bot.get_channel(697324016658022441)
        self.bot.dm_channel = self.bot.get_channel(714307639609131018)

        for guild in self.bot.guilds:
            if guild.id in self.bot.guild_blacklist:
                await guild.leave()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):

        if self.bot.log_channel:

            embed = discord.Embed(colour=discord.Colour.gold())
            embed.set_thumbnail(url=str(guild.icon_url_as(format='gif' if guild.is_icon_animated() is True else 'png')))
            embed.title = f'Joined a guild'
            time = datetime.strftime(guild.me.joined_at, "%A %d %B %Y at %H:%M:%S")
            embed.description = f'`Name:` {guild.name}\n`ID:` {guild.id}\n`Owner:` {guild.owner}\n`Time:` {time}'
            await self.bot.log_channel.send(embed=embed)

        self.bot.log.info(f'Joined a guild. Name: {guild.name} | ID: {guild.id} | Owner: {guild.owner}')

        if guild.id in self.bot.guild_blacklist.keys():
            await guild.leave()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):

        if self.bot.log_channel:

            embed = discord.Embed(colour=discord.Colour.gold())
            embed.set_thumbnail(url=str(guild.icon_url_as(format='gif' if guild.is_icon_animated() is True else 'png')))
            embed.title = f'Left a {"blacklisted " if guild.id in self.bot.guild_blacklist.keys() else ""}guild'
            embed.description = f'`Name:` {guild.name}\n`ID:` {guild.id}\n`Owner:` {guild.owner}'
            await self.bot.log_channel.send(embed=embed)

        self.bot.log.info(f'Left a guild. Name: {guild.name} | ID: {guild.id} | Owner: {guild.owner}')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.id == self.bot.user.id:
            return

        if not self.bot.mention_channel or not self.bot.dm_channel:
            return

        ctx = await self.bot.get_context(message)

        if message.guild is None:

            time = datetime.strftime(ctx.message.created_at, "%A %d %B %Y at %H:%M:%S")
            info = f'`Channel:` {ctx.channel}\n`Channel ID:` {ctx.channel.id}\n`Time`: {time}'

            embed = discord.Embed(colour=ctx.colour)
            embed.set_author(name=f'DM from {ctx.author}',
                             icon_url=str(ctx.author.avatar_url_as(format='gif' if ctx.author.is_avatar_animated() is True else 'png')))
            embed.description = f'{message.content}'
            embed.add_field(name='Info:', value=info)
            await self.bot.dm_channel.send(embed=embed)

        if self.bot.user in message.mentions:

            guild = f'`Guild:` {ctx.guild}\n' if ctx.guild else ''
            guild_id = f'`Guild ID:` {ctx.guild.id}\n' if ctx.guild else ''
            time = datetime.strftime(ctx.message.created_at, "%A %d %B %Y at %H:%M:%S")
            info = f'{guild}{guild_id}`Channel:` {ctx.channel}\n`Channel ID:` {ctx.channel.id}\n`Time`: {time}'

            embed = discord.Embed(colour=ctx.colour)
            embed.set_author(name=f'Mentioned by {ctx.author}',
                             icon_url=str(ctx.author.avatar_url_as(format='gif' if ctx.author.is_avatar_animated() is True else 'png')))
            embed.description = f'{message.content}'
            embed.add_field(name='Info:', value=info)
            await self.bot.mention_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):

        if before.author.bot:
            return

        if before.content == after.content:
            return

        await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: context.Context, error):

        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            return  # Ignore this exception

        elif isinstance(error, commands.CommandOnCooldown):

            if ctx.author.id in self.bot.owner_ids:
                ctx.command.reset_cooldown(ctx)
                return await ctx.command.reinvoke(ctx)

            cooldowns = {
                commands.BucketType.default: f'for the whole bot.',
                commands.BucketType.user: f'for you.',
                commands.BucketType.guild: f'for this server.',
                commands.BucketType.channel: f'for this channel.',
                commands.BucketType.member: f'cooldown for you.',
                commands.BucketType.category: f'for this channel category.',
                commands.BucketType.role: f'for your role.'
            }
            return await ctx.send(f'The command `{ctx.command}` is on cooldown {cooldowns[error.cooldown.type]} '
                                  f'You can retry in `{self.bot.utils.format_time(error.retry_after, friendly=True)}`')

        elif isinstance(error, commands.MaxConcurrencyReached):
            cooldowns = {
                commands.BucketType.default: f'.',
                commands.BucketType.user: f' per user.',
                commands.BucketType.guild: f' per server.',
                commands.BucketType.channel: f' per channel.',
                commands.BucketType.member: f' per member.',
                commands.BucketType.category: f' per channel category.',
                commands.BucketType.role: f' per role.'
            }
            return await ctx.send(f'The command `{ctx.command}` is already being ran at its maximum of '
                                  f'{error.number} time(s){cooldowns[error.per]} Retry a bit later.')

        ctx.command.reset_cooldown(ctx)

        if isinstance(error, commands.BotMissingPermissions):
            permissions = '\n'.join([f'> {permission}' for permission in error.missing_perms])
            message = f'I am missing the following permissions required to run the command `{ctx.command}`.\n{permissions}'
            try:
                return await ctx.send(message)
            except discord.Forbidden:
                try:
                    return await ctx.author.send(message)
                except discord.Forbidden:
                    return

        elif isinstance(error, commands.MissingPermissions):
            permissions = '\n'.join([f'> {permission}' for permission in error.missing_perms])
            return await ctx.send(f'You are missing the following permissions required to run the command `{ctx.command}`.\n{permissions}')

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f'You missed the `{error.param.name}` parameter for the command `{ctx.command}`. '
                                  f'Use `{self.bot.config.prefix}help {ctx.command}` for more information on what parameters to use.')

        error_messages = {

            exceptions.ArgumentError: f'{error}',
            exceptions.ImageError: f'{error}',
            exceptions.VoiceError: f'{error}',
            commands.CheckFailure: f'{error}',
            NodeNotFound: f'There are no lavalink nodes available right now.',
            commands.TooManyArguments: f'You used too many parameters for the command `{ctx.command}`. Use `{self.bot.config.prefix}help {ctx.command}` for '
                                       f'more information on what parameters to use.',
            commands.BadArgument: f'I was unable to understand a parameter that you used for the command `{ctx.command}`. '
                                  f'Use `{self.bot.config.prefix}help {ctx.command}` for more information on what parameters to use.',
            commands.BadUnionArgument: f'I was unable to understand a parameter that you used for the command `{ctx.command}`. '
                                       f'Use `{self.bot.config.prefix}help {ctx.command}` for more information on what parameters to use.',
            commands.NoPrivateMessage: f'The command `{ctx.command}` can not be used in private messages.',
            commands.NotOwner: f'The command `{ctx.command}` is owner only.',
            commands.NSFWChannelRequired: f'The command `{ctx.command}` can only be ran in a NSFW channel.',
            commands.DisabledCommand: f'The command `{ctx.command}` has been disabled.',
            commands.ExpectedClosingQuoteError: f'You missed a closing quote in the parameters passed to the `{ctx.command}` command.',
            commands.UnexpectedQuoteError: f'There was an unexpected quote in the parameters passed to the `{ctx.command}` command.'
        }

        error_message = error_messages.get(type(error), None)
        if error_message is not None:
            return await ctx.send(error_message)

        await ctx.send(f'Something went wrong while executing that command. Please use `{self.bot.config.prefix}support` for more help or information.')

        formatter = prettify_exceptions.DefaultFormatter()

        formatter.theme['_ansi_enabled'] = True
        print(f'\n{"".join(formatter.format_exception(type(error), error, error.__traceback__)).strip()}')

        if not self.bot.error_channel:
            return

        guild = f'`Guild:` {ctx.guild} ({ctx.guild.id})' if ctx.guild else ''
        channel = f'`Channel:` {ctx.channel} ({ctx.channel.id})'
        author = f'`Author:` {ctx.author} ({ctx.author.id})'
        time = f'`Time:` {datetime.strftime(ctx.message.created_at, "%A %d %B %Y at %H:%M:%S")}'
        info = f'`Message content:` {ctx.message.content}\n{guild}\n{channel}\n{author}\n{time}'

        embed = discord.Embed(colour=ctx.colour, description=f'Error in command `{ctx.command}`')
        embed.set_author(name=ctx.author, icon_url=str(ctx.author.avatar_url_as(format='gif' if ctx.author.is_avatar_animated() is True else 'png')))
        embed.add_field(name='Info:', value=info)
        await self.bot.error_channel.send(embed=embed)

        formatter.theme['_ansi_enabled'] = False
        traceback = "".join(formatter.format_exception(type(error), error, error.__traceback__)).strip()

        if len(traceback) < 2000:
            return await self.bot.error_channel.send(f'```{traceback}```')

        [await self.bot.error_channel.send(f'```{msg}```') for msg in [traceback[i:i+1900] for i in range(0, len(traceback), 1900)]]

    @commands.Cog.listener()
    async def on_socket_response(self, message: dict):

        event = message.get('t', 'None')
        if event is not None:
            self.bot.socket_stats[event] += 1


def setup(bot):
    bot.add_cog(Events(bot))
