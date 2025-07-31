import discord
from discord.ext import commands
import os
from db import Database

class NotificationsCog(commands.Cog):
    """Notification opt-in/opt-out functionality and reaction handling."""
    
    def __init__(self, bot):
        self.bot = bot
        # Get database instance from the main bot
        self.db = getattr(bot, 'db', None)
        if not self.db:
            database_file = os.environ.get("DATABASE_FILE", "bot_settings.db")
            self.db = Database(database_file)

    async def add_optin_user(self, guild_id: int, user_id: int):
        # Try to get username from bot if possible
        user_name = None
        guild = self.bot.get_guild(guild_id)
        member = None
        if guild:
            member = guild.get_member(user_id)
            if not member:
                try:
                    member = await guild.fetch_member(user_id)
                except Exception:
                    member = None
            if member:
                user_name = member.name
        self.db.add_optin_user(guild_id, user_id, user_name)

    async def remove_optin_user(self, guild_id: int, user_id: int):
        self.db.remove_optin_user(guild_id, user_id)

    async def get_optin_users(self, guild_id: int):
        return self.db.get_optin_users(guild_id)

    @commands.command(name="notifyme", help="React to the posted message to opt-in/out of Kezan notifications.")
    async def notifyme_command(self, ctx):
        """
        Posts a message users can react to in order to opt-in/out of Kezan notifications.
        Usage: !notifyme
        """
        msg = await ctx.send(
            "React with 🔔 to this message to receive Kezan online notifications! Remove your reaction to opt out."
        )
        await msg.add_reaction("🔔")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "🔔" and not payload.member.bot:
            guild_id = payload.guild_id
            user_id = payload.user_id
            await self.add_optin_user(guild_id, user_id)
            # Logging
            guild = self.bot.get_guild(guild_id)
            user = payload.member
            if guild and user:
                print(f"[notifyme] Added user {user.name} ({user_id}) to opt-in list for guild '{guild.name}' ({guild_id})")
            else:
                print(f"[notifyme] Added user ID {user_id} to opt-in list for guild ID {guild_id}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.emoji.name == "🔔":
            guild_id = payload.guild_id
            user_id = payload.user_id
            await self.remove_optin_user(guild_id, user_id)
            # Logging
            guild = self.bot.get_guild(guild_id)
            user = None
            if guild:
                user = guild.get_member(user_id)
            if guild and user:
                print(f"[notifyme] Removed user {user.name} ({user_id}) from opt-in list for guild '{guild.name}' ({guild_id})")
            else:
                print(f"[notifyme] Removed user ID {user_id} from opt-in list for guild ID {guild_id}")

def setup(bot):
    bot.add_cog(NotificationsCog(bot))
