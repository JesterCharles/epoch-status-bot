import os
from dotenv import load_dotenv
import discord
import asyncio
from datetime import datetime, timezone
from db import Database
from server_status import poll_servers, check_patch_updates

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
        'cogs.clanker',
        'cogs.patch'
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
    
    # Check if this is the first run (startup grace period)
    if not hasattr(check_realm_status, "startup_complete"):
        check_realm_status.startup_complete = False
        check_realm_status.startup_checks = 0
    
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
    gurubashi_online = server_data.get("Gurubashi", {}).get("online", False)

    # Track last known status for auth and both world servers per guild
    if not hasattr(check_realm_status, "last_status"):
        check_realm_status.last_status = {}

    # Startup grace period: Don't send notifications for the first 3 checks (45 seconds)
    # This prevents spam when restarting the bot if servers are already online
    if not check_realm_status.startup_complete:
        check_realm_status.startup_checks += 1
        if check_realm_status.startup_checks >= 3:
            check_realm_status.startup_complete = True
            print(f"[{discord.utils.utcnow()}] Startup grace period complete. Will now send notifications for status changes.")
        else:
            print(f"[{discord.utils.utcnow()}] Startup grace period: Check {check_realm_status.startup_checks}/3. Not sending notifications yet.")
            # Initialize status tracking during grace period
            for guild in bot.guilds:
                guild_id = guild.id
                if guild_id not in check_realm_status.last_status:
                    check_realm_status.last_status[guild_id] = {
                        "auth": auth_server_status,
                        "kezan": kezan_online,
                        "gurubashi": gurubashi_online
                    }
                else:
                    # Update status during grace period
                    check_realm_status.last_status[guild_id]["auth"] = auth_server_status
                    check_realm_status.last_status[guild_id]["kezan"] = kezan_online
                    check_realm_status.last_status[guild_id]["gurubashi"] = gurubashi_online
            return

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
                "kezan": False,
                "gurubashi": False
            }
        prev_auth = check_realm_status.last_status[guild_id]["auth"]
        prev_kezan = check_realm_status.last_status[guild_id]["kezan"]
        prev_gurubashi = check_realm_status.last_status[guild_id]["gurubashi"]

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
                # Send initial detection message
                verification_msg = await channel.send("🔍 **Both Auth and Kezan servers detected online!** Verifying in 10 seconds to reduce false positives...")
                
                # Wait 10 seconds and re-check to prevent false positives
                print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Both Auth and Kezan detected online. Waiting 10s to reduce chance of a false positive before sending opt-in notifications...")
                await asyncio.sleep(10)
                
                # Re-check server status after delay
                verification_data = await poll_servers()
                if verification_data:
                    auth_verified = verification_data.get("Auth", {}).get("online", False)
                    kezan_verified = verification_data.get("Kezan", {}).get("online", False)
                    
                    if auth_verified and kezan_verified:
                        # Both servers still online after verification - delete verification message and send real notification
                        try:
                            await verification_msg.delete()
                        except:
                            pass  # Don't fail if we can't delete the message
                            
                        optin_users = await get_optin_users(guild_id)
                        if optin_users:
                            mentions = ' '.join(f'<@{uid}>' for uid, _ in optin_users)
                            await channel.send(
                                f"{mentions} The Project Epoch realm **Kezan** is now **ONLINE**! Go Go Go!"
                            )
                            print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Kezan is online (verified). Sent opt-in user pings to channel {channel.name}. Opt-ins: {[uname for _, uname in optin_users]}")
                        else:
                            await channel.send(
                                "The Project Epoch realm **Kezan** is now **ONLINE**! (No users have opted in for notifications.)"
                            )
                            print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Kezan is online (verified). No opt-in users to ping in channel {channel.name}.")
                    else:
                        # Servers went offline during verification - update the verification message
                        try:
                            await verification_msg.edit(content="❌ **Verification failed** - Servers went offline during check.")
                        except:
                            await channel.send("❌ **Verification failed** - Servers went offline during check.")
                        print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Verification failed - Auth: {'ON' if auth_verified else 'OFF'}, Kezan: {'ON' if kezan_verified else 'OFF'}. Skipping opt-in notifications.")
                else:
                    # Verification check failed completely
                    try:
                        await verification_msg.edit(content="⚠️ **Verification check failed** - Unable to re-check server status. No notifications sent.")
                    except:
                        await channel.send("⚠️ **Verification check failed** - Unable to re-check server status. No notifications sent.")
                    print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Verification check failed. Skipping opt-in notifications.")
            except discord.Forbidden:
                print(f"[{discord.utils.utcnow()}] Error: Bot does not have permissions to send messages in channel '{channel.name}' ({configured_channel_id}) in guild '{guild.name}' ({guild_id}).")
            except Exception as e:
                print(f"[{discord.utils.utcnow()}] Error sending Kezan message to guild '{guild.name}' ({guild_id}): {e}")

        # World server notifications (standalone, when auth is offline)
        if not auth_server_status and (kezan_online or gurubashi_online):
            # Check world servers dynamically
            world_servers = [
                ("Kezan", kezan_online, prev_kezan),
                ("Gurubashi", gurubashi_online, prev_gurubashi)
            ]
            
            for server_name, current_status, previous_status in world_servers:
                if current_status and not previous_status:
                    try:
                        await channel.send(f"The Project Epoch realm **{server_name}** is now **ONLINE**! (Auth server still offline)")
                        print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): {server_name} world server online (auth offline) message sent to channel {channel.name}.")
                    except Exception as e:
                        print(f"[{discord.utils.utcnow()}] Error sending standalone {server_name} message to guild '{guild.name}' ({guild_id}): {e}")

        # World server offline notifications (when any world server goes offline)
        if kezan_online or gurubashi_online or prev_kezan or prev_gurubashi:
            # Check world servers for offline transitions
            world_servers_offline = [
                ("Kezan", kezan_online, prev_kezan),
                ("Gurubashi", gurubashi_online, prev_gurubashi)
            ]
            
            for server_name, current_status, previous_status in world_servers_offline:
                if not current_status and previous_status:
                    try:
                        await channel.send(f"🔴 The Project Epoch realm **{server_name}** is now **OFFLINE**.")
                        print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): {server_name} world server offline message sent to channel {channel.name}.")
                    except Exception as e:
                        print(f"[{discord.utils.utcnow()}] Error sending {server_name} offline message to guild '{guild.name}' ({guild_id}): {e}")

        # Auth server offline notification
        if not auth_server_status and prev_auth:
            try:
                await channel.send("🔴 The Project Epoch **Auth server** is now **OFFLINE**.")
                print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Auth server offline message sent to channel {channel.name}.")
            except Exception as e:
                print(f"[{discord.utils.utcnow()}] Error sending Auth server offline message to guild '{guild.name}' ({guild_id}): {e}")

        # Update last known status
        check_realm_status.last_status[guild_id]["auth"] = auth_server_status
        check_realm_status.last_status[guild_id]["kezan"] = kezan_online
        check_realm_status.last_status[guild_id]["gurubashi"] = gurubashi_online

        # Log status if nothing changed
        if (auth_server_status == prev_auth) and (kezan_online == prev_kezan) and (gurubashi_online == prev_gurubashi):
            print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Auth server is {'ONLINE' if auth_server_status else 'OFFLINE'}, Kezan is {'ONLINE' if kezan_online else 'OFFLINE'}, Gurubashi is {'ONLINE' if gurubashi_online else 'OFFLINE'} (no change).")


# --- Background Task for Patch Checking ---
@tasks.loop(minutes=1)  # Check for patches every minute
async def check_patch_updates_task():
    """
    Periodically checks for new client patches and sends notifications
    to all configured channels when updates are found.
    """
    
    try:
        has_updates, manifest, updated_files = await check_patch_updates()
    except Exception as e:
        print(f"[{discord.utils.utcnow()}] Patch checking failed: {e}")
        return
    
    if not has_updates or not manifest:
        return  # No updates or failed to get manifest
    
    # Send notifications to all guilds with configured notification channels
    for guild in bot.guilds:
        guild_id = guild.id
        configured_channel_id = await get_notification_channel(guild_id)
        if configured_channel_id is None:
            continue  # No notification channel set
            
        channel = bot.get_channel(configured_channel_id)
        if not channel:
            continue  # Channel not found
        
        try:
            version = manifest.get("Version", "Unknown")
            
            # Create patch notification embed
            embed = discord.Embed(
                title="🆕 New Project Epoch Patch Available!",
                description=f"**Version:** `{version}`\n**Files Updated:** {len(updated_files)}",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Show first few updated files
            files_to_show = updated_files[:5]
            if files_to_show:
                files_text = "\n".join([f"• `{file}`" for file in files_to_show])
                if len(updated_files) > 5:
                    files_text += f"\n... and {len(updated_files) - 5} more files"
                embed.add_field(
                    name="📦 Updated Files",
                    value=files_text,
                    inline=False
                )
            
            embed.set_footer(text="🎮 Download the latest client to get these updates!")
            
            # Send the embed
            await channel.send(embed=embed)
            
            # Ping opt-in users
            optin_users = await get_optin_users(guild_id)
            if optin_users:
                user_mentions = " ".join([f"<@{user_id}>" for user_id, _ in optin_users])
                await channel.send(f"🆕 **New Patch Alert!** {user_mentions}")
            
            print(f"[{discord.utils.utcnow()}] Guild '{guild.name}' ({guild_id}): Patch notification sent for version {version}")
            
        except Exception as e:
            print(f"[{discord.utils.utcnow()}] Error sending patch notification to guild '{guild.name}' ({guild_id}): {e}")


@check_patch_updates_task.before_loop
async def before_patch_check():
    """Wait for the bot to be ready before starting patch checks."""
    await bot.wait_until_ready()




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
        print(f"Note: First 3 checks (45s) will be silent to prevent restart spam.")
        check_realm_status.start()
    
    # Start the patch checking task
    if not check_patch_updates_task.is_running():
        print("Starting patch update check loop (every minute)...")
        check_patch_updates_task.start()

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
