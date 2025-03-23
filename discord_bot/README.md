# Discord Assistant Bot

A versatile Discord bot that combines natural conversation with practical productivity tools to help users stay organized and engaged.

## Features

### Conversational Assistant
- Natural, casual conversation with users
- Adaptive responses based on user's mood and preferences
- Resource sharing for various topics
- User profiles to customize interactions

### Productivity Tools
- **Pomodoro Timer**: Stay focused with customizable Pomodoro sessions
- **Alarm System**: Set reminders for important tasks or events
- **To-Do List**: Manage your tasks directly in Discord
- **Progress Tracking**: See your productivity data over time

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- pip (Python package installer)

### Installation

1. Clone or download this repository.

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the bot:
   - Open `config.json` and add your Discord bot token
   - Customize the command prefix (default is `!`)
   - Set your Discord user ID as the owner_id

4. Run the bot:
   ```
   python main.py
   ```

### Inviting the Bot to Your Server

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Navigate to the "OAuth2" section
4. In URL Generator, select the "bot" scope and appropriate permissions
   - Recommended permissions: Send Messages, Read Messages/View Channels, Embed Links, Attach Files, Read Message History
5. Copy and visit the generated URL to invite the bot to your server

## Usage

### General Commands
- `!help` - Display help for all commands
- `!ping` - Check if the bot is responsive

### Productivity Commands
- `!pomodoro [minutes]` - Start a Pomodoro timer (default: 25 minutes)
- `!pomodoro check` - Check remaining time in current Pomodoro
- `!pomodoro cancel` - Cancel current Pomodoro session

- `!alarm set HH:MM [message]` - Set an alarm for a specific time
- `!alarm list` - View your active alarms
- `!alarm clear [number]` - Clear all alarms or a specific one

- `!todo add <task>` - Add a task to your to-do list
- `!todo list` - View your to-do list
- `!todo complete <number>` - Mark a task as completed
- `!todo delete <number>` - Delete a task
- `!todo clear` - Clear all tasks

### Conversation Features
- `!profile` - View your user profile
- `!profile name <name>` - Set your preferred name
- `!profile mood <mood>` - Update your current mood
- `!profile status <status>` - Set your relationship status

- `!resources <topic>` - Get helpful resources on a topic

### Administrator Commands
- `!config` - View bot configuration
- `!config set <key> <value>` - Change a configuration setting
- `!config reset [key]` - Reset configuration to defaults

## Customization

### Response Customization
You can customize the bot's responses by editing the JSON files in the `data/responses` directory:
- `greetings.json` - Greeting messages
- `farewell.json` - Farewell messages
- `general.json` - General conversation responses
- `encouragement.json` - Motivational messages

### Bot Settings
Administrators can use the `!config` commands to adjust:
- `conversation_cooldown` - Seconds between conversation responses
- `respond_chance` - Likelihood of responding to non-command messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Discord.py developers
- All the contributors to the Python ecosystem 