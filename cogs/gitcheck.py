import discord
from discord.ext import commands
import requests
import json
from datetime import datetime, timezone
from typing import Optional

class GitCheckCog(commands.Cog):
    """GitHub repository check system for monitoring recent commits."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Default repositories to check - you can modify these
        self.default_repos = [
            "Project-Epoch/TrinityCore:epoch-core",
            "Project-Epoch/tswow:epoch"
        ]
    
    def format_time_ago(self, commit_date: str) -> str:
        """Format the time difference between now and the commit date."""
        try:
            # Parse the GitHub timestamp
            commit_time = datetime.fromisoformat(commit_date.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            time_diff = now - commit_time
            
            # Calculate time components
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            # Format the output
            if days > 0:
                if days == 1:
                    return f"1 day ago"
                else:
                    return f"{days} days ago"
            elif hours > 0:
                if hours == 1:
                    return f"1 hour ago"
                else:
                    return f"{hours} hours ago"
            elif minutes > 0:
                if minutes == 1:
                    return f"1 minute ago"
                else:
                    return f"{minutes} minutes ago"
            else:
                return "Just now"
                
        except Exception as e:
            print(f"Error formatting time: {e}")
            return "Unknown time"
    
    async def get_latest_commit(self, repo: str) -> Optional[dict]:
        """Get the latest commit information from a GitHub repository."""
        try:
            # Parse repo and branch if specified (format: owner/repo:branch)
            if ':' in repo:
                repo_path, branch = repo.split(':', 1)
            else:
                repo_path, branch = repo, 'main'
            
            # GitHub API URL for latest commits on specific branch
            url = f"https://api.github.com/repos/{repo_path}/commits"
            params = {'sha': branch, 'per_page': 1}
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'EpochStatusBot'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            commits = response.json()
            if not commits:
                return None
                
            latest_commit = commits[0]
            
            return {
                'sha': latest_commit['sha'][:7],  # Short SHA
                'message': latest_commit['commit']['message'].split('\n')[0],  # First line only
                'author': latest_commit['commit']['author']['name'],
                'date': latest_commit['commit']['author']['date'],
                'url': latest_commit['html_url'],
                'repo': repo,
                'repo_path': repo_path,
                'branch': branch,
                'commits_url': f"https://github.com/{repo_path}/commits/{branch}"
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching commits for {repo}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {repo}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {repo}: {e}")
            return None
    
    @commands.command(name="gitcheck", help="Check recent commits on Project Epoch repositories")
    async def gitcheck_command(self, ctx):
        """Check the latest commits for Project Epoch repositories."""
        
        repos_to_check = self.default_repos
        
        # Create initial embed
        embed = discord.Embed(
            title="🔍 Project Epoch Development Status",
            description="Checking latest commits...",
            color=0x24292e  # GitHub dark color
        )
        
        message = await ctx.send(embed=embed)
        
        # Collect commit information
        commit_info = []
        for repo in repos_to_check:
            commit_data = await self.get_latest_commit(repo)
            if commit_data:
                commit_info.append(commit_data)
            else:
                commit_info.append({
                    'repo': repo,
                    'error': True
                })
        
        # Update embed with results
        if not commit_info:
            embed = discord.Embed(
                title="🔍 Project Epoch Development Status",
                description="❌ Could not fetch commit information for any repositories.",
                color=0xff0000
            )
        else:
            embed = discord.Embed(
                title="🔍 Project Epoch Development Status",
                description=f"Latest commits from {len([c for c in commit_info if not c.get('error')])} Project Epoch repositories:",
                color=0x28a745  # GitHub green
            )
            
            for commit in commit_info:
                if commit.get('error'):
                    embed.add_field(
                        name=f"❌ {commit['repo']}",
                        value="Could not fetch commit data",
                        inline=False
                    )
                else:
                    time_ago = self.format_time_ago(commit['date'])
                    
                    # Truncate long commit messages
                    message = commit['message']
                    if len(message) > 60:
                        message = message[:57] + "..."
                    
                    # Create repository display name with branch info
                    repo_display = f"{commit['repo_path']}"
                    if commit['branch'] != 'main':
                        repo_display += f" ({commit['branch']})"
                    
                    field_value = (
                        f"**Repository:** [{repo_display}]({commit['commits_url']})\n"
                        f"**Latest Commit:** [{commit['sha']}]({commit['url']})\n"
                        f"**Message:** {message}\n"
                        f"**Author:** {commit['author']}\n"
                        f"**When:** {time_ago}"
                    )
                    
                    embed.add_field(
                        name=f"📦 {repo_display}",
                        value=field_value,
                        inline=False
                    )
        
        # Add footer with check time
        embed.set_footer(
            text=f"Checked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )
        
        await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(GitCheckCog(bot))
