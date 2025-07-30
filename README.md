# Project Epoch Discord Status Bot

A Discord bot that notifies users and channels about the status of the Project Epoch game servers, with opt-in notifications and persistent configuration using SQLite. Designed for easy deployment, configuration, and sharing.

---


## Features & Usage

- **Status Notifications:** Periodically checks the Project Epoch API and notifies Discord channels when the auth server or the Kezan world server comes online.
- **Opt-in User Pings:** Users can opt-in or out of Kezan notifications by reacting to a bot message.
    - Use `!notifyme` — The bot posts a message. React with 🔔 to opt-in for Kezan notifications. Remove your reaction to opt out.
    - **Note:** If you use `!notifyme` again, reacting to the new message will keep you opted in. To opt out, you must remove your 🔔 reaction from the latest message; only then will you stop receiving notifications. Reacting again will opt you back in.
- **Admin Channel Configuration:** Server admins can set which channel receives notifications.
    - Use `!setchannel #channel` — Set the channel for status notifications (admin only).
- **Manual Status Check:**
    - Use `!status` — Manually check and display the current server status.
- **Persistent Storage:** Uses SQLite to store notification channels and opt-in users per guild. The database file will be generated for you automatically on first run.
- **Environment-based Configuration:** All secrets and settings are loaded from environment variables (with .env support for local development).

---

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/JesterCharles/epoch-discord-bot.git
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

---

## File Structure
- `epoch-status.py` — Main bot logic and Discord integration.
- `db.py` — SQLite database helper class.
- `requirements.txt` — Python dependencies.
- `.env.example` — Example environment file (copy to `.env` and fill in your values).
- `.gitignore` — Ensures secrets and DB files are not committed.

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
- The bot only stores minimal, non-sensitive user data (Discord user IDs and usernames for opt-in).

---

## Contributing
Pull requests and suggestions are welcome! Please open an issue or PR if you have ideas or improvements.

---
