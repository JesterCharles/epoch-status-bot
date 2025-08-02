import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone
from server_status import poll_servers

class StatusCog(commands.Cog):
    """Status checking functionality for Project Epoch realm."""
    
    def __init__(self, bot):
        self.bot = bot

    async def fetch_realm_status_data(self):
        """
        Checks the realm status via direct server connections and returns status data.
        """
        try:
            server_data = await poll_servers()
            if not server_data:
                return None
            
            # Build status data similar to the old API format
            auth_status = server_data.get("Auth", {}).get("online", False)
            kezan_status = server_data.get("Kezan", {}).get("online", False)
            gurubashi_status = server_data.get("Gurubashi", {}).get("online", False)
            
            return {
                "authServerStatus": auth_status,
                "realms": [
                    {"name": "Kezan", "worldServerOnline": kezan_status},
                    {"name": "Gurubashi", "worldServerOnline": gurubashi_status}
                ]
            }
        except Exception as e:
            print(f"[{discord.utils.utcnow()}] Error in fetch_realm_status_data: {e}")
            return None

    @commands.command(name="status", help="Checks the current Project Epoch realm status.")
    async def status_command(self, ctx):
        """
        A command that checks the current realm status and reports it to the channel where it was invoked.
        Usage: !status
        """
        # Create initial embed
        embed = discord.Embed(
            title="🔍 Project Epoch Server Status",
            description="Checking server status...",
            color=0xffff00  # Yellow while checking
        )
        message = await ctx.send(embed=embed)
        
        data = await self.fetch_realm_status_data()
        
        if data and isinstance(data, dict):
            auth_status = data.get("authServerStatus", False)
            realms = data.get("realms", [])
            kezan = next((realm for realm in realms if realm.get("name") == "Kezan"), None)
            kezan_online = kezan.get("worldServerOnline", False) if kezan else False
            gurubashi = next((realm for realm in realms if realm.get("name") == "Gurubashi"), None)
            gurubashi_online = gurubashi.get("worldServerOnline", False) if gurubashi else False
            
            # Determine overall status and color
            if auth_status and (kezan_online or gurubashi_online):
                overall_status = "ONLINE"
                status_emoji = "✅"
                embed_color = 0x00ff00  # Green
            elif auth_status:
                overall_status = "AUTH ONLY"
                status_emoji = "⚠️"
                embed_color = 0xffa500  # Orange
            else:
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
                text="Status checked via direct server connection",
                icon_url="https://cdn.discordapp.com/emojis/852558866151800832.png"  # Optional: server icon
            )
            
        else:
            # Error embed
            embed = discord.Embed(
                title="🔍 Project Epoch Server Status",
                description="❌ **Connection Failed**",
                color=0xff0000
            )
            embed.add_field(
                name="⚠️ Error",
                value="Could not retrieve server status. Server connections failed.",
                inline=False
            )
            embed.set_footer(text="Please try again in a moment")
            
        await message.edit(embed=embed)
        
        # Log the status check with clean logic
        if data:
            auth_log = "ON" if data.get('authServerStatus') else "OFF"
            kezan_log = "ON" if kezan_online else "OFF"
            gurubashi_log = "ON" if gurubashi_online else "OFF"
            status_summary = f"Auth: {auth_log}, Kezan: {kezan_log}, Gurubashi: {gurubashi_log}"
        else:
            status_summary = "CONNECTION_FAILED"
            
        print(f"[{discord.utils.utcnow()}] Manual status check requested by {ctx.author.name} in guild '{ctx.guild.name}': {status_summary}")

async def setup(bot):
    await bot.add_cog(StatusCog(bot))
