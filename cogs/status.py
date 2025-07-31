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
        status_message = "Checking realm status..."
        message = await ctx.send(status_message)
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
                response_text = "Could not retrieve realm status at this time. The API might be down."
        else:
            response_text = "Could not retrieve realm status at this time. The API might be down."
            
        await message.edit(content=response_text)
        print(f"[{discord.utils.utcnow()}] Manual status check requested by {ctx.author.name} in guild '{ctx.guild.name}': {response_text}")

async def setup(bot):
    await bot.add_cog(StatusCog(bot))
