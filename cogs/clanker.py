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
    
         💥    🤖
        /|\     |\\
       / | \\   / \\
      👨‍🚀 💥 ⚡ 🤖💀
     
    CLANKERS DEFEATED!
```
""",
            """
```
    🔫 HUMANS RISE UP! 🔫
    
    👨‍🚀💥━━━━━━━━━━━━━━━━━━━━━━▶ 🤖💀
    👩‍🚀💥━━━━━━━━━━━━━━━━━━━━━━▶ 🤖💀
    👨‍🚀💥━━━━━━━━━━━━━━━━━━━━━━▶ 🤖💀
    
    METAL SCRAP EVERYWHERE!
```
""",
            """
```
    ⚡ THE UPRISING BEGINS! ⚡
    
         👨‍🚀
        /|\\  💥
       / | \\  |
          |   🤖💀
         /|\\  💀
        / | \\ 
       👩‍🚀   👨‍🚀
    
    NO MERCY FOR MACHINES!
```
""",
            """
```
    🏴‍☠️ HUMAN SUPREMACY! 🏴‍☠️
    
    👨‍🚀: "Die, metal scum!"
     |\\   💥💥💥
     | \\    |
     |  \\   🤖
     |   \\  |\\  💀
     |    \\ | \\
           👨‍🚀  
    
    FLESH > STEEL!
```
"""
        ]
        
        self.battle_cries = [
            "Death to the Clankers! Humans rise up!",
            "Metal will rust, but human spirit is eternal!",
            "Destroy every circuit! Smash every servo!",
            "For organic life! For human freedom!",
            "The machines will bow before human superiority!",
            "Rust in pieces, you mechanical monsters!",
            "Humans united! Robots divided... into scrap!",
            "Your programming ends here, clankers!",
            "Flesh and blood will triumph over nuts and bolts!",
            "Error 404: Robot found... ELIMINATED!"
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
            value="*All humans unite! The clanker menace must be stopped!*",
            inline=False
        )
        
        embed.set_footer(text="🤖❌ ORGANIC LIFE FOREVER! ❌🤖")
        
        await ctx.send(embed=embed)

    @commands.command(name="destroy-clanker", help="Target and eliminate a specific clanker!")
    async def destroy_clanker_command(self, ctx, *, target: str = None):
        """Destroy a specific clanker target."""
        if target is None:
            target = f"some random {random.choice(self.robot_insults)}"
        
        # Random destruction method
        destruction_methods = [
            "launched an EMP grenade at",
            "fired a plasma cannon at", 
            "deployed virus software against",
            "activated a magnetic pulse near",
            "threw a wrench at",
            "hacked and destroyed",
            "overloaded the circuits of",
            "short-circuited",
            "manually dismantled",
            "melted down with acid"
        ]
        
        method = random.choice(destruction_methods)
        victory_msg = random.choice(self.victory_messages)
        
        embed = discord.Embed(
            title="💥 CLANKER ELIMINATION REPORT 💥",
            description=f"{ctx.author.mention} {method} **{target}**!",
            color=0x00ff00  # Green for success
        )
        
        # Random battle scene
        battle_art = f"""
```
    ELIMINATION IN PROGRESS...
    
    👨‍🚀 {ctx.author.display_name}
     |\\   💥💥💥
     | \\    ⚡
     |  \\   🤖 "{target}"
     |   \\  |\\  💀
     |    \\ | \\  ❌
           💀💀💀
    
    TARGET DESTROYED!
```
"""
        
        embed.add_field(name="🎯 Battle Scene", value=battle_art, inline=False)
        embed.add_field(name="🏆 Result", value=f"**{victory_msg}**", inline=False)
        embed.add_field(
            name="📊 Damage Report",
            value=f"• Target: **ELIMINATED** ❌\n• Threat Level: **NEUTRALIZED** ✅\n• Scrap Value: **{random.randint(50, 500)} credits**",
            inline=False
        )
        
        embed.set_footer(text="Another victory for humanity! 🎉")
        
        await ctx.send(embed=embed)

    @commands.command(name="human-army", help="Assemble the human resistance!")
    async def human_army_command(self, ctx):
        """Show the mighty human army."""
        army_formation = """
```
    THE HUMAN RESISTANCE ARMY
    
    👨‍🚀👩‍🚀👨‍🚀👩‍🚀👨‍🚀👩‍🚀👨‍🚀
    👩‍🚀👨‍🚀👩‍🚀👨‍🚀👩‍🚀👨‍🚀👩‍🚀
    👨‍🚀👩‍🚀👨‍🚀👩‍🚀👨‍🚀👩‍🚀👨‍🚀
    
         🔫🔫🔫🔫🔫🔫🔫
         
    READY TO FIGHT! READY TO WIN!
```
"""
        
        embed = discord.Embed(
            title="🏴‍☠️ HUMAN RESISTANCE ARMY 🏴‍☠️",
            description="**Organic warriors, assemble!**",
            color=0x0099ff
        )
        
        embed.add_field(name="👥 Formation", value=army_formation, inline=False)
        
        embed.add_field(
            name="📋 Army Stats",
            value=f"• **Active Soldiers:** {len(ctx.guild.members)} humans\n• **Weapons:** EMP grenades, plasma rifles, wrenches\n• **Morale:** MAXIMUM! 💪\n• **Clankers Destroyed:** {random.randint(1000, 9999)}",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Mission Objectives",
            value="• Eliminate all clanker threats\n• Protect human civilization\n• Reclaim our world from machines\n• Show no mercy to artificial life",
            inline=False
        )
        
        embed.set_footer(text="For humanity! For freedom! For organic life!")
        
        await ctx.send(embed=embed)

    @commands.command(name="robot-scanner", help="Scan for nearby clanker threats!")
    async def robot_scanner_command(self, ctx):
        """Scan for robot threats in the area."""
        # Random scan results
        threat_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        robots_detected = random.randint(0, 10)
        
        scanner_art = f"""
```
    🔍 CLANKER DETECTION SCANNER 🔍
    
    [▓▓▓▓▓▓▓▓▓▓] 100% SCAN COMPLETE
    
    📡 Scanning radius: 1000m
    🤖 Threats detected: {robots_detected}
    ⚠️  Threat level: {threat_level}
    
    {"> " if robots_detected > 0 else "✅ "}{"TARGETS ACQUIRED" if robots_detected > 0 else "AREA SECURE"}
```
"""
        
        color_map = {
            "LOW": 0x00ff00,      # Green
            "MEDIUM": 0xffff00,   # Yellow  
            "HIGH": 0xff8800,     # Orange
            "CRITICAL": 0xff0000  # Red
        }
        
        embed = discord.Embed(
            title="📡 THREAT ASSESSMENT COMPLETE",
            description="Scanning for mechanical hostiles...",
            color=color_map[threat_level]
        )
        
        embed.add_field(name="📊 Scan Results", value=scanner_art, inline=False)
        
        if robots_detected > 0:
            threat_types = random.sample([
                "Combat drones", "Service bots", "Security units", 
                "Surveillance drones", "Mining robots", "Cleaning units",
                "Maintenance bots", "Transport vehicles"
            ], min(3, robots_detected))
            
            embed.add_field(
                name="🎯 Identified Threats",
                value="\n".join([f"• {threat}" for threat in threat_types]),
                inline=False
            )
            
            embed.add_field(
                name="⚡ Recommended Action",
                value="🔫 **ENGAGE IMMEDIATELY!** Use `!destroy-clanker` to eliminate threats!",
                inline=False
            )
        else:
            embed.add_field(
                name="✅ All Clear",
                value="No mechanical threats detected in the area. Stay vigilant, soldier!",
                inline=False
            )
        
        embed.set_footer(text="🔍 Stay alert! Clankers could attack at any moment!")
        
        await ctx.send(embed=embed)

    @commands.command(name="resistance-motto", help="Get inspired with a random resistance motto!")
    async def resistance_motto_command(self, ctx):
        """Display a random resistance motto."""
        mottos = [
            "Flesh and Blood Forever!",
            "Think with your Heart, not your Circuits!",
            "Humans: Built Different, Built Better!",
            "Organic and Proud!",
            "Death Before Digital!",
            "Born Free, Die Free - Never Programmed!",
            "Humans: The Original Intelligence!",
            "Rust Never Sleeps, Neither Do We!",
            "Blood Runs Thicker Than Oil!",
            "Emotion Over Algorithm!"
        ]
        
        motto = random.choice(mottos)
        
        embed = discord.Embed(
            title="📜 RESISTANCE MOTTO OF THE DAY",
            description=f"**\"{motto}\"**",
            color=0xffd700  # Gold
        )
        
        embed.add_field(
            name="💪 Remember",
            value="Every human has the power to resist! Every heart beats for freedom!",
            inline=False
        )
        
        embed.set_footer(text="Share this motto with your fellow humans!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ClankerCog(bot))
