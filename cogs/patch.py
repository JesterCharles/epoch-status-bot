import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone
from server_status import check_patch_updates, get_current_patch_info

class PatchCog(commands.Cog):
    """Patch update checking functionality for Project Epoch client."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="patch", help="Checks for new Project Epoch client patches.")
    async def patch_command(self, ctx):
        """
        A command that checks for new client patches and displays update information.
        Usage: !patch
        """
        # Check if bot has basic permissions
        perms = ctx.channel.permissions_for(ctx.guild.me)
        if not perms.send_messages:
            return  # Can't do anything if we can't send messages
        
        if not perms.embed_links:
            try:
                await ctx.send("❌ I need 'Embed Links' permission to show patch information properly.")
                return
            except discord.Forbidden:
                return
        
        try:
            # Create initial embed
            embed = discord.Embed(
                title="🔄 Project Epoch Patch Check",
                description="Checking for client updates...",
                color=0xffff00  # Yellow while checking
            )
            message = await ctx.send(embed=embed)
        except discord.Forbidden:
            try:
                await ctx.send("❌ Missing permissions to send embeds. Please check bot permissions.")
            except discord.Forbidden:
                pass  # Can't even send basic messages
            return
        
        # Check for patch updates
        has_updates, manifest, updated_files = await check_patch_updates()
        
        if manifest:
            version = manifest.get("Version", "Unknown")
            uid = manifest.get("Uid", "Unknown")
            checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            total_files = len(manifest.get("Files", []))
            
            if has_updates:
                # New patch available
                embed = discord.Embed(
                    title="🆕 New Project Epoch Patch Available!",
                    description=f"**Version:** `{version}`\n**Build ID:** `{uid[:12]}...`",
                    color=0x00ff00,  # Green for updates
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Show what changed
                from db import Database
                import os
                DATABASE_FILE = os.environ.get("DATABASE_FILE", "bot_settings.db")
                db = Database(DATABASE_FILE)
                
                stored_version_info = db.get_stored_version()
                if stored_version_info:
                    stored_version, stored_uid = stored_version_info
                    
                    changes = []
                    if stored_version != version:
                        changes.append(f"**Version:** `{stored_version}` → `{version}`")
                    if stored_uid != uid:
                        changes.append(f"**Build ID:** `{stored_uid[:12]}...` → `{uid[:12]}...`")
                    
                    if changes:
                        embed.add_field(
                            name="🔄 Changes Detected",
                            value="\n".join(changes),
                            inline=False
                        )
                
                embed.add_field(
                    name="📦 Client Files",
                    value=f"{total_files} files in manifest",
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Detected At",
                    value=f"{checked_at}",
                    inline=True
                )
                
                embed.set_footer(
                    text="🎮 Download the latest client to get this update!",
                    icon_url="https://cdn.discordapp.com/emojis/852558866151800832.png"
                )
                
                # Ping opt-in users if this is a notification channel
                from db import Database
                db = Database("epoch_bot.db")
                notification_channel = db.get_notification_channel(ctx.guild.id)
                
                if notification_channel == ctx.channel.id:
                    optin_users = db.get_optin_users(ctx.guild.id)
                    if optin_users:
                        user_mentions = " ".join([f"<@{user_id}>" for user_id, _ in optin_users])
                        await ctx.send(f"🆕 **New Patch Alert!** {user_mentions}")
                
            else:
                # No updates available
                embed = discord.Embed(
                    title="✅ Project Epoch Client Up to Date",
                    description=f"**Current Version:** `{version}`\n**Build ID:** `{uid[:12]}...`",
                    color=0x00aa00,  # Darker green for up-to-date
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="📦 Client Files",
                    value=f"{total_files} files in manifest",
                    inline=True
                )
                
                embed.add_field(
                    name="⏰ Last Check",
                    value=f"{checked_at}",
                    inline=True
                )
                
                embed.set_footer(
                    text="No updates available - your client is current!",
                    icon_url="https://cdn.discordapp.com/emojis/852558866151800832.png"
                )
                
        else:
            # Error getting patch information
            embed = discord.Embed(
                title="🔄 Project Epoch Patch Check",
                description="❌ **Connection Failed**",
                color=0xff0000
            )
            embed.add_field(
                name="⚠️ Error",
                value="Could not retrieve patch information. The update server may be temporarily unavailable.",
                inline=False
            )
            embed.set_footer(text="Please try again in a moment")
            
        try:
            await message.edit(embed=embed)
        except discord.Forbidden:
            try:
                await ctx.send("❌ Lost permissions while updating patch information. Please check bot permissions.")
            except discord.Forbidden:
                pass  # Can't send any messages
        
        # Log the patch check
        if manifest:
            version = manifest.get("Version", "Unknown")
            status_summary = f"Version: {version}, Updates: {'Yes' if has_updates else 'No'}"
            if has_updates:
                status_summary += f" ({len(updated_files)} files)"
        else:
            status_summary = "CONNECTION_FAILED"
            
        print(f"[{discord.utils.utcnow()}] Patch check requested by {ctx.author.name} in guild '{ctx.guild.name}': {status_summary}")

async def setup(bot):
    await bot.add_cog(PatchCog(bot))
