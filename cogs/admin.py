import discord
from discord.ext import commands
import os
from db import Database

class AdminCog(commands.Cog):
    """Administrative commands for bot configuration."""
    
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = os.environ.get("COMMAND_PREFIX", "!")
        # Get database instance from the main bot
        self.db = getattr(bot, 'db', None)
        if not self.db:
            database_file = os.environ.get("DATABASE_FILE", "bot_settings.db")
            self.db = Database(database_file)

    async def set_notification_channel(self, guild_id: int, channel_id: int):
        self.db.set_notification_channel(guild_id, channel_id)
        print(f"[{discord.utils.utcnow()}] Stored channel {channel_id} for guild {guild_id} in database.")

    async def get_notification_channel(self, guild_id: int) -> int | None:
        return self.db.get_notification_channel(guild_id)

    @commands.command(name="setchannel", help="Sets the channel for realm status notifications for this server. (Admin Only)")
    @commands.has_permissions(administrator=True)
    async def set_channel_command(self, ctx, channel: discord.TextChannel):
        """
        Sets the notification channel for this server.
        Usage: !setchannel #your-channel-name (or !setchannel <channel_id>)
        """
        try:
            guild_id = ctx.guild.id
            channel_id = channel.id
            await self.set_notification_channel(guild_id, channel_id)
            await ctx.send(f"Notification channel for this server has been set to {channel.mention}!")
            print(f"[{discord.utils.utcnow()}] Guild '{ctx.guild.name}' ({guild_id}): Notification channel set to {channel.name} ({channel_id}).")
        except Exception as e:
            await ctx.send(f"An error occurred while setting the channel: {e}")
            print(f"[{discord.utils.utcnow()}] Error setting channel in guild '{ctx.guild.name}': {e}")

    @set_channel_command.error
    async def set_channel_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify a channel. Usage: `{self.command_prefix}setchannel #your-channel` or `{self.command_prefix}setchannel <channel_id>`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid channel specified. Please ensure it's a valid text channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have the necessary permissions (Administrator) to use this command.")
        else:
            await ctx.send(f"An error occurred: {error}")
        print(f"[{discord.utils.utcnow()}] Error in {self.command_prefix}setchannel command: {error}")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
