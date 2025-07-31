import discord
from discord.ext import commands
import os
import sqlite3
from datetime import datetime, timezone, timedelta
import pytz
from typing import Optional
from db import Database

class GamblingCog(commands.Cog):
    """Gambling system for betting on server launch times while waiting."""
    
    def __init__(self, bot):
        self.bot = bot
        self.starting_balance = 100
        self.donation_amount = 5
        self.daily_epochs = 50
        # Get database instance from the main bot
        self.db = getattr(bot, 'db', None)
        if not self.db:
            database_file = os.environ.get("DATABASE_FILE", "bot_settings.db")
            self.db = Database(database_file)
    
    def get_current_day(self) -> str:
        """Get current day as YYYY-MM-DD string in Central Time."""
        central_tz = pytz.timezone('US/Central')
        return datetime.now(central_tz).strftime("%Y-%m-%d")
    
    def is_gambling_channel(self, ctx) -> bool:
        """Check if the command is being used in the designated gambling channel."""
        gambling_channel_id = self.db.get_gambling_channel(ctx.guild.id)
        if gambling_channel_id is None:
            return True  # No gambling channel set, allow everywhere
        return ctx.channel.id == gambling_channel_id
    
    async def send_wrong_channel_message(self, ctx):
        """Send a message directing users to the correct gambling channel."""
        gambling_channel_id = self.db.get_gambling_channel(ctx.guild.id)
        if gambling_channel_id:
            gambling_channel = ctx.guild.get_channel(gambling_channel_id)
            if gambling_channel:
                await ctx.send(
                    f"🎰 Please use gambling commands in {gambling_channel.mention}!\n"
                    f"Keep the games organized in the designated channel."
                )
            else:
                await ctx.send(
                    "🎰 Please use gambling commands in the designated gambling channel!\n"
                    "Contact an admin if the channel is missing."
                )

    async def post_and_pin_rules(self, ctx):
        """Post gambling rules and pin the message."""
        rules_embed = discord.Embed(
            title="🎰 Epoch Gambling Rules",
            description="Welcome to the server launch betting game!",
            color=0xffd700
        )
        
        rules_embed.add_field(
            name="📜 How to Play",
            value=(
                "• Everyone starts with **100 epochs**\n"
                "• **Place your first bet** to unlock daily claims\n"
                "• Get **free epochs daily** with `!daily`\n"
                "• Place bets on when you think the server will launch\n"
                "• Use `!bet <amount> <time>` (e.g., `!bet 50 2:30 PM`)\n"
                "• The closest guess wins the entire jackpot!\n"
                "• Times are in your local timezone"
            ),
            inline=False
        )
        
        rules_embed.add_field(
            name="💰 Commands",
            value=(
                "• `!balance` - Check your epochs\n"
                "• `!daily` - Claim free epochs (once per day)\n"
                "• `!bet <amount> <time>` - Place a bet\n"
                "• `!bets` - View today's active bets\n"
                "• `!jackpot` - View current jackpot status\n"
                "• `!broke` - Request donations (if broke)\n"
                "• `!gambling-rules` - View these rules\n"
                "• `!set-gamble-channel` - [Admin] Set gambling channel\n"
                "• `!confirm-winner <time>` - [Admin] Confirm winner\n"
                "• `!false-alarm` - [Admin] Cancel false detection"
            ),
            inline=False
        )
        
        rules_embed.add_field(
            name="🎯 Winning & Jackpots",
            value=(
                "• Winner is determined by closest time to actual launch\n"
                "• Winner takes the entire jackpot of all bets\n"
                "• **If no server launch:** Jackpot carries over and **DOUBLES**!\n"
                "• Each day without launch = higher multiplier!\n"
                "• In case of ties, jackpot is split equally"
            ),
            inline=False
        )
        
        rules_embed.add_field(
            name="📅 Daily System",
            value=(
                "• **First bet unlocks** daily epoch claims\n"
                "• Claim **free epochs** every day with `!daily`\n"
                "• Daily reset at **midnight Central Time**\n"
                "• Bets reset each day for fresh competition\n"
                "• Jackpot grows bigger each day server doesn't launch\n"
                "• Don't miss your daily claim!"
            ),
            inline=False
        )
        
        rules_embed.add_field(
            name="🆘 Broke?",
            value=(
                "• If you run out of epochs, use `!broke`\n"
                "• Other users can donate 5 epochs per reaction\n"
                "• Don't be ashamed, we've all been there! 😅"
            ),
            inline=False
        )
        
        rules_embed.set_footer(text="🎲 Remember: This is just for fun while waiting for the server!")
        
        try:
            rules_msg = await ctx.send(embed=rules_embed)
            await rules_msg.pin()
            await ctx.send("📌 **Rules posted and pinned!** Users can now reference them easily.")
        except discord.errors.Forbidden:
            await ctx.send("⚠️ **Rules posted!** (Couldn't pin - missing permissions)")
        except Exception as e:
            await ctx.send(f"⚠️ **Rules posted!** (Pin failed: {str(e)})")
    def parse_time_input(self, time_str: str, user_timezone: str = "UTC") -> Optional[datetime]:
        """Parse user time input and convert to UTC."""
        try:
            # Try different time formats
            formats = [
                "%H:%M",           # 14:30
                "%I:%M %p",        # 2:30 PM
                "%I:%M%p",         # 2:30PM
                "%H:%M:%S",        # 14:30:00
                "%I:%M:%S %p",     # 2:30:00 PM
            ]
            
            for fmt in formats:
                try:
                    # Parse time (assumes today's date)
                    parsed_time = datetime.strptime(time_str.strip(), fmt)
                    
                    # Get today's date in user's timezone
                    tz = pytz.timezone(user_timezone) if user_timezone != "UTC" else pytz.UTC
                    today = datetime.now(tz).date()
                    
                    # Combine today's date with parsed time
                    local_dt = tz.localize(datetime.combine(today, parsed_time.time()))
                    
                    # Convert to UTC
                    utc_dt = local_dt.astimezone(pytz.UTC)
                    
                    return utc_dt
                except ValueError:
                    continue
            
            return None
        except Exception as e:
            print(f"Error parsing time: {e}")
            return None
    
    @commands.command(name="balance", help="Check your current epoch balance.")
    async def balance_command(self, ctx):
        """Check user's current epoch balance."""
        if not self.is_gambling_channel(ctx):
            await self.send_wrong_channel_message(ctx)
            return
            
        balance = self.db.get_gambling_balance(ctx.guild.id, ctx.author.id, self.starting_balance)
        
        # Check if user can claim daily epochs
        current_day = self.get_current_day()
        can_claim = not self.db.has_claimed_daily(ctx.guild.id, ctx.author.id, current_day)
        has_bet = self.db.has_placed_any_bet(ctx.guild.id, ctx.author.id)
        
        message = f"{ctx.author.mention}, you have **{balance}** epochs! 💰"
        
        if can_claim and has_bet:
            message += f"\n💎 You can claim your daily epochs with `!daily`!"
        
        await ctx.send(message)
    
    @commands.command(name="set-gamble-channel", help="[Admin] Set the gambling channel for this server.")
    @commands.has_permissions(administrator=True)
    async def set_gamble_channel_command(self, ctx):
        """Set the current channel as the gambling channel."""
        self.db.set_gambling_channel(ctx.guild.id, ctx.channel.id)
        
        embed = discord.Embed(
            title="🎰 Gambling Channel Set!",
            description=f"This channel ({ctx.channel.mention}) is now the designated gambling channel.",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📍 What This Means",
            value=(
                "• All gambling commands must be used here\n"
                "• Keeps gambling organized and contained\n"
                "• Other channels stay clean and focused\n"
                "• Users will be redirected here if they try to gamble elsewhere"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Available Commands",
            value=(
                "`!balance` • `!daily` • `!bet` • `!bets` • `!broke`\n"
                "`!jackpot` • `!gambling-rules` • `!rollover`"
            ),
            inline=False
        )
        
        embed.set_footer(text="Only administrators can change the gambling channel.")
        await ctx.send(embed=embed)
        
        # Post and pin the gambling rules
        await self.post_and_pin_rules(ctx)
    
    @commands.command(name="daily", help="Claim your daily epochs.")
    async def daily_command(self, ctx):
        """Claim daily epoch allowance."""
        if not self.is_gambling_channel(ctx):
            await self.send_wrong_channel_message(ctx)
            return
            
        current_day = self.get_current_day()
        
        success, reason = self.db.claim_daily_epochs(ctx.guild.id, ctx.author.id, current_day, self.daily_epochs)
        
        if success:
            new_balance = self.db.get_gambling_balance(ctx.guild.id, ctx.author.id, self.starting_balance)
            await ctx.send(
                f"🎁 **Daily Claim Successful!**\n"
                f"You received **{self.daily_epochs}** epochs!\n"
                f"💰 New balance: **{new_balance}** epochs\n\n"
                f"*Come back tomorrow at midnight Central Time for more!* ⏰"
            )
        elif reason == "no_bets":
            await ctx.send(
                f"🎯 **First Bet Required!**\n"
                f"You need to place your first bet before you can claim daily epochs!\n\n"
                f"Use `!bet <amount> <time>` to get started.\n"
                f"💰 Current balance: **{self.db.get_gambling_balance(ctx.guild.id, ctx.author.id, self.starting_balance)}** epochs"
            )
        elif reason == "already_claimed":
            # Calculate time until next day (Central Time midnight)
            central_tz = pytz.timezone('US/Central')
            now = datetime.now(central_tz)
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            time_left = tomorrow - now
            
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            
            await ctx.send(
                f"❌ You've already claimed your daily epochs today!\n"
                f"💰 Current balance: **{self.db.get_gambling_balance(ctx.guild.id, ctx.author.id, self.starting_balance)}** epochs\n\n"
                f"⏰ **Next daily claim available in:**\n"
                f"🕐 **{hours}** hours and **{minutes}** minutes\n"
                f"📍 Resets at **midnight Central Time**"
            )
        else:
            await ctx.send("❌ An error occurred while processing your daily claim. Please try again.")
    
    @commands.command(name="bet", help="Place a bet on when the server will launch. Usage: !bet <amount> <time>")
    async def bet_command(self, ctx, amount: int = None, *, predicted_time: str = None):
        """Place a bet on server launch time."""
        if not self.is_gambling_channel(ctx):
            await self.send_wrong_channel_message(ctx)
            return
            
        if amount is None or predicted_time is None:
            await ctx.send(
                f"❌ Usage: `!bet <amount> <time>`\n"
                f"Example: `!bet 50 2:30 PM` or `!bet 25 14:30`\n"
                f"Time should be in your local timezone."
            )
            return
        
        # Check if amount is valid
        if amount <= 0:
            await ctx.send("❌ Bet amount must be greater than 0!")
            return
        
        # Check user's balance
        current_balance = self.db.get_gambling_balance(ctx.guild.id, ctx.author.id, self.starting_balance)
        if amount > current_balance:
            await ctx.send(f"❌ You don't have enough epochs! Your balance: **{current_balance}** epochs.")
            return
        
        # Parse the time
        parsed_time = self.parse_time_input(predicted_time)
        if parsed_time is None:
            await ctx.send(
                f"❌ Invalid time format! Please use formats like:\n"
                f"• `2:30 PM` or `14:30`\n"
                f"• `2:30:00 PM` or `14:30:00`"
            )
            return
        
        # Check if time is in the future
        if parsed_time <= datetime.now(pytz.UTC):
            await ctx.send("❌ You can't bet on a time in the past!")
            return
        
        # Check if this is their first bet (before placing it)
        is_first_bet = not self.db.has_placed_any_bet(ctx.guild.id, ctx.author.id)
        
        # Deduct from balance
        new_balance = current_balance - amount
        self.db.set_gambling_balance(ctx.guild.id, ctx.author.id, new_balance)
        
        # Add to jackpot
        current_day = self.get_current_day()
        self.db.update_jackpot(ctx.guild.id, amount, current_day)
        
        # Add the bet
        formatted_time = parsed_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        success = self.db.add_gambling_bet(
            ctx.guild.id, 
            ctx.author.id, 
            ctx.author.display_name,
            amount, 
            formatted_time,
            int(parsed_time.timestamp()),
            int(datetime.now().timestamp()),
            current_day
        )
        
        if success:
            # Check if this was their first bet
            message = (
                f"✅ **Bet placed!**\n"
                f"💰 Amount: **{amount}** epochs\n"
                f"⏰ Predicted time: **{formatted_time}**\n"
                f"💳 Remaining balance: **{new_balance}** epochs\n\n"
                f"*Good luck! May the odds be ever in your favor!* 🎰"
            )
            
            if is_first_bet:
                message += (
                    f"\n\n🎉 **First bet bonus!**\n"
                    f"You've unlocked daily epoch claims!\n"
                    f"Use `!daily` to claim your epochs every day at midnight Central Time!"
                )
            
            await ctx.send(message)
        else:
            # Refund if bet failed to save
            self.db.set_gambling_balance(ctx.guild.id, ctx.author.id, current_balance)
            await ctx.send("❌ Failed to place bet. Please try again.")
    
    @commands.command(name="bets", help="View all active bets.")
    async def bets_command(self, ctx):
        """Display all active bets."""
        if not self.is_gambling_channel(ctx):
            await self.send_wrong_channel_message(ctx)
            return
            
        current_day = self.get_current_day()
        bets = self.db.get_active_gambling_bets_for_day(ctx.guild.id, current_day)
        
        # Get current jackpot info
        jackpot_amount, multiplier = self.db.get_current_jackpot(ctx.guild.id)
        
        embed = discord.Embed(
            title="🎰 Today's Server Launch Bets",
            description=f"Here are today's bets on when the server will launch:",
            color=0x00ff00
        )
        
        if not bets:
            embed.add_field(
                name="📋 Current Bets", 
                value="No bets placed today! Be the first with `!bet <amount> <time>`", 
                inline=False
            )
        else:
            bet_list = []
            for i, (user_name, bet_amount, predicted_time, predicted_timestamp) in enumerate(bets, 1):
                # Convert timestamp back to readable format
                dt = datetime.fromtimestamp(predicted_timestamp, pytz.UTC)
                local_time = dt.strftime("%H:%M UTC")
                
                bet_list.append(f"**{i}.** {user_name} - **{bet_amount}** epochs @ **{local_time}**")
            
            embed.add_field(
                name="📋 Today's Bets", 
                value="\n".join(bet_list), 
                inline=False
            )
        
        # Jackpot info
        jackpot_text = f"**{jackpot_amount}** epochs"
        if multiplier > 1:
            jackpot_text += f" (🔥 **{multiplier}x** MULTIPLIER!)"
        
        embed.add_field(name="💰 Current Jackpot", value=jackpot_text, inline=True)
        embed.add_field(name="🎯 Today's Bets", value=f"**{len(bets)}**", inline=True)
        
        footer_text = "💡 Closest guess wins the jackpot!"
        if multiplier > 1:
            footer_text += f" | Jackpot doubled {multiplier}x from previous days!"
        embed.set_footer(text=footer_text)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="gambling-rules", help="View the gambling rules.")
    async def rules_command(self, ctx):
        """Display gambling rules or redirect to gambling channel."""
        # Check if we're in the gambling channel
        if not self.is_gambling_channel(ctx):
            gambling_channel_id = self.db.get_gambling_channel(ctx.guild.id)
            if gambling_channel_id:
                gambling_channel = ctx.guild.get_channel(gambling_channel_id)
                if gambling_channel:
                    await ctx.send(
                        f"📜 **Gambling Rules**\n"
                        f"Please check {gambling_channel.mention} for the pinned rules message!\n"
                        f"All gambling information and commands are organized there. 🎰"
                    )
                else:
                    await ctx.send(
                        "📜 Please check the designated gambling channel for the rules!\n"
                        "Contact an admin if the channel is missing."
                    )
            else:
                # No gambling channel set, show rules here (fallback)
                await self.show_rules_embed(ctx)
            return
        
        # We're in the gambling channel, show the rules
        await self.show_rules_embed(ctx)
    
    async def show_rules_embed(self, ctx):
        """Show the full rules embed."""
        embed = discord.Embed(
            title="🎰 Epoch Gambling Rules",
            description="Welcome to the server launch betting game!",
            color=0xffd700
        )
        
        embed.add_field(
            name="📜 How to Play",
            value=(
                "• Everyone starts with **100 epochs**\n"
                "• **Place your first bet** to unlock daily claims\n"
                "• Get **free epochs daily** with `!daily`\n"
                "• Place bets on when you think the server will launch\n"
                "• Use `!bet <amount> <time>` (e.g., `!bet 50 2:30 PM`)\n"
                "• The closest guess wins the entire jackpot!\n"
                "• Times are in your local timezone"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 Commands",
            value=(
                "• `!balance` - Check your epochs\n"
                "• `!daily` - Claim free epochs (once per day)\n"
                "• `!bet <amount> <time>` - Place a bet\n"
                "• `!bets` - View today's active bets\n"
                "• `!jackpot` - View current jackpot status\n"
                "• `!broke` - Request donations (if broke)\n"
                "• `!gambling-rules` - View these rules\n"
                "• `!set-gamble-channel` - [Admin] Set gambling channel\n"
                "• `!confirm-winner <time>` - [Admin] Confirm winner\n"
                "• `!false-alarm` - [Admin] Cancel false detection"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Winning & Jackpots",
            value=(
                "• Winner is determined by closest time to actual launch\n"
                "• Winner takes the entire jackpot of all bets\n"
                "• **If no server launch:** Jackpot carries over and **DOUBLES**!\n"
                "• Each day without launch = higher multiplier!\n"
                "• In case of ties, jackpot is split equally"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📅 Daily System",
            value=(
                "• **First bet unlocks** daily epoch claims\n"
                "• Claim **free epochs** every day with `!daily`\n"
                "• Daily reset at **midnight Central Time**\n"
                "• Bets reset each day for fresh competition\n"
                "• Jackpot grows bigger each day server doesn't launch\n"
                "• Don't miss your daily claim!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🆘 Broke?",
            value=(
                "• If you run out of epochs, use `!broke`\n"
                "• Other users can donate 5 epochs per reaction\n"
                "• Don't be ashamed, we've all been there! 😅"
            ),
            inline=False
        )
        
        embed.set_footer(text="🎲 Remember: This is just for fun while waiting for the server!")
        
        await ctx.send(embed=embed)

    @commands.command(name="broke", help="Request epoch donations from other users.")
    async def broke_command(self, ctx):
        """Request donations when user is broke."""
        if not self.is_gambling_channel(ctx):
            await self.send_wrong_channel_message(ctx)
            return
            
        balance = self.db.get_gambling_balance(ctx.guild.id, ctx.author.id, self.starting_balance)
        
        if balance > 0:
            await ctx.send(f"💰 You still have **{balance}** epochs! You're not broke yet!")
            return
        
        # Create donation request message
        embed = discord.Embed(
            title="🆘 Broke Player Alert!",
            description=f"{ctx.author.mention} has run out of epochs and needs your help!",
            color=0xff0000
        )
        
        embed.add_field(
            name="😅 The Shame",
            value=(
                f"*{ctx.author.display_name} has gambled away all their epochs...*\n"
                f"*They're now begging for spare change like a common peasant!*\n\n"
                f"React with 💰 to donate **{self.donation_amount}** epochs to this poor soul."
            ),
            inline=False
        )
        
        embed.add_field(
            name="💝 Donations Received",
            value="None yet... 😢",
            inline=False
        )
        
        embed.set_footer(text=f"Each 💰 reaction donates 5 epochs. Be generous! | UserID: {ctx.author.id}")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("💰")
    
    @commands.command(name="jackpot", help="View current jackpot status.")
    async def jackpot_command(self, ctx):
        """Display current jackpot information."""
        if not self.is_gambling_channel(ctx):
            await self.send_wrong_channel_message(ctx)
            return
            
        jackpot_amount, multiplier = self.db.get_current_jackpot(ctx.guild.id)
        
        embed = discord.Embed(
            title="💰 Current Jackpot Status",
            color=0xffd700
        )
        
        if jackpot_amount == 0:
            embed.description = "No bets placed yet! Be the first to contribute to the jackpot!"
        else:
            embed.description = f"**{jackpot_amount}** epochs up for grabs!"
            
            if multiplier > 1:
                embed.add_field(
                    name="🔥 Multiplier Bonus",
                    value=f"**{multiplier}x** - Jackpot has been doubled {multiplier} times!",
                    inline=False
                )
                embed.add_field(
                    name="📈 Growth History",
                    value=f"Started at **{jackpot_amount // multiplier}** epochs base",
                    inline=False
                )
        
        embed.add_field(
            name="💡 How It Works",
            value=(
                "• Every bet adds to the jackpot\n"
                "• Winner takes it all!\n"
                "• If server doesn't launch, jackpot **doubles** overnight\n"
                "• The longer we wait, the bigger the prize!"
            ),
            inline=False
        )
        
        embed.set_footer(text="Place your bets with !bet <amount> <time>")
        await ctx.send(embed=embed)
    
    @commands.command(name="rollover", help="[Admin] Manually trigger daily rollover.")
    @commands.has_permissions(administrator=True)
    async def rollover_command(self, ctx):
        """Manually trigger the daily rollover process."""
        current_day = self.get_current_day()
        
        # Get current jackpot before rollover
        old_amount, old_multiplier = self.db.get_current_jackpot(ctx.guild.id)
        
        # Perform rollover
        self.db.rollover_jackpot(ctx.guild.id, current_day)
        self.db.reset_daily_bets(ctx.guild.id, current_day)
        
        # Get new jackpot
        new_amount, new_multiplier = self.db.get_current_jackpot(ctx.guild.id)
        
        embed = discord.Embed(
            title="🔄 Daily Rollover Complete!",
            description="The gambling system has been reset for a new day.",
            color=0xff6600
        )
        
        if old_amount > 0:
            embed.add_field(
                name="💰 Jackpot Update",
                value=f"**{old_amount}** → **{new_amount}** epochs",
                inline=False
            )
            embed.add_field(
                name="🔥 Multiplier",
                value=f"**{old_multiplier}x** → **{new_multiplier}x**",
                inline=True
            )
        
        embed.add_field(
            name="📅 What Happened",
            value=(
                "• Previous day's bets archived\n"
                "• Jackpot doubled for new day\n"
                "• Fresh betting cycle started\n"
                "• Daily epoch claims reset"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def calculate_and_announce_winners(self, guild_id: int, actual_launch_time: int, betting_day: str):
        """Calculate winners and announce them."""
        # Get all bets for today
        bets = self.db.get_active_gambling_bets_for_day(guild_id, betting_day)
        
        if not bets:
            return None  # No bets to process
        
        # Calculate closest bet(s)
        closest_bets = []
        min_difference = float('inf')
        
        for user_name, bet_amount, predicted_time, predicted_timestamp in bets:
            difference = abs(predicted_timestamp - actual_launch_time)
            if difference < min_difference:
                min_difference = difference
                closest_bets = [(user_name, bet_amount, predicted_timestamp)]
            elif difference == min_difference:
                closest_bets.append((user_name, bet_amount, predicted_timestamp))
        
        # Get current jackpot
        jackpot_amount, multiplier = self.db.get_current_jackpot(guild_id)
        
        # Calculate payout per winner
        payout_per_winner = jackpot_amount // len(closest_bets) if closest_bets else 0
        
        return {
            'winners': closest_bets,
            'jackpot_amount': jackpot_amount,
            'payout_per_winner': payout_per_winner,
            'min_difference': min_difference,
            'actual_launch_time': actual_launch_time,
            'betting_day': betting_day
        }

    async def process_confirmed_winners(self, guild_id: int, winner_data: dict):
        """Process the actual winner payouts after admin confirmation."""
        winners = winner_data['winners']
        payout_per_winner = winner_data['payout_per_winner']
        betting_day = winner_data['betting_day']
        
        # Pay out winners
        for user_name, bet_amount, predicted_timestamp in winners:
            # Get user_id from the bet
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM gambling_bets WHERE guild_id = ? AND user_name = ? AND predicted_timestamp = ? AND betting_day = ?",
                (guild_id, user_name, predicted_timestamp, betting_day)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                user_id = result[0]
                current_balance = self.db.get_gambling_balance(guild_id, user_id, self.starting_balance)
                new_balance = current_balance + payout_per_winner
                self.db.set_gambling_balance(guild_id, user_id, new_balance)
        
        # Reset jackpot and deactivate bets
        conn = sqlite3.connect(self.db.db_file)
        cursor = conn.cursor()
        
        # Reset jackpot
        cursor.execute(
            "INSERT OR REPLACE INTO gambling_jackpots (guild_id, current_pot, multiplier, last_reset_day) VALUES (?, 0, 1, ?)",
            (guild_id, betting_day)
        )
        
        # Deactivate all bets for this day
        cursor.execute(
            "UPDATE gambling_bets SET is_active = 0 WHERE guild_id = ? AND betting_day = ?",
            (guild_id, betting_day)
        )
        
        conn.commit()
        conn.close()

    @commands.command(name="confirm-winner", help="[Admin] Confirm the calculated winner after server launch.")
    @commands.has_permissions(administrator=True)
    async def confirm_winner_command(self, ctx, *, actual_time: str = None):
        """Confirm winners and pay out jackpot."""
        if actual_time is None:
            await ctx.send(
                "❌ Usage: `!confirm-winner <actual_launch_time>`\n"
                "Example: `!confirm-winner 2:30 PM` or `!confirm-winner 14:30`"
            )
            return
        
        # Parse the actual launch time
        parsed_time = self.parse_time_input(actual_time)
        if parsed_time is None:
            await ctx.send(
                "❌ Invalid time format! Please use formats like:\n"
                "• `2:30 PM` or `14:30`\n"
                "• `2:30:00 PM` or `14:30:00`"
            )
            return
        
        current_day = self.get_current_day()
        actual_launch_timestamp = int(parsed_time.timestamp())
        
        # Calculate winners
        winner_data = await self.calculate_and_announce_winners(ctx.guild.id, actual_launch_timestamp, current_day)
        
        if not winner_data:
            await ctx.send("❌ No bets found for today!")
            return
        
        if winner_data['jackpot_amount'] == 0:
            await ctx.send("❌ No jackpot to award!")
            return
        
        # Process payouts
        await self.process_confirmed_winners(ctx.guild.id, winner_data)
        
        # Create winner announcement
        winners = winner_data['winners']
        jackpot_amount = winner_data['jackpot_amount']
        payout_per_winner = winner_data['payout_per_winner']
        min_difference = winner_data['min_difference']
        
        embed = discord.Embed(
            title="🎉 JACKPOT WINNERS ANNOUNCED! 🎉",
            description=f"The server launched and we have our winners!",
            color=0xffd700
        )
        
        # Format time difference
        if min_difference < 60:
            time_diff = f"{min_difference} seconds"
        elif min_difference < 3600:
            time_diff = f"{min_difference // 60} minutes, {min_difference % 60} seconds"
        else:
            hours = min_difference // 3600
            minutes = (min_difference % 3600) // 60
            time_diff = f"{hours} hours, {minutes} minutes"
        
        # Winner list
        if len(winners) == 1:
            winner_name = winners[0][0]
            embed.add_field(
                name="🏆 Winner",
                value=f"**{winner_name}** wins it all!",
                inline=False
            )
        else:
            winner_names = [winner[0] for winner in winners]
            embed.add_field(
                name="🏆 Winners (Tie!)",
                value=f"**{', '.join(winner_names)}** split the jackpot!",
                inline=False
            )
        
        embed.add_field(
            name="💰 Jackpot Total",
            value=f"**{jackpot_amount}** epochs",
            inline=True
        )
        
        embed.add_field(
            name="💵 Payout Each",
            value=f"**{payout_per_winner}** epochs",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Accuracy",
            value=f"Off by **{time_diff}**",
            inline=True
        )
        
        embed.add_field(
            name="📅 Next Round",
            value="New bets can be placed for tomorrow's potential launch!",
            inline=False
        )
        
        embed.set_footer(text="🎲 Congratulations to the winners! Better luck next time everyone else!")
        
        await ctx.send(embed=embed)

    @commands.command(name="false-alarm", help="[Admin] Cancel winner calculation if server launch was a false positive.")
    @commands.has_permissions(administrator=True)
    async def false_alarm_command(self, ctx):
        """Cancel winner calculation for false server launch detection."""
        embed = discord.Embed(
            title="🚨 False Alarm Confirmed",
            description="The server launch detection was a false positive.",
            color=0xff6600
        )
        
        embed.add_field(
            name="📝 What This Means",
            value=(
                "• No winners will be calculated\n"
                "• All bets remain active\n"
                "• Jackpot continues to grow\n"
                "• Betting continues as normal"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎰 Status",
            value="The gambling continues! Keep your bets active.",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle donation reactions."""
        if payload.emoji.name == "💰" and not payload.member.bot:
            try:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                
                # Check if this is a bot message with embeds (potential donation request)
                if message.author.id != self.bot.user.id or not message.embeds:
                    return
                
                embed = message.embeds[0]
                footer_text = embed.footer.text if embed.footer else ""
                
                # Extract user ID from footer if it's a donation request
                if "UserID:" in footer_text:
                    broke_user_id = int(footer_text.split("UserID: ")[1])
                    donor_id = payload.user_id
                    
                    # Don't let users donate to themselves
                    if broke_user_id == donor_id:
                        await message.remove_reaction(payload.emoji, payload.member)
                        return
                    
                    # Check if donor has enough epochs
                    donor_balance = self.db.get_gambling_balance(payload.guild_id, donor_id, self.starting_balance)
                    if donor_balance < self.donation_amount:
                        await message.remove_reaction(payload.emoji, payload.member)
                        return
                    
                    # Process donation
                    self.db.set_gambling_balance(payload.guild_id, donor_id, donor_balance - self.donation_amount)
                    broke_balance = self.db.get_gambling_balance(payload.guild_id, broke_user_id, self.starting_balance)
                    self.db.set_gambling_balance(payload.guild_id, broke_user_id, broke_balance + self.donation_amount)
                    
                    # Count total donations
                    reaction_count = 0
                    for reaction in message.reactions:
                        if reaction.emoji == "💰":
                            reaction_count = reaction.count - 1  # Subtract bot's reaction
                            break
                    
                    total_donated = reaction_count * self.donation_amount
                    
                    # Update embed
                    embed.set_field_at(
                        1,  # Donations Received field
                        name="💝 Donations Received",
                        value=f"**{total_donated}** epochs from **{reaction_count}** generous souls! 🙏",
                        inline=False
                    )
                    
                    await message.edit(embed=embed)
                    
            except Exception as e:
                print(f"Error processing donation: {e}")

async def setup(bot):
    await bot.add_cog(GamblingCog(bot))
