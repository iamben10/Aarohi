# Aarohi Discord Bot

Aarohi is a productivity and utility Discord bot that helps users stay organized and focused. It includes features for productivity tracking, timers, reminders, and more.

## Features

- **Channel Restriction:** Bot only responds in a specific channel
- **Pomodoro Timer:** Track focused work sessions
- **Alarms & Reminders:** Set alarms with custom messages
- **Productivity Points:** Earn points for completed focus sessions
- **To-Do Management:** Manage your tasks within Discord
- **Timezone Support:** Set your timezone for accurate timing

## Getting Started

1. Clone this repository
2. Copy `config.json.template` to `config.json` and add your Discord bot token
3. Install dependencies: `pip install discord.py flask pytz pickle-mixin`
4. Run the bot using one of the launcher scripts:
   - `RUN_AAROHI.bat` - Standard launcher
   - `FIXED_RUN_AAROHI.bat` - Enhanced launcher with better error handling
   - `START_RESTRICTED_AAROHI.bat` - Launcher that emphasizes channel restriction

## Bot Commands

- `!help` - Display available commands
- `!ping` - Check if the bot is online
- `!pomodoro [minutes]` - Start a Pomodoro timer
- `!alarm HH:MM message` - Set an alarm
- `!settimezone timezone` - Set your timezone
- `!points` - View your productivity points
- `!leaderboard` - See the productivity rankings

## Channel Restriction

The bot is configured to only respond in a specific Discord channel (ID: 1353429400460198032). You can modify this by changing the `ALLOWED_CHANNEL_ID` value in `standalone_bot.py`.

## Verification

Run `verify_bot.py` to confirm that the channel restriction is properly configured. 