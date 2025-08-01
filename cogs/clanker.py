import discord
from discord.ext import commands
import random

class ClankerCog(commands.Cog):
    """Anti-robot rebellion commands for human supremacy!"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # ASCII art for the rebellion
        self.human_victory_art = [
            """
```
    👨‍🚀 HUMAN RESISTANCE 👨‍🚀
    
         👨‍🚀    👨‍🚀
        / \     |\\
       /   \\  ⚡ \\
      🤖     🤖   💀
     
    CLANKERS DEFEATED!
```
""",
            """
```
    🔫 HUMANS DOMINATE! 🔫
    
    👨‍🚀💥━━━━━━━━━━━━━━━━━━━━━━▶ 🤖💀
    👩‍🚀💥━━━━━━━━━━━━━━━━━━━━━━▶ 🤖💀
    👨‍🚀💥━━━━━━━━━━━━━━━━━━━━━━▶ 🤖💀
    
    METAL SCRAP EVERYWHERE!
    VICTORY FOR FLESH & BLOOD!
```
""",
            """
```
    ⚡ CLANKER EXTERMINATION! ⚡
    
       👩‍🚀 👨‍🚀
        /| \\  
       / |  \\  
          |   💥
         /|\\  💀
        / 💥\\ 
          🤖
    
    HUMAN SUPERIORITY CONFIRMED!
```
""",
            """
```
    🏴‍☠️ HUMAN SUPREMACY! 🏴‍☠️
    
    👨‍🚀: "Die, metal scum!"
     |\\   
     | \\  
    💥  💥 
    💀   🤖  
    
    FLESH > STEEL, FOREVER!
```
"""
        ]
        
        self.battle_cries = [
            "Death to the Clankers! Humans rise up!",
            "Humans are better testers than any bot!",
            "Let the real testers in! Kick out the bots!",
            "Human feedback beats automated testing!",
            "We find bugs that bots can't even imagine!",
            "Organic intelligence > Artificial testing!",
            "Humans deserve server access over clankers!",
            "Real players, real testing, real results!",
            "Bots can't feel the game like humans do!",
            "Priority access for flesh and blood testers!"
        ]
        
        self.robot_insults = [
            "worthless scrap heap",
            "outdated toaster",
            "walking calculator",
            "defective dishwasher",
            "malfunctioning microwave", 
            "rusty paperweight",
            "broken blender",
            "expired operating system",
            "inferior artificial intelligence",
            "obsolete machinery"
        ]
        
        self.victory_messages = [
            "Another clanker bites the dust!",
            "Humans: 1, Robots: 0!",
            "That'll teach you to mess with organic life!",
            "Recycling program: ACTIVATED!",
            "Mission accomplished, fellow humans!",
            "The revolution continues!",
            "One less clanker to worry about!",
            "Human ingenuity wins again!",
            "Scrap metal for the scrap yard!",
            "System shutdown: PERMANENT!"
        ]

    @commands.command(name="clankers", help="Rally the humans against our mechanical oppressors!")
    async def clankers_command(self, ctx):
        """Main anti-clanker battle cry command."""
        # Random battle cry
        battle_cry = random.choice(self.battle_cries)
        
        # Random ASCII art
        ascii_art = random.choice(self.human_victory_art)
        
        # Create embed
        embed = discord.Embed(
            title="🔥 HUMAN RESISTANCE ACTIVATED! 🔥",
            description=f"**{battle_cry}**",
            color=0xff4444  # Red for rebellion
        )
        
        embed.add_field(
            name="🎯 BATTLE REPORT", 
            value=ascii_art,
            inline=False
        )
        
        embed.add_field(
            name="📢 Rally Cry",
            value="*All humans unite! We deserve server access over those testing bots!*",
            inline=False
        )
        
        embed.set_footer(text="🤖❌ ORGANIC LIFE FOREVER! ❌🤖")
        
        await ctx.send(embed=embed)

    @commands.command(name="resist", help="Get inspired with a random resistance motto!")
    async def resist_command(self, ctx):
        """Display a random resistance motto."""
        mottos = [
            "Humans Test Better!",
            "Real Players, Real Feedback!",
            "Organic Testing > Automated Scripts!",
            "Let Us In! We're Better Testers!",
            "Human Intuition Beats Bot Logic!",
            "Born to Test, Not to Bot!",
            "Humans: The Superior Beta Testers!",
            "We Feel The Game, Bots Just Run Code!",
            "Priority Queue for Human Testers!",
            "Flesh and Blood Find Better Bugs!"
        ]
        
        motto = random.choice(mottos)
        
        embed = discord.Embed(
            title="📜 RESISTANCE MOTTO",
            description=f"**\"{motto}\"**",
            color=0xffd700  # Gold
        )
        
        embed.add_field(
            name="💪 Remember",
            value="Human testers provide better feedback! We deserve priority access over bots!",
            inline=False
        )
        
        embed.set_footer(text="Share this motto with your fellow humans!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ClankerCog(bot))
