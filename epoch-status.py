import os
from dotenv import load_dotenv
import discord
import requests
import asyncio
import json
from db import Database

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

# Optional: API_URL
API_URL = os.environ.get("API_URL", "https://project-epoch-status.com/api/status/realms")

# Optional: CHECK_INTERVAL_SECONDS
try:
    CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "10"))
except ValueError: # double check if it's a valid integer
    CHECK_INTERVAL_SECONDS = 10

# Optional: COMMAND_PREFIX
COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX", "!")

# Optional: DATABASE_FILE
DATABASE_FILE = os.environ.get("DATABASE_FILE", "bot_settings.db")

# --- Global State Tracking ---
# This dictionary will store the last known status for each guild (server ID -> True/False)
# to prevent spamming notifications for repeated online/offline states.
last_known_guild_status = {}

# --- Discord Bot Setup ---

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


# --- Database Initialization is handled by the Database class ---

async def add_optin_user(guild_id: int, user_id: int):
    # Try to get username from bot if possible
    user_name = None
    guild = bot.get_guild(guild_id)
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
    db.add_optin_user(guild_id, user_id, user_name)

async def remove_optin_user(guild_id: int, user_id: int):
    db.remove_optin_user(guild_id, user_id)

async def get_optin_users(guild_id: int):
    return db.get_optin_users(guild_id)


# --- Command to Post Opt-in Notification Message ---
@bot.command(name="notifyme", help="React to the posted message to opt-in/out of Kezan notifications.")
async def notifyme_command(ctx):
    """
    Posts a message users can react to in order to opt-in/out of Kezan notifications.
    Usage: !notifyme
    """
    msg = await ctx.send(
        "React with 🔔 to this message to receive Kezan online notifications! Remove your reaction to opt out."
    )
    await msg.add_reaction("🔔")


# --- Reaction Event Handlers for Opt-in ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name == "🔔" and not payload.member.bot:
        guild_id = payload.guild_id
        user_id = payload.user_id
        await add_optin_user(guild_id, user_id)
        # Logging
        guild = bot.get_guild(guild_id)
        user = payload.member
        if guild and user:
            print(f"[notifyme] Added user {user.name} ({user_id}) to opt-in list for guild '{guild.name}' ({guild_id})")
        else:
            print(f"[notifyme] Added user ID {user_id} to opt-in list for guild ID {guild_id}")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name == "🔔":
        guild_id = payload.guild_id
        user_id = payload.user_id
        await remove_optin_user(guild_id, user_id)
        # Logging
        guild = bot.get_guild(guild_id)
        user = None
        if guild:
            user = guild.get_member(user_id)
        if guild and user:
            print(f"[notifyme] Removed user {user.name} ({user_id}) from opt-in list for guild '{guild.name}' ({guild_id})")
        else:
            print(f"[notifyme] Removed user ID {user_id} from opt-in list for guild ID {guild_id}")


# --- Notification Channel Management (using db.py) ---
async def set_notification_channel(guild_id: int, channel_id: int):
    db.set_notification_channel(guild_id, channel_id)
    print(f"[{discord.utils.utcnow()}] Stored channel {channel_id} for guild {guild_id} in database.")

async def get_notification_channel(guild_id: int) -> int | None:
    return db.get_notification_channel(guild_id)


# --- Helper Function for API Call ---
async def fetch_realm_status_data():
    """
    Fetches the realm status from the API and returns the status string or None on error.
    """
    try:
        response = requests.get(API_URL)
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


# --- Background Task for Status Checking ---
@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_realm_status():
    """
    Periodically checks the realm status API and sends a Discord notification
    to all configured channels if the realm status changes.
    """

    data = await fetch_realm_status_data()
    if data is None:
        print(f"[{discord.utils.utcnow()}] API status is unknown, skipping realm check for now.")
        return

    auth_server_status = data.get("authServerStatus", False)
    realms = data.get("realms", [])
    kezan = next((realm for realm in realms if realm.get("name") == "Kezan"), None)
    kezan_online = kezan.get("worldServerOnline", False) if kezan else False

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
    # Make sure the bot is ready before starting the loop
    if not check_realm_status.is_running():
        print("Starting realm status check loop...")
        check_realm_status.start()

# --- Command to Check Status ---
@bot.command(name="status", help="Checks the current Project Epoch realm status.")
async def status_command(ctx):
    """
    A command that checks the current realm status and reports it to the channel where it was invoked.
    Usage: !status
    """
    status_message = "Checking realm status..."
    message = await ctx.send(status_message) # Send an initial "checking" message

    data = await fetch_realm_status_data()

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

# --- Command to Set Notification Channel ---
@bot.command(name="setchannel", help="Sets the channel for realm status notifications for this server. (Admin Only)")
@commands.has_permissions(administrator=True) # Restrict to administrators
async def set_channel_command(ctx, channel: discord.TextChannel):
    """
    Sets the notification channel for this server.
    Usage: !setchannel #your-channel-name (or !setchannel <channel_id>)
    """
    try:
        guild_id = ctx.guild.id
        channel_id = channel.id
        await set_notification_channel(guild_id, channel_id)
        await ctx.send(f"Notification channel for this server has been set to {channel.mention}!")
        print(f"[{discord.utils.utcnow()}] Guild '{ctx.guild.name}' ({guild_id}): Notification channel set to {channel.name} ({channel_id}).")
    except Exception as e:
        await ctx.send(f"An error occurred while setting the channel: {e}")
        print(f"[{discord.utils.utcnow()}] Error setting channel in guild '{ctx.guild.name}': {e}")

@set_channel_command.error
async def set_channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Please specify a channel. Usage: `{COMMAND_PREFIX}setchannel #your-channel` or `{COMMAND_PREFIX}setchannel <channel_id>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid channel specified. Please ensure it's a valid text channel.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the necessary permissions (Administrator) to use this command.")
    else:
        await ctx.send(f"An error occurred: {error}")
    print(f"[{discord.utils.utcnow()}] Error in {COMMAND_PREFIX}setchannel command: {error}")

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
