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

# Event: Message received
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
                f"`{config['prefix']}ping` - Check if I'm online
"
                f"`{config['prefix']}help` - Display this help message"
            ),
            inline=False
        )

        # Productivity Tools
        embed.add_field(
            name="⏱️ Productivity Tools",
            value=(
                f"`{config['prefix']}pomodoro` - Start a focus session
"
                f"`{config['prefix']}todo` - Manage your to-do list
"
                f"`{config['prefix']}alarm` - Set or view alarms
"
                f"`{config['prefix']}focus` - Enter distraction-free mode"
            ),
            inline=False
        )

        # Personalization
        embed.add_field(
            name="✨ Personalization",
            value=(
                f"`{config['prefix']}profile` - View or update your profile
"
                f"`{config['prefix']}mood` - Track your emotional state
"
                f"`{config['prefix']}resources` - Get helpful resources
"
                f"`{config['prefix']}quote` - Get an inspirational quote"
            ),
            inline=False
        )

        # Footer
        embed.set_footer(text=f"Type {config['prefix']}help <command> for more details")

        # Send ONLY this embed, nothing else
        await message.channel.send(embed=embed)
        return  # CRITICAL: Don't process this message any further
    elif message.content.strip().lower().startswith(f"{config['prefix']}help "):
        cmd = message.content.strip().split(" ")[1]
        await message.channel.send(f"I don't have specific help for `{cmd}`. Try `{config['prefix']}help` to see all available commands.")
        return
    
    # For all other messages, process commands as normal
    await bot.process_commands(message)
    
    # If not a command, process as a conversation (to be implemented in conversation cog)

# Simple ping command to check latency
@bot.command(name="ping", help="Check the bot's response time")
async def ping(ctx):
    # Calculate latency
    latency = round(bot.latency * 1000)
    
    # Determine response based on latency
    if latency < 50:
        quality = "Lightning fast"
        emoji = "⚡"
        color = discord.Color.green()
    elif latency < 100:
        quality = "Very good"
        emoji = "🚀"
        color = discord.Color.blue()
    elif latency < 200:
        quality = "Good"
        emoji = "👍"
        color = discord.Color.gold()
    elif latency < 400:
        quality = "Acceptable"
        emoji = "🙂"
        color = discord.Color.orange()
    else:
        quality = "Slow"
        emoji = "🐢"
        color = discord.Color.red()
    
    # Create a fun response
    responses = [
        f"Pong! {emoji}",
        f"I'm here! {emoji}",
        f"At your service! {emoji}",
        f"Ready to help! {emoji}",
        f"Hello there! {emoji}"
    ]
    
    # Create an embed for richer display
    embed = discord.Embed(
        title=random.choice(responses),
        description=f"Response time: **{latency}ms** ({quality})",
        color=color,
        timestamp=datetime.utcnow()
    )
    
    # Add uptime if we have it
    if hasattr(bot, 'start_time'):
        uptime = datetime.utcnow() - bot.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        if days:
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours:
            uptime_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes:
            uptime_str = f"{minutes}m {seconds}s"
        else:
            uptime_str = f"{seconds}s"
            
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
    
    # Add server count
    embed.add_field(name="Serving", value=f"{len(bot.guilds)} servers", inline=True)
    
    # Add a footer
    tips = [
        "Try !help to see all commands!",
        "Use !profile to customize your experience!",
        "Need a productivity boost? Try !pomodoro!",
        "Stay organized with !todo",
        "Need inspiration? Try !quote"
    ]
    embed.set_footer(text=random.choice(tips))
    
    # Send the response
    await ctx.send(embed=embed)

# Simple help command using the standard decorator

    else:
        # Command-specific help
        await ctx.send(f"I don't have specific help for `{command}`. Try `!help` to see all available commands.")

# Run the bot
if __name__ == "__main__":
    bot.run(config['token'], log_handler=None) 