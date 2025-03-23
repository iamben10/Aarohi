import discord
from discord.ext import commands
import os
import json
import logging
from datetime import datetime
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord_bot")

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    logger.error("Config file not found. Please create a config.json file.")
    exit(1)

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# COMPLETELY DISABLE DEFAULT HELP COMMAND
bot = commands.Bot(command_prefix=config['prefix'], intents=intents, help_command=None)

# Event: Bot is ready
@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')
    # Set start time for uptime tracking
    bot.start_time = datetime.utcnow()
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name=f"{config['prefix']}help"
    ))
    
    # Load cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded extension: {filename}')
            except Exception as e:
                logger.error(f'Failed to load extension {filename}: {e}')
    
    logger.info("Bot is fully ready!")

# Custom help handler - intercepts before any command processing
@bot.event
async def on_message(message):
    # Don't respond to bot messages
    if message.author.bot:
        return
    
    # CRITICAL: Special handling for help command
    # This intercepts ALL help messages before they reach any other handler
    if message.content.strip().lower() in [f"{config['prefix']}help", f"{config['prefix']}help "]:
        embed = discord.Embed(
            title="Aarohi Commands",
            description="Hey! I'm Aarohi, here to help you stay productive and have some fun.",
            color=discord.Color.purple()
        )

        # Basic Commands
        embed.add_field(
            name="📌 Basic Commands",
            value=(
                f"`{config['prefix']}ping` - Check if I'm online\n"
                f"`{config['prefix']}help` - Display this help message"
            ),
            inline=False
        )

        # Productivity Tools
        embed.add_field(
            name="⏱️ Productivity Tools",
            value=(
                f"`{config['prefix']}pomodoro` - Start a focus session\n"
                f"`{config['prefix']}todo` - Manage your to-do list\n"
                f"`{config['prefix']}alarm` - Set or view alarms\n"
                f"`{config['prefix']}focus` - Enter distraction-free mode"
            ),
            inline=False
        )

        # Personalization
        embed.add_field(
            name="✨ Personalization",
            value=(
                f"`{config['prefix']}profile` - View or update your profile\n"
                f"`{config['prefix']}mood` - Track your emotional state\n"
                f"`{config['prefix']}resources` - Get helpful resources\n"
                f"`{config['prefix']}quote` - Get an inspirational quote"
            ),
            inline=False
        )

        # Footer
        embed.set_footer(text=f"Type {config['prefix']}help <command> for more details")

        # Send ONLY this embed, nothing else
        await message.channel.send(embed=embed)
        return  # CRITICAL: Don't process this message any further
    
    # For all other messages, process commands as normal
    await bot.process_commands(message)

# Simple ping command to check latency
@bot.command(name="ping")
async def ping(ctx):
    # Calculate latency
    latency = round(bot.latency * 1000)
    
    # Create a simple response
    embed = discord.Embed(
        title="Pong! 🏓",
        description=f"Response time: **{latency}ms**",
        color=discord.Color.green()
    )
    
    # Send the response
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(config['token'], log_handler=None) 