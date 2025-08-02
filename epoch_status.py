import os
from dotenv import load_dotenv
import discord
import asyncio
from datetime import datetime, timezone
from db import Database
from server_status import poll_servers, SERVERS

# Load environment variables from .env if present
load_dotenv()
# Optional: DATABASE_FILE
DATABASE_FILE = os.environ.get("DATABASE_FILE", "bot_settings.db")

# --- Database Instance ---
db = Database(DATABASE_FILE)
from discord.ext import tasks, commands


# --- Configuration (from environment variables) ---
# Required: DISCORD_BOT_TOKEN
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable is required.")

# Optional: CHECK_INTERVAL_SECONDS
try:
    CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "15"))
except ValueError: # double check if it's a valid integer
    CHECK_INTERVAL_SECONDS = 15

# Optional: COMMAND_PREFIX
COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX", "!")

# --- Discord Bot Setup ---

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Store database instance on bot for cogs to access
bot.db = db

# Async setup hook for loading cogs
async def setup_hook():
    """Load all cogs when the bot starts up."""
    cogs_to_load = [
        'cogs.status',
        'cogs.admin', 
        'cogs.notifications',
        'cogs.gambling',
        'cogs.gitcheck',
        'cogs.clanker'
    ]
    
    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            print(f"Loaded {cog} successfully")
        except Exception as e:
            print(f"Failed to load {cog}: {e}")

# Set the setup hook
bot.setup_hook = setup_hook

# Helper functions for background task - keep these in main file since they're used by the background loop
async def get_notification_channel(guild_id: int) -> int | None:
    return db.get_notification_channel(guild_id)

async def get_optin_users(guild_id: int):
    return db.get_optin_users(guild_id)

# --- Background Task for Status Checking ---
@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_realm_status():
    """
    Periodically polls server status and sends Discord notifications
    to all configured channels when status changes.
    """
    
    # Poll servers for current status
    try:
        server_data = await poll_servers()
    except Exception as e:
        print(f"[{discord.utils.utcnow()}] Server polling failed: {e}")
        return
    
    if not server_data:
        print(f"[{discord.utils.utcnow()}] Server polling returned empty data, skipping notification check.")
        return

    # Get server status from polling results
    auth_server_status = server_data.get("Auth", {}).get("online", False)
    kezan_online = server_data.get("Kezan", {}).get("online", False)

    # Track last known status for both auth and Kezan world server per guild
    if not hasattr(check_realm_status, "last_status"):
        check_realm_status.last_status = {}

    for guild in bot.guilds:
        guild_id = guild.id
        configured_channel_id = await get_notification_channel(guild_id)
        if configured_channel_id is None:
            print(f"[{discord.utils.utcnow()}] No notification channel set for guild '{guild.name}' (ID: {guild_id}). Skipping.")
            continue
        channel = bot.get_channel(configured_channel_id)
        if not channel:
            print(f"[{discord.utils.utcnow()}] Configured channel with ID {configured_channel_id} not found in guild '{guild.name}'. Skipping.")
            continue

        # Initialize last status for this guild
        if guild_id not in check_realm_status.last_status:
            check_realm_status.last_status[guild_id] = {
                "auth": False,
                "kezan": False
            }
        prev_auth = check_realm_status.last_status[guild_id]["auth"]
        prev_kezan = check_realm_status.last_status[guild_id]["kezan"]

        # Auth server notification (non-@everyone)
        if auth_server_status and not prev_auth:
            try:
                msg = await channel.send("The Project Epoch auth server is now **ONLINE**! You may be able to log in soon.")
                # Add :bait: reaction for the guild 'High Tempo' (EPOCH)
                if guild.name == "High Tempo" or guild.name.startswith("High Tempo"):
                    # Try to find a custom emoji named 'bait' in the guild
                    bait_emoji = discord.utils.get(guild.emojis, name="bait")
                    try:
                        if bait_emoji:
                            await msg.add_reaction(bait_emoji)
                        else:
                            await msg.add_reaction(":bait:") # fallback, may error if not a unicode emoji
                    except Exception as e:
                        print(f"[notifyme] Could not add :bait: reaction: {e}")
                print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Auth server online message sent to channel {channel.name}.")
            except Exception as e:
                print(f"[{discord.utils.utcnow()}] Error sending auth server message to guild '{guild.name}' ({guild_id}): {e}")

        # Kezan world server notification (opt-in users) only if both auth and Kezan are up
        if auth_server_status and kezan_online and not prev_kezan:
            try:
                optin_users = await get_optin_users(guild_id)
                if optin_users:
                    mentions = ' '.join(f'<@{uid}>' for uid, _ in optin_users)
                    await channel.send(
                        f"{mentions} The Project Epoch realm **Kezan** is now **ONLINE**! Go Go Go!"
                    )
                    print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Kezan is online. Sent opt-in user pings to channel {channel.name}. Opt-ins: {[uname for _, uname in optin_users]}")
                else:
                    await channel.send(
                        "The Project Epoch realm **Kezan** is now **ONLINE**! (No users have opted in for notifications.)"
                    )
                    print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Kezan is online. No opt-in users to ping in channel {channel.name}.")
            except discord.Forbidden:
                print(f"[{discord.utils.utcnow()}] Error: Bot does not have permissions to send messages in channel '{channel.name}' ({configured_channel_id}) in guild '{guild.name}' ({guild_id}).")
            except Exception as e:
                print(f"[{discord.utils.utcnow()}] Error sending Kezan message to guild '{guild.name}' ({guild_id}): {e}")

        # Update last known status
        check_realm_status.last_status[guild_id]["auth"] = auth_server_status
        check_realm_status.last_status[guild_id]["kezan"] = kezan_online

        # Log status if nothing changed
        if (auth_server_status == prev_auth) and (kezan_online == prev_kezan):
            print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Auth server is {'ONLINE' if auth_server_status else 'OFFLINE'}, Kezan is {'ONLINE' if kezan_online else 'OFFLINE'} (no change).")


# --- Discord Event Handlers ---
@bot.event
async def on_ready():
    """
    Called when the bot successfully connects to Discord.
    Initializes the database and starts background tasks.
    """
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    
    # Database is initialized on db instance creation
    # Start the status checking task
    if not check_realm_status.is_running():
        print(f"Starting realm status check loop (every {CHECK_INTERVAL_SECONDS}s)...")
        check_realm_status.start()

# --- Run the Bot ---
if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("ERROR: Please replace 'YOUR_DISCORD_BOT_TOKEN_HERE' with your actual bot token.")
        print("Refer to the instructions on how to get your token.")
    else:
        try:
            bot.run(DISCORD_BOT_TOKEN)
        except discord.errors.LoginFailure:
            print("ERROR: Failed to log in. Check your bot token. It might be invalid or expired.")
        except Exception as e:
            print(f"An error occurred while running the bot: {e}")
