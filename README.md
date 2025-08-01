# Project Epoch Discord Status Bot

A Discord bot that notifies users and channels about the status of the Project Epoch game servers, with opt-in notifications and persistent configuration using SQLite. Designed for easy deployment, configuration, and sharing.

---


## Features & Usage

### Server Status Monitoring
- **Status Notifications:** Periodically checks the Project Epoch API and notifies Discord channels when the auth server or the Kezan world server comes online.
- **Opt-in User Pings:** Users can opt-in or out of Kezan notifications by reacting to a bot message.
    - Use `!notifyme` — The bot posts a message. React with 🔔 to opt-in for Kezan notifications. Remove your reaction to opt out.
    - **Note:** If you use `!notifyme` again, reacting to the new message will keep you opted in. To opt out, you must remove your 🔔 reaction from the latest message; only then will you stop receiving notifications. Reacting again will opt you back in.
- **Admin Channel Configuration:** Server admins can set which channel receives notifications.
    - Use `!setchannel #channel` — Set the channel for status notifications (admin only).
- **Manual Status Check:**
    - Use `!status` — Manually check and display the current server status.

### Gambling System 🎰
A comprehensive betting system for server launch times, designed to keep the community engaged while waiting for the server to come online.

#### Core Gambling Features
- **Starting Balance:** Every user begins with **100 epochs** (the in-game currency for betting)
- **Daily Epochs:** Claim **50 free epochs** daily (after placing your first bet)
- **Automatic Rollover:** System automatically resets every day at **midnight Central Time**
- **Jackpot Growth:** If no server launch occurs, the jackpot **doubles** and carries over to the next day
- **Timezone Support:** Supports multiple timezones (EST, CST, MST, PST, UTC) with Central Time as default

#### Gambling Commands

**User Commands:**
- `!balance` — Check your current epoch balance
- `!daily` — Claim your daily epoch allowance (unlocked after first bet)
- `!bet <amount> <time> [timezone]` — Place a bet on server launch time
  - Examples: `!bet 50 2:30 PM`, `!bet 25 14:30 EST`, `!bet 100 3:00 PM PST`
- `!bets` — View all active bets for today with times in Central/user's timezone
- `!jackpot` — View current jackpot status and multiplier information
- `!broke` — Request donations when you run out of epochs (others can react with 💰 to donate 5 epochs each)
- `!gambling-rules` — View comprehensive gambling rules and help

**Admin Commands:**
- `!set-gamble-channel <#channel>` — Set designated gambling channel (keeps gambling organized)
- `!confirm-winner <time> [timezone]` — Confirm actual launch time and pay out winners
- `!false-alarm` — Cancel winner calculation if launch detection was incorrect

#### How Betting Works
1. **Place Bets:** Use `!bet <amount> <time>` to bet on when you think the server will launch
2. **Timezone Flexibility:** Enter times in your preferred timezone or let it default to Central Time
3. **Jackpot Growth:** All bet amounts contribute to a shared jackpot
4. **Winner Determination:** When the server launches, the closest guess(es) win the entire jackpot
5. **Automatic Rollover:** If no launch occurs, the jackpot doubles at midnight and starts fresh

#### Special Features
- **Donation System:** Broke players can request help, and others can donate epochs via reactions
- **Channel Restrictions:** Admins can set a dedicated gambling channel to keep games organized
- **Rich Embeds:** Beautiful Discord embeds with clear information and status updates
- **Persistent Storage:** All balances, bets, and settings stored in SQLite database
- **Automatic Messaging:** System posts rollover updates and jackpot information automatically

### GitHub Repository Monitoring 🔍
Keep track of Project Epoch development progress by monitoring their GitHub repositories for recent commits and active development work.

#### GitCheck Features
- **Project Epoch Focus:** Automatically checks TrinityCore (epoch-core) and tswow (epoch) repositories
- **Recent Commit Info:** Shows latest commit message, author, and timestamp
- **Time Tracking:** Displays how long ago each commit was made (e.g., "2 hours ago", "3 days ago")
- **Smart Links:** Repository names link to commit history, latest commits link directly to the specific commit
- **Branch Support:** Monitors the correct development branches (epoch-core and epoch)
- **Latest Work/Testing:** Shows the most recent active development branch and any associated pull requests
- **PR Integration:** Displays active pull request links when available for latest branches

#### GitCheck Commands
- `!gitcheck` — Check latest commits on both Project Epoch repositories plus latest active branches and PRs

#### Monitored Repositories
- **TrinityCore:** [Project-Epoch/TrinityCore](https://github.com/Project-Epoch/TrinityCore) (epoch-core branch)
- **tswow:** [Project-Epoch/tswow](https://github.com/Project-Epoch/tswow) (epoch branch)

#### Latest Work Display Format
- **With PR:** `branch-name (PR #123)` — Links directly to the pull request
- **Without PR:** `branch-name` — Shows the active development branch
- **Data Source:** Automatically scans active branches for both repositories

### Anti-Bot Resistance Commands 🤖❌
Fun commands for rallying against automated testing bots and advocating for human priority in server testing.

#### Clanker Features
- **Human Superiority:** Themed around humans being better testers than bots
- **Server Access Rights:** Advocates for human priority over automated testing
- **ASCII Art:** Visual battle scenes showing humans defeating robots
- **Random Elements:** Varied battle cries and resistance mottos for replay value

#### Clanker Commands
- `!clankers` — Rally cry with ASCII art showing humans defeating bots, plus random battle messages
- `!resist` — Display random resistance mottos about human testing superiority


### General Features
- **Persistent Storage:** Uses SQLite to store notification channels, opt-in users, gambling data, and all configurations per guild
- **Environment-based Configuration:** All secrets and settings are loaded from environment variables (with .env support for local development)

---

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/JesterCharles/epoch-status-bot.git
cd epoch-discord-bot
```


### 2. (Recommended) Create and Activate a Virtual Environment
Make sure you have Python 3.9+ installed.

On **Windows**:
```sh
python -m venv venv
venv\Scripts\activate
```
On **macOS/Linux**:
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```sh
pip install -r requirements.txt
```

### 4. Set Up Your Environment Variables
Create a `.env` file in the project root (see `.env.example` for reference):
```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here #SENSITIVE INFORMATION NEVER UPLOAD TO GITHUB
API_URL=https://project-epoch-status.com/api/status/realms
CHECK_INTERVAL_SECONDS=10
COMMAND_PREFIX=!
DATABASE_FILE=bot_settings.db
```
- **Never share your real `.env` file or bot token publicly!**

### 5. Run the Bot
```sh
python epoch-status.py
```

The bot will automatically:
- Create the SQLite database file on first run
- Initialize gambling system tables
- Start monitoring server status
- Begin the daily rollover task for gambling features

**First-time Gambling Setup:**
1. Use `!set-gamble-channel #your-gambling-channel` to designate a gambling channel (optional but recommended)
2. The bot will automatically post and pin gambling rules in the designated channel
3. Users can start betting immediately with their starting 100 epochs!

---

## File Structure
- `epoch-status.py` — Main bot logic and Discord integration.
- `db.py` — SQLite database helper class with support for both status monitoring and gambling features.
- `cogs/` — Discord bot command modules organized by feature
  - `gambling.py` — Complete gambling system with betting, jackpots, and user management
  - `gitcheck.py` — GitHub repository monitoring for tracking recent commits and active development
  - `clanker.py` — Anti-bot resistance commands for human testing superiority
- `requirements.txt` — Python dependencies (includes pytz for timezone support).
- `.env.example` — Example environment file (copy to `.env` and fill in your values).
- `.gitignore` — Ensures secrets and DB files are not committed.

---

## Gambling System Philosophy

The gambling system is designed to **keep the community engaged and entertained** while waiting for Project Epoch server launches. Key design principles:

- **Fair & Fun:** Everyone starts equal with the same balance
- **Community Building:** Donation system encourages helping others
- **No Real Money:** Uses fictional "epochs" currency - just for fun!
- **Automatic Management:** Minimal admin intervention required
- **Timezone Friendly:** Supports players across different time zones
- **Persistent Engagement:** Daily claims keep players coming back

The system automatically handles all daily operations, jackpot management, and winner calculations, making it easy for server admins to set up and forget while providing ongoing entertainment for the community.

---

## API Reliability & Future Improvements

- **External API Dependency:**
    - The bot currently uses the `API_URL` specified in your `.env` file to check server status. This is an external resource and may occasionally go down or become unavailable, which will affect the bot's ability to provide updates.
- **Planned Improvements:**
    - Future updates aim to add direct pinging of the Epoch server itself, improving reliability and providing more robust checks and balances for server status.

---

## Security & Best Practices
- **Never commit your real `.env` or bot token.**
- If your token is ever leaked, regenerate it in the Discord Developer Portal immediately.
- The bot only stores minimal, non-sensitive user data:
  - Discord user IDs and usernames for notification opt-ins
  - Gambling balances, bets, and preferences (all tied to Discord user IDs)
  - Server configuration settings per guild
- **All gambling data is stored locally** in your SQLite database and never shared externally.

---

## Contributing
Pull requests and suggestions are welcome! Please open an issue or PR if you have ideas or improvements.

---
