import discord
from discord.ext import commands
import requests
import json
from datetime import datetime, timezone
from typing import Optional
import asyncio

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

    async def get_latest_branch_and_pr(self, repo_path: str) -> Optional[dict]:
        """Get the latest active branch and its PR status for a repository."""
        try:
            # Remove branch info if present (e.g., "Project-Epoch/TrinityCore:epoch-core" -> "Project-Epoch/TrinityCore")
            if ':' in repo_path:
                repo_path = repo_path.split(':', 1)[0]
            
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Get the active branches page
            branches_url = f"https://github.com/{repo_path}/branches/active"
            response = requests.get(branches_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML to find branch and PR information from the table
            html_content = response.text
            
            import re
            
            # Look for table rows that contain branch information
            # The active branches table has specific patterns for branch names and PR links
            
            # Find branch links and their associated PR information
            # Pattern for branch name in the table
            branch_pattern = r'<a[^>]*href="/' + re.escape(repo_path) + r'/tree/([^"]+)"[^>]*>([^<]+)</a>'
            branch_matches = re.findall(branch_pattern, html_content)
            
            if not branch_matches:
                return None
            
            # Find the first non-main/master branch
            target_branch = None
            for branch_match in branch_matches:
                branch_name = branch_match[0]
                if branch_name not in ['main', 'master']:
                    target_branch = branch_name
                    break
            
            if not target_branch:
                return None
            
            # Look for PR information in the same table row
            # PR links appear as "Pull request #number" in the table
            pr_pattern = r'<a[^>]*href="/' + re.escape(repo_path) + r'/pull/(\d+)"[^>]*>.*?#(\d+)[^<]*</a>'
            pr_matches = re.findall(pr_pattern, html_content)
            
            # Also look for PR titles - they appear near the PR links
            pr_title_pattern = r'<a[^>]*href="/' + re.escape(repo_path) + r'/pull/\d+"[^>]*title="([^"]*)"'
            pr_title_matches = re.findall(pr_title_pattern, html_content)
            
            pr_info = None
            if pr_matches:
                # Get the first PR that matches (should be for our target branch)
                pr_number = pr_matches[0][1]
                pr_title = pr_title_matches[0] if pr_title_matches else f"Pull Request #{pr_number}"
                pr_info = {
                    'number': int(pr_number),
                    'title': pr_title,
                    'url': f"https://github.com/{repo_path}/pull/{pr_number}"
                }
            
            return {
                'branch_name': target_branch,
                'branch_url': f"https://github.com/{repo_path}/tree/{target_branch}",
                'pr': pr_info
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching branch info for {repo_path}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing branch JSON for {repo_path}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching branch info for {repo_path}: {e}")
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
        for i, repo in enumerate(repos_to_check):
            if i > 0:  # Add delay between repositories
                await asyncio.sleep(0.2)  # 200ms delay between repo checks
                
            commit_data = await self.get_latest_commit(repo)
            if commit_data:
                # Also get latest branch and PR info (with additional delay)
                await asyncio.sleep(0.1)
                branch_info = await self.get_latest_branch_and_pr(commit_data['repo_path'])
                commit_data['branch_info'] = branch_info
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
                    commit_message = commit['message']
                    if len(commit_message) > 60:
                        commit_message = commit_message[:57] + "..."
                    
                    # Create repository display name with branch info
                    repo_display = f"{commit['repo_path']}"
                    if commit['branch'] != 'main':
                        repo_display += f" ({commit['branch']})"
                    
                    field_value = (
                        f"**Repository:** [{repo_display}]({commit['commits_url']})\n"
                        f"**Latest Commit:** [{commit['sha']}]({commit['url']})\n"
                        f"**Message:** {commit_message}\n"
                        f"**Author:** {commit['author']}\n"
                        f"**When:** {time_ago}"
                    )
                    
                    # Add latest branch and PR info if available
                    if commit.get('branch_info'):
                        branch_info = commit['branch_info']
                        # Create clickable branch name link
                        branch_text = f"[{branch_info['branch_name']}]({branch_info['branch_url']})"
                        
                        if branch_info['pr']:
                            pr = branch_info['pr']
                            branch_text += f" ([PR #{pr['number']}]({pr['url']}))"
                        
                        field_value += f"\n**Latest Branch:** {branch_text}"
                    
                    embed.add_field(
                        name=f"📦 {repo_display}",
                        value=field_value,
                        inline=True
                    )
            
            # Add empty field to force side-by-side layout for 2 repositories
            if len([c for c in commit_info if not c.get('error')]) == 2:
                embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # Add footer with check time
        embed.set_footer(
            text=f"Checked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )
        
        await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(GitCheckCog(bot))
