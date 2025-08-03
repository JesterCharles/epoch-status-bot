import discord
from discord.ext import commands
import requests
import json
import os

class StatusCog(commands.Cog):
    """Status checking functionality for Project Epoch realm."""
    
    def __init__(self, bot):
        self.bot = bot
        self.api_url = os.environ.get("API_URL", "https://project-epoch-status.com/api/status/realms")

    async def fetch_realm_status_data(self):
        """
        Fetches the realm status from the API and returns the status string or None on error.
        """
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()
            return data  # Return the full JSON
        except requests.exceptions.RequestException as e:
            print(f"[{discord.utils.utcnow()}] API Request Error in fetch_realm_status_data: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[{discord.utils.utcnow()}] JSON Decode Error in fetch_realm_status_data: Could not parse API response. {e}")
            return None
        except Exception as e:
            print(f"[{discord.utils.utcnow()}] An unexpected error occurred in fetch_realm_status_data: {e}")
            return None

    @commands.command(name="status", help="Checks the current Project Epoch realm status.")
    async def status_command(self, ctx):
        """
        A command that checks the current realm status and reports it to the channel where it was invoked.
        Usage: !status
        """
<<<<<<< Updated upstream
        status_message = "Checking realm status..."
        message = await ctx.send(status_message)
=======
        # Check if bot has basic permissions
        perms = ctx.channel.permissions_for(ctx.guild.me)
        if not perms.send_messages:
            return  # Can't do anything if we can't send messages
        
        if not perms.embed_links:
            try:
                await ctx.send("❌ I need 'Embed Links' permission to show server status properly.")
                return
            except discord.Forbidden:
                return
        
        try:
            # Create initial embed
            embed = discord.Embed(
                title="🔍 Project Epoch Server Status",
                description="Checking server status...",
                color=0xffff00  # Yellow while checking
            )
            message = await ctx.send(embed=embed)
        except discord.Forbidden:
            try:
                await ctx.send("❌ Missing permissions to send embeds. Please check bot permissions.")
            except discord.Forbidden:
                pass  # Can't even send basic messages
            return
        
>>>>>>> Stashed changes
        data = await self.fetch_realm_status_data()
        
        if data and isinstance(data, dict):
            status = data.get("status")
            auth_status = data.get("authServerStatus", False)
            realms = data.get("realms", [])
            kezan = next((realm for realm in realms if realm.get("name") == "Kezan"), None)
            kezan_online = kezan.get("worldServerOnline", False) if kezan else False
            
            if status:
                response_text = (
                    f"The Project Epoch realm is currently **{status.upper()}**.\n"
                    f"Auth server: {'ONLINE' if auth_status else 'OFFLINE'}\n"
                    f"Kezan world server: {'ONLINE' if kezan_online else 'OFFLINE'}"
                )
            else:
<<<<<<< Updated upstream
                response_text = "Could not retrieve realm status at this time. The API might be down."
=======
                overall_status = "OFFLINE"
                status_emoji = "❌"
                embed_color = 0xff0000  # Red
            
            # Create status embed
            embed = discord.Embed(
                title="🔍 Project Epoch Server Status",
                description=f"{status_emoji} **Status: {overall_status}**",
                color=embed_color,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Auth server status
            auth_emoji = "🟢" if auth_status else "🔴"
            embed.add_field(
                name="🔐 Authentication Server",
                value=f"{auth_emoji} {'ONLINE' if auth_status else 'OFFLINE'}",
                inline=True
            )
            
            # Kezan server status
            kezan_emoji = "🟢" if kezan_online else "🔴"
            embed.add_field(
                name="🌍 Kezan World Server",
                value=f"{kezan_emoji} {'ONLINE' if kezan_online else 'OFFLINE'}",
                inline=True
            )
            
            # Gurubashi server status
            gurubashi_emoji = "🟢" if gurubashi_online else "🔴"
            embed.add_field(
                name="🏝️ Gurubashi World Server",
                value=f"{gurubashi_emoji} {'ONLINE' if gurubashi_online else 'OFFLINE'}",
                inline=True
            )
            
            # Add footer
            embed.set_footer(
                text="Status checked via direct connection (API backup available)",
                icon_url="https://cdn.discordapp.com/emojis/852558866151800832.png"  # Optional: server icon
            )
            
>>>>>>> Stashed changes
        else:
            response_text = "Could not retrieve realm status at this time. The API might be down."
            
<<<<<<< Updated upstream
        await message.edit(content=response_text)
        print(f"[{discord.utils.utcnow()}] Manual status check requested by {ctx.author.name} in guild '{ctx.guild.name}': {response_text}")
=======
        try:
            await message.edit(embed=embed)
        except discord.Forbidden:
            try:
                await ctx.send("❌ Lost permissions while updating status. Please check bot permissions.")
            except discord.Forbidden:
                pass  # Can't send any messages
        
        # Log the status check with clean logic
        if data:
            auth_log = "ON" if data.get('authServerStatus') else "OFF"
            kezan_log = "ON" if kezan_online else "OFF"
            gurubashi_log = "ON" if gurubashi_online else "OFF"
            status_summary = f"Auth: {auth_log}, Kezan: {kezan_log}, Gurubashi: {gurubashi_log}"
        else:
            status_summary = "CONNECTION_FAILED"
            
        print(f"[{discord.utils.utcnow()}] Manual status check requested by {ctx.author.name} in guild '{ctx.guild.name}': {status_summary}")
>>>>>>> Stashed changes

async def setup(bot):
    await bot.add_cog(StatusCog(bot))
