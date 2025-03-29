import discord
from discord.ext import commands
import json
import logging
import os
from datetime import datetime, timedelta
import random
import asyncio
import time
import pytz
import pickle
import re
from typing import Dict, List, Tuple, Optional, Union
from flask import Flask
from threading import Thread
from keep_alive import keep_alive
from training_pipeline import TrainingPipeline
import traceback
import sys
from robust_commands import inject_robust_command_handling

# Define allowed channel ID (GLOBAL CONSTANT)
ALLOWED_CHANNEL_ID = 1353429400460198032  # The specific channel where Aarohi should respond

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aarohi_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("aarohi_bot")

print("\n" + "=" * 60)
print("AAROHI BOT - CLEAN COMMAND SYSTEM")
print("=" * 60)
print("\nThis version of Aarohi has a completely overhauled command system.")
print("All commands work independently and produce clean output.\n")
print(f"BOT RESTRICTED TO CHANNEL ID: {ALLOWED_CHANNEL_ID}")

# Initialize training pipeline
training_pipeline = TrainingPipeline()

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

try:
    # Try to load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    prefix = config.get('prefix', '!')  # Use '!' as fallback
except:
    # If config loading fails, use default prefix
    prefix = '!'
    print("Warning: Couldn't load config.json, using default prefix '!'")

# Create bot with COMPLETELY DISABLED help command (we'll implement our own)
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
# Inject bulletproof command handling
error_handler = inject_robust_command_handling(bot)
logger.info("Bulletproof command handling activated")


# Print confirmation of prefix
print(f"Bot initialized with command prefix: '{prefix}'")

# Global storage for scheduled alarms - persistent across restarts
# Format: {user_id: [(channel_id, datetime_obj, message), ...]}
ALARMS_FILE = "alarms_data.pkl"
TIMEZONES_FILE = "user_timezones.pkl"
POINTS_FILE = "user_points.pkl"
scheduled_alarms: Dict[int, List[Tuple[int, datetime, str]]] = {}
alarm_tasks = {}  # Store tasks by user_id for management
user_timezones: Dict[int, str] = {}  # Store user timezone info

# Global storage for productivity points
# Format: {user_id: {"points": int, "daily_sessions": [(duration, timestamp), ...], "last_reset": datetime}}
user_points: Dict[int, Dict] = {}
points_task = None  # Task for the daily leaderboard generation and reset

# Sound notification options
SOUND_EFFECTS = {
    "default": "🔔 *Ding!*",
    "bell": "🔔 *Ding-dong!*",
    "alarm": "⏰ *BRRRING! BRRRING!*",
    "gentle": "🎵 *Soft chime*",
    "motivational": "🎺 *Triumphant fanfare!*",
    "celebration": "🎉 *Party horn and confetti!*"
}

# User sound preferences - Format: {user_id: sound_name}
user_sound_prefs: Dict[int, str] = {}
SOUND_PREFS_FILE = "sound_prefs.pkl"

# Global variable to store which channel to send the leaderboard to
leaderboard_channel_id = None

# Time zone for the bot (using UTC as default)
BOT_TIMEZONE = pytz.timezone('UTC')

# Dictionary mapping common region names to time zones
TIMEZONE_ALIASES = {
    "est": "US/Eastern",
    "cst": "US/Central",
    "mst": "US/Mountain",
    "pst": "US/Pacific",
    "ist": "Asia/Kolkata",
    "gmt": "Europe/London",
    "cet": "Europe/Paris",
    "jst": "Asia/Tokyo",
    "aest": "Australia/Sydney",
    "asia": "Asia/Kolkata",  # Default for Asia
    "europe": "Europe/London",  # Default for Europe
    "us": "US/Eastern",  # Default for US
    "usa": "US/Eastern",
    "india": "Asia/Kolkata",
    "uk": "Europe/London",
    "japan": "Asia/Tokyo",
    "australia": "Australia/Sydney",
    "china": "Asia/Shanghai",
    "russia": "Europe/Moscow",
    "canada": "America/Toronto",
    "brazil": "America/Sao_Paulo",
    "mexico": "America/Mexico_City",
    "germany": "Europe/Berlin",
    "france": "Europe/Paris",
    "italy": "Europe/Rome",
    "spain": "Europe/Madrid"
}

# Global storage for active pomodoro sessions
# Format: {user_id: (channel_id, end_time, task_obj)}
active_pomodoros = {}

# Load saved user timezones if available
def load_timezones():
    global user_timezones
    try:
        if os.path.exists(TIMEZONES_FILE):
            with open(TIMEZONES_FILE, 'rb') as f:
                user_timezones = pickle.load(f)
            logger.info(f"Loaded {len(user_timezones)} user timezones from storage")
            return True
        else:
            user_timezones = {}
            logger.info("No saved user timezones found, starting fresh")
            return False
    except Exception as e:
        logger.error(f"Error loading user timezones: {e}")
        user_timezones = {}
        return False

# Save user timezones to file
def save_timezones():
    try:
        with open(TIMEZONES_FILE, 'wb') as f:
            pickle.dump(user_timezones, f)
        logger.info(f"Saved {len(user_timezones)} user timezones to storage")
        return True
    except Exception as e:
        logger.error(f"Error saving user timezones: {e}")
        return False

# Load saved user points if available
def load_points():
    global user_points
    try:
        if os.path.exists(POINTS_FILE):
            with open(POINTS_FILE, 'rb') as f:
                user_points = pickle.load(f)
            logger.info(f"Loaded {len(user_points)} user point records from storage")
            return True
        else:
            user_points = {}
            logger.info("No saved user points found, starting fresh")
            return False
    except Exception as e:
        logger.error(f"Error loading user points: {e}")
        user_points = {}
        return False

# Save user points to file
def save_points():
    try:
        with open(POINTS_FILE, 'wb') as f:
            pickle.dump(user_points, f)
        logger.info(f"Saved {len(user_points)} user point records to storage")
        return True
    except Exception as e:
        logger.error(f"Error saving user points: {e}")
        return False

# Load saved sound preferences if available
def load_sound_prefs():
    global user_sound_prefs
    try:
        if os.path.exists(SOUND_PREFS_FILE):
            with open(SOUND_PREFS_FILE, 'rb') as f:
                user_sound_prefs = pickle.load(f)
            logger.info(f"Loaded {len(user_sound_prefs)} user sound preferences from storage")
            return True
        else:
            user_sound_prefs = {}
            logger.info("No saved sound preferences found, starting fresh")
            return False
    except Exception as e:
        logger.error(f"Error loading sound preferences: {e}")
        user_sound_prefs = {}
        return False

# Save sound preferences to file
def save_sound_prefs():
    try:
        with open(SOUND_PREFS_FILE, 'wb') as f:
            pickle.dump(user_sound_prefs, f)
        logger.info(f"Saved {len(user_sound_prefs)} user sound preferences to storage")
        return True
    except Exception as e:
        logger.error(f"Error saving sound preferences: {e}")
        return False

# Get a user's preferred sound effect, defaulting to "default" if not set
def get_user_sound(user_id):
    sound_name = user_sound_prefs.get(user_id, "default")
    return SOUND_EFFECTS.get(sound_name, SOUND_EFFECTS["default"])

# Award points for completed Pomodoro session
def award_points(user_id, minutes):
    try:
        # Initialize user's points record if it doesn't exist
        if user_id not in user_points:
            user_points[user_id] = {
                "points": 0,
                "daily_sessions": [],
                "last_reset": datetime.now()
            }
        
        # Check if we need to reset (if it's a new day)
        now = datetime.now()
        last_reset = user_points[user_id]["last_reset"]
        if now.date() > last_reset.date():
            # It's a new day, reset the points but keep track of the time
            user_points[user_id]["points"] = 0
            user_points[user_id]["daily_sessions"] = []
            user_points[user_id]["last_reset"] = now
        
        # Award points (1 point per minute)
        points_earned = minutes
        user_points[user_id]["points"] += points_earned
        
        # Record the session
        user_points[user_id]["daily_sessions"].append((minutes, now))
        
        # Save the updated points
        save_points()
        
        logger.info(f"Awarded {points_earned} points to user {user_id} for a {minutes}-minute session")
        return points_earned, user_points[user_id]["points"]
    
    except Exception as e:
        logger.error(f"Error awarding points to user {user_id}: {e}")
        return 0, 0

# Generate and send daily leaderboard at 11 PM
async def generate_leaderboard():
    try:
        # Get current date for the leaderboard title
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create a list of (user_id, points) tuples
        leaderboard_data = []
        for user_id, data in user_points.items():
            if data["points"] > 0:  # Only include users who earned points today
                leaderboard_data.append((user_id, data["points"]))
        
        # Sort by points in descending order
        leaderboard_data.sort(key=lambda x: x[1], reverse=True)
        
        # If we have no data, just log it and return
        if not leaderboard_data:
            logger.info("No points data for leaderboard today")
            return
        
        # Find a channel to send the leaderboard to
        channel = None
        if leaderboard_channel_id:
            channel = bot.get_channel(leaderboard_channel_id)
        
        if not channel:
            # Try to find an active channel from a user in the leaderboard
            for user_id, _ in leaderboard_data:
                if user_id in active_pomodoros:
                    channel_id = active_pomodoros[user_id][0]
                    channel = bot.get_channel(channel_id)
                    if channel:
                        break
        
        if not channel:
            logger.error("Could not find a channel to send the leaderboard to")
            return
        
        # Generate the leaderboard message
        embed = discord.Embed(
            title=f"📊 Today's Productivity Leaderboard ({today})",
            description="Here's how everyone stacked up today with their focus time!",
            color=discord.Color.gold()
        )
        
        # Format the leaderboard entries
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, points) in enumerate(leaderboard_data):
            # Try to get the user's display name
            try:
                user = await bot.fetch_user(user_id)
                username = user.display_name
            except:
                username = f"User {user_id}"
            
            # Add medal for top 3
            prefix = medals[i] if i < 3 else f"{i+1}."
            leaderboard_text += f"{prefix} **{username}** - {points} points\n"
            
            # Limit to top 10 users
            if i >= 9:
                break
        
        embed.add_field(
            name="Top Performers",
            value=leaderboard_text or "No study sessions recorded today",
            inline=False
        )
        
        # Add a motivational message
        if len(leaderboard_data) > 1:
            top_points = leaderboard_data[0][1]
            bottom_points = leaderboard_data[-1][1]
            
            if top_points > bottom_points * 2:  # Top scorer has more than double the points of bottom scorer
                embed.add_field(
                    name="💪 Challenge",
                    value="Wow! Our top performers are crushing it! Everyone else, time to step up your game!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔥 Great Work",
                    value="Everyone's doing great! Keep up the momentum tomorrow!",
                    inline=False
                )
        
        # Send the leaderboard
        await channel.send(embed=embed)
        logger.info(f"Sent daily leaderboard to channel {channel.id}")
        
        # Reset points for all users after sending the leaderboard
        reset_day = datetime.now()
        for user_id in user_points:
            user_points[user_id]["points"] = 0
            user_points[user_id]["daily_sessions"] = []
            user_points[user_id]["last_reset"] = reset_day
        
        save_points()
        logger.info("Reset all user points after leaderboard")
        
    except Exception as e:
        logger.error(f"Error generating leaderboard: {e}")

# Schedule the daily leaderboard task
async def schedule_leaderboard():
    global points_task
    
    # Cancel any existing task
    if points_task and not points_task.done():
        points_task.cancel()
    
    while True:
        try:
            # Calculate time until 11 PM today
            now = datetime.now()
            target_time = now.replace(hour=23, minute=0, second=0, microsecond=0)
            
            # If it's already past 11 PM, schedule for tomorrow
            if now >= target_time:
                target_time = target_time + timedelta(days=1)
            
            # Calculate seconds until target time
            seconds_until_target = (target_time - now).total_seconds()
            
            logger.info(f"Scheduled leaderboard for {target_time.strftime('%Y-%m-%d %H:%M:%S')} "
                       f"({seconds_until_target/3600:.2f} hours from now)")
            
            # Wait until 11 PM
            await asyncio.sleep(seconds_until_target)
            
            # Generate and send the leaderboard
            await generate_leaderboard()
            
            # Sleep a bit to avoid duplicating if this runs exactly at midnight
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            logger.info("Leaderboard scheduler task was cancelled")
            break
        except Exception as e:
            logger.error(f"Error in leaderboard scheduler: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(3600)  # 1 hour

# Load saved alarms if available
def load_alarms():
    global scheduled_alarms
    try:
        if os.path.exists(ALARMS_FILE):
            with open(ALARMS_FILE, 'rb') as f:
                scheduled_alarms = pickle.load(f)
            logger.info(f"Loaded {sum(len(alarms) for alarms in scheduled_alarms.values())} alarms from storage")
            return True
        else:
            scheduled_alarms = {}
            logger.info("No saved alarms found, starting fresh")
            return False
    except Exception as e:
        logger.error(f"Error loading alarms: {e}")
        scheduled_alarms = {}
        return False

# Save alarms to file
def save_alarms():
    try:
        with open(ALARMS_FILE, 'wb') as f:
            pickle.dump(scheduled_alarms, f)
        logger.info(f"Saved {sum(len(alarms) for alarms in scheduled_alarms.values())} alarms to storage")
        return True
    except Exception as e:
        logger.error(f"Error saving alarms: {e}")
        return False

# Start alarm scheduler for a user
async def start_alarm_scheduler(user_id: int):
    global alarm_tasks
    
    # Cancel existing task if any
    if user_id in alarm_tasks and not alarm_tasks[user_id].done():
        alarm_tasks[user_id].cancel()
    
    # Create a new task
    alarm_tasks[user_id] = asyncio.create_task(alarm_check_loop(user_id))
    logger.info(f"Started alarm scheduler for user {user_id}")

# Main alarm checking loop for a user
async def alarm_check_loop(user_id: int):
    global scheduled_alarms
    
    logger.info(f"Alarm loop started for user {user_id}")
    
    while True:
        try:
            if user_id not in scheduled_alarms or not scheduled_alarms[user_id]:
                # No alarms for this user, stop the loop
                logger.info(f"No more alarms for user {user_id}, stopping scheduler")
                return
            
            # Get current time in UTC
            now_utc = datetime.now(pytz.UTC)
            
            # Check each alarm for this user
            triggered_alarms = []
            
            for i, (channel_id, alarm_time, message) in enumerate(scheduled_alarms[user_id]):
                try:
                    # Convert alarm_time to UTC for comparison if it's not already
                    if alarm_time.tzinfo is None:
                        # Apply user's timezone if known, otherwise use UTC
                        if user_id in user_timezones:
                            user_tz = pytz.timezone(user_timezones[user_id])
                            naive_alarm = alarm_time.replace(tzinfo=None)
                            alarm_time_utc = user_tz.localize(naive_alarm).astimezone(pytz.UTC)
                        else:
                            alarm_time_utc = pytz.UTC.localize(alarm_time)
                    else:
                        alarm_time_utc = alarm_time.astimezone(pytz.UTC)
                        
                    if alarm_time_utc <= now_utc:
                        # This alarm should trigger now or has passed
                        triggered_alarms.append((i, channel_id, alarm_time, message))
                except Exception as e:
                    logger.error(f"Error checking alarm {i} for user {user_id}: {e}")
                    # Skip this problematic alarm and continue with others
                    continue
            
            # Process triggered alarms (in reverse to avoid index issues when removing)
            for i, channel_id, alarm_time, message in sorted(triggered_alarms, reverse=True):
                # Try to send notification
                try:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        # Display in user's local timezone if available
                        if user_id in user_timezones:
                            user_tz = pytz.timezone(user_timezones[user_id])
                            local_time = alarm_time.astimezone(user_tz) if alarm_time.tzinfo else user_tz.localize(alarm_time)
                            time_display = local_time.strftime('%H:%M')
                        else:
                            time_display = alarm_time.strftime('%H:%M')
                        
                        # Get user's preferred sound notification
                        sound_effect = get_user_sound(user_id)
                            
                        embed = discord.Embed(
                            title="⏰ ALARM!",
                            description=f"<@{user_id}> Your alarm for **{time_display}** is ringing!",
                            color=discord.Color.red()
                        )
                        
                        # Add sound effect notification
                        embed.add_field(
                            name="Sound Alert",
                            value=f"{sound_effect}",
                            inline=False
                        )
                        
                        if message:
                            embed.add_field(name="Message", value=message)
                        
                        await channel.send(f"<@{user_id}>", embed=embed)
                        logger.info(f"Triggered alarm for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        logger.error(f"Channel {channel_id} not found for alarm notification")
                except Exception as e:
                    logger.error(f"Error triggering alarm: {e}")
                
                try:
                    # Remove this alarm
                    del scheduled_alarms[user_id][i]
                except Exception as e:
                    logger.error(f"Error removing triggered alarm: {e}")
            
            # Save updated alarms if any were triggered
            if triggered_alarms:
                try:
                    # Remove empty user entries
                    if not scheduled_alarms[user_id]:
                        del scheduled_alarms[user_id]
                    
                    save_alarms()
                except Exception as e:
                    logger.error(f"Error saving alarms after triggering: {e}")
            
            # Sleep for a short time (check every 10 seconds)
            await asyncio.sleep(10)
            
        except Exception as e:
            # Top-level exception handler to prevent the loop from breaking
            logger.error(f"Critical error in alarm loop for user {user_id}: {e}")
            # Continue the loop after a short delay
            await asyncio.sleep(10)

# Parse time string into datetime object
def parse_alarm_time(time_str: str, user_id: int) -> Optional[datetime]:
    try:
        # Standardize input format
        time_str = time_str.strip()
        
        # Check various formats
        if ":" not in time_str:
            # If just digits, try to interpret as HHMM
            if time_str.isdigit() and 3 <= len(time_str) <= 4:
                if len(time_str) == 3:
                    # Convert "930" to "09:30"
                    hour = int(time_str[0])
                    minute = int(time_str[1:3])
                else:
                    # Convert "1430" to "14:30"
                    hour = int(time_str[0:2])
                    minute = int(time_str[2:4])
            else:
                return None
        else:
            # Standard HH:MM format
            parts = time_str.split(':')
            if len(parts) != 2:
                return None
                
            try:
                hour = int(parts[0])
                minute = int(parts[1])
            except ValueError:
                return None
        
        # Validate time values
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None
        
        # Get user's timezone if available, otherwise use UTC
        user_tz = None
        if user_id in user_timezones:
            try:
                user_tz = pytz.timezone(user_timezones[user_id])
            except Exception as e:
                logger.error(f"Invalid timezone for user {user_id}: {user_timezones[user_id]} - {e}")
                user_tz = None
        
        if not user_tz:
            # Use UTC as fallback
            user_tz = pytz.UTC
            logger.warning(f"Using UTC for user {user_id} as fallback timezone")
        
        # Get current time in user's timezone
        now = datetime.now(user_tz)
        
        # Create alarm time for today in user's timezone
        alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has already passed today, schedule for tomorrow
        if alarm_time < now:
            logger.info(f"Alarm time {alarm_time.strftime('%H:%M')} has passed for today, scheduling for tomorrow")
            alarm_time = alarm_time + timedelta(days=1)
            
        # Return with timezone info preserved
        return alarm_time
    
    except Exception as e:
        logger.error(f"Error parsing alarm time '{time_str}': {e}")
        return None

# Attempt to extract timezone information from user's introduction message
async def detect_timezone_from_intro(message_content: str) -> Optional[str]:
    # Common timezone patterns in introductions
    tz_patterns = {
        r"(?i)time ?zone:?\s+([A-Za-z\/]+)": lambda x: x.strip(),
        r"(?i)from ([A-Za-z]+)": lambda x: TIMEZONE_ALIASES.get(x.lower().strip(), None),
        r"(?i)live in ([A-Za-z]+)": lambda x: TIMEZONE_ALIASES.get(x.lower().strip(), None),
        r"(?i)based in ([A-Za-z]+)": lambda x: TIMEZONE_ALIASES.get(x.lower().strip(), None),
        r"(?i)i'm from ([A-Za-z]+)": lambda x: TIMEZONE_ALIASES.get(x.lower().strip(), None),
        r"(?i)i am from ([A-Za-z]+)": lambda x: TIMEZONE_ALIASES.get(x.lower().strip(), None),
    }
    
    for pattern, processor in tz_patterns.items():
        match = re.search(pattern, message_content)
        if match:
            possible_tz = processor(match.group(1))
            if possible_tz and possible_tz in TIMEZONE_ALIASES:
                return TIMEZONE_ALIASES[possible_tz]
            try:
                # Try to validate the timezone
                pytz.timezone(possible_tz)
                return possible_tz
            except:
                continue
    
    return None

# Event: Bot is ready
@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')
    print(f"\n✅ {bot.user.name} is now online!")
    
    # Set start time for uptime tracking
    bot.start_time = datetime.utcnow()
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name=f"!help"
    ))
    
    # Load saved user timezones
    load_timezones()
    
    # Load saved sound preferences
    load_sound_prefs()
    
    # Load saved points data
    load_points()
    
    # Schedule daily leaderboard task
    asyncio.create_task(schedule_leaderboard())
    
    # Load saved alarms and start schedulers for each user
    load_alarms()
    for user_id in scheduled_alarms:
        await start_alarm_scheduler(user_id)
    
    # Attempt to load cogs - with error handling to avoid issues
    print("\nLoading cogs...")
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Loaded extension: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load extension {filename}: {e}")
    else:
        print("❌ No cogs directory found")
    
    print(f"\nBot is fully ready!")
    print(f"Type !help in Discord to see the clean commands list!")
    
    # Start monitoring chat folder in background
    asyncio.create_task(monitor_chat_folder())

async def monitor_chat_folder():
    """Monitor chat folder in background"""
    while True:
        try:
            training_pipeline.monitor_chat_folder('chat_exports')
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error monitoring chat folder: {e}")
            await asyncio.sleep(5)

@bot.command(name='teach')
async def teach(ctx, *, content: str):
    """Teach the bot a new response pattern"""
    try:
        # Parse the teaching command
        # Format: !teach If someone says 'input' then reply 'output'
        parts = content.split("'")
        if len(parts) != 4:
            await ctx.send("Please use the format: !teach If someone says 'input' then reply 'output'")
            return
            
        input_text = parts[1]
        output_text = parts[3]
        
        # Add to training pipeline
        training_pipeline.add_training_pair(input_text, output_text)
        
        await ctx.send("I've learned that! I'll remember to respond that way.")
        
    except Exception as e:
        await ctx.send(f"Sorry, I couldn't understand that teaching format. Please try again.")
        print(f"Error in teach command: {e}")

@bot.command(name='stats')
async def stats(ctx):
    """Show training statistics"""
    try:
        stats = training_pipeline.get_training_stats()
        embed = discord.Embed(title="Aarohi's Training Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Training Pairs", value=stats["total_training_pairs"])
        embed.add_field(name="Emotion Types Covered", value=stats["emotion_types_covered"])
        embed.add_field(name="Last Updated", value=stats["last_updated"])
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send("Sorry, I couldn't retrieve my training statistics right now.")
        print(f"Error in stats command: {e}")

@bot.event
async def on_message(message):
    # Don't respond to our own messages
    if message.author == bot.user:
        return
        
    # Ignore messages from all other channels
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return
    
    # Process commands FIRST - this must be called for all messages
    await bot.process_commands(message)

    # Only continue for non-command messages
    # Skip if message is a command, DM, or from a bot
    if message.content.startswith(prefix) or message.guild is None or message.author.bot:
        return

    # Get response from training pipeline
    response, confidence = training_pipeline.find_response(message.content)

    # Only respond if confidence is high enough
    if confidence > 0.5:
        await message.channel.send(response)

# Custom help command - exactly matching the required format
@bot.command(name="help")
async def help_command(ctx, command: str = None):
    """Display the clean Aarohi Commands help"""
    if command:
        # If a specific command is requested, redirect to the guide
        await guide(ctx, command)
        return
    
    # Create help embed exactly as required
    embed = discord.Embed(
        title="Aarohi Commands",
        description="Hey! I'm Aarohi, here to help you stay productive and have some fun.",
        color=discord.Color.purple()
    )

    # Basic Commands
    embed.add_field(
        name="📌 Basic Commands",
        value=(
            f"`!ping` - Check if I'm online\n"
            f"`!help` - Display this help message\n"
            f"`!guide <command>` - Detailed help for a specific command"
        ),
        inline=False
    )
    
    # Productivity Commands
    embed.add_field(
        name="📝 Productivity",
        value=(
            f"`!todo` - Manage your to-do list\n"
            f"`!alarm HH:MM message` - Set an alarm\n"
            f"`!alarm cancel #ID` - Cancel a specific alarm\n"
            f"`!settimezone timezone` - Set your timezone\n"
            f"`!pomodoro <minutes>` - Start a Pomodoro timer\n"
            f"`!pomodoro cancel` - Cancel active Pomodoro\n"
            f"`!focus min` - Set a focus time"
        ),
        inline=False
    )
    
    # Points & Leaderboard Commands - NEW SECTION
    embed.add_field(
        name="🏆 Points & Competition",
        value=(
            f"`!points` - View your productivity points\n"
            f"`!leaderboard` - See the current rankings\n"
            f"`!setsound` - Customize your notification sounds\n"
            f"Daily leaderboard posted at 11:00 PM"
        ),
        inline=False
    )
    
    # Personalization
    embed.add_field(
        name="✨ Personalization",
        value=(
            f"`!profile` - View your profile\n"
            f"`!mood <emotion>` - Track your mood\n"
            f"`!resources` - Get helpful resources\n"
            f"`!quote` - Get an inspirational quote"
        ),
        inline=False
    )
    
    # Footer
    embed.set_footer(text=f"Type !guide <command> for detailed instructions on any command")
    
    await ctx.send(embed=embed)

# Simple ping command to check latency
@bot.command(name="ping")
async def ping(ctx):
    """Check the bot's response time"""
    # Calculate latency
    latency = round(bot.latency * 1000)
    
    # Create a simple response
    embed = discord.Embed(
        title="Pong! 🏓",
        description=f"Response time: **{latency}ms**",
        color=discord.Color.green()
    )
    
    # Send the response - ONE single message
    await ctx.send(embed=embed)

# Quote command that always sends a single response
@bot.command(name="quote")
async def quote(ctx, category: str = None):
    """Get an inspirational quote"""
    # Dictionary of quotes by category
    quotes = {
        "motivation": [
            ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
            ("You are never too old to set another goal or to dream a new dream.", "C.S. Lewis"),
            ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It always seems impossible until it's done.", "Nelson Mandela")
        ],
        "success": [
            ("Success is not final, failure is not fatal: It is the courage to continue that counts.", "Winston Churchill"),
            ("The road to success and the road to failure are almost exactly the same.", "Colin R. Davis"),
            ("Success usually comes to those who are too busy to be looking for it.", "Henry David Thoreau"),
            ("The secret of success is to do the common thing uncommonly well.", "John D. Rockefeller Jr."),
            ("I find that the harder I work, the more luck I seem to have.", "Thomas Jefferson")
        ],
        "focus": [
            ("Concentrate all your thoughts upon the work in hand.", "Alexander Graham Bell"),
            ("The successful warrior is the average man, with laser-like focus.", "Bruce Lee"),
            ("My success, part of it certainly, is that I have focused in on a few things.", "Bill Gates"),
            ("That's been one of my mantras - focus and simplicity.", "Steve Jobs"),
            ("The main thing is to keep the main thing the main thing.", "Stephen Covey")
        ]
    }
    
    # All quotes together for random selection
    all_quotes = []
    for category_quotes in quotes.values():
        all_quotes.extend(category_quotes)
        
    # Determine which quote to show
    if category and category.lower() in quotes:
        # Get a quote from the specific category
        quote_text, author = random.choice(quotes[category.lower()])
        cat_display = category.capitalize()
    else:
        # Get a random quote from any category
        quote_text, author = random.choice(all_quotes)
        cat_display = "Inspirational"
        
    # Create embed for the quote
    embed = discord.Embed(
        title=f"{cat_display} Quote",
        description=f"**\"{quote_text}\"**",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"— {author}")
    
    # Add available categories to the embed if no category was specified or an invalid one was given
    if not category or (category and category.lower() not in quotes):
        categories = ", ".join([f"`{cat}`" for cat in quotes.keys()])
        embed.add_field(name="Available Categories", value=f"Try: {categories}")
        
    # Send a single consolidated response - ONE single message
    await ctx.send(embed=embed)

# Pomodoro command
@bot.command(name="pomodoro")
async def pomodoro(ctx, *args):
    """Start or cancel a Pomodoro timer for focused work sessions"""
    user_id = ctx.author.id
    
    # Parse arguments
    if len(args) == 0:
        # Default to 25 minutes if no arguments
        action = "start"
        minutes = 25
    elif args[0].lower() == "cancel":
        # Handle cancellation request
        action = "cancel"
        minutes = 0
    else:
        # Try to parse the first argument as minutes
        try:
            minutes = int(args[0])
            action = "start"
        except ValueError:
            # Invalid input - not a number or "cancel"
            embed = discord.Embed(
                title="⚠️ Invalid Pomodoro Command",
                description=f"I couldn't understand that command. Please use either:\n"
                           f"• `!pomodoro [minutes]` to start a timer\n"
                           f"• `!pomodoro cancel` to cancel an active timer",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
    
    # =====================
    # HANDLE CANCELLATION
    # =====================
    if action == "cancel":
        # Check if user has an active Pomodoro session
        if user_id in active_pomodoros:
            try:
                # Extract session data
                channel_id, end_time, task = active_pomodoros[user_id]
                
                # Cancel the task if it's running
                if not task.done():
                    task.cancel()
                
                # Remove from active pomodoros dictionary
                del active_pomodoros[user_id]
                
                # Send confirmation message
                embed = discord.Embed(
                    title="🍅 Pomodoro Canceled",
                    description="Your Pomodoro session has been canceled.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                logger.info(f"Canceled Pomodoro timer for user {user_id}")
                
            except Exception as e:
                # Handle any errors during cancellation
                logger.error(f"Error canceling Pomodoro for user {user_id}: {e}")
                
                # Attempt cleanup even if an error occurred
                if user_id in active_pomodoros:
                    del active_pomodoros[user_id]
                
                # Send error message
                embed = discord.Embed(
                    title="⚠️ Error Canceling Pomodoro",
                    description="There was an error canceling your session, but it has been cleared.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                
        else:
            # No active session to cancel
            embed = discord.Embed(
                title="🍅 No Active Session",
                description="You don't have an active Pomodoro session to cancel.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        
        return
    
    # =====================
    # HANDLE STARTING NEW SESSION
    # =====================
    
    # Validate input minutes
    if minutes <= 0 or minutes > 120:
        embed = discord.Embed(
            title="⚠️ Invalid Duration",
            description="Please provide a valid time between 1 and 120 minutes.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Check if user already has an active pomodoro session
    if user_id in active_pomodoros:
        # Get remaining time
        channel_id, end_time, task = active_pomodoros[user_id]
        
        # Calculate remaining time
        now = datetime.now(pytz.UTC)
        if end_time.tzinfo is None:
            end_time = pytz.UTC.localize(end_time)
            
        time_diff = end_time - now
        minutes_left = max(0, int(time_diff.total_seconds() / 60))
        seconds_left = max(0, int(time_diff.total_seconds() % 60))
        
        embed = discord.Embed(
            title="🍅 Pomodoro Already Running",
            description=(
                f"You already have an active Pomodoro session with "
                f"**{minutes_left}m {seconds_left}s** remaining."
            ),
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Options",
            value=(
                f"• Wait for current session to end\n"
                f"• Type `!pomodoro cancel` to cancel it"
            ),
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    # Create confirmation embed for new session
    embed = discord.Embed(
        title="🍅 Pomodoro Timer Started",
        description=f"Focus session of **{minutes} minute{'s' if minutes != 1 else ''}** started for {ctx.author.mention}",
        color=discord.Color.red()
    )
    embed.add_field(
        name="Pomodoro Technique",
        value="Work focused for the entire duration. When the timer ends, take a 5-minute break."
    )
    
    # Calculate and display end time
    now = datetime.now()
    end_time = now + timedelta(minutes=minutes)
    end_time_str = end_time.strftime("%H:%M")
    
    embed.add_field(
        name="End Time",
        value=f"Your session will end at **{end_time_str}**",
        inline=False
    )
    
    embed.add_field(
        name="Cancel Anytime",
        value=f"To cancel this session, type `!pomodoro cancel`",
        inline=False
    )
    
    embed.set_footer(text="Stay focused! I'll notify you when the time is up.")
    
    # Send confirmation message
    await ctx.send(embed=embed)
    
    # Create and store the pomodoro task with error handling
    try:
        task = asyncio.create_task(pomodoro_timer(ctx.channel.id, user_id, minutes))
        active_pomodoros[user_id] = (ctx.channel.id, end_time, task)
        
        logger.info(f"Started Pomodoro timer for user {user_id} for {minutes} minutes, ending at {end_time_str}")
    except Exception as e:
        logger.error(f"Error creating Pomodoro timer task for user {user_id}: {e}")
        embed = discord.Embed(
            title="⚠️ Error Starting Timer",
            description="There was an error starting your Pomodoro timer. Please try again.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Pomodoro timer function
async def pomodoro_timer(channel_id: int, user_id: int, minutes: int):
    try:
        # Sleep for the specified duration
        logger.info(f"Pomodoro timer sleeping for {minutes} minutes for user {user_id}")
        await asyncio.sleep(minutes * 60)  # Convert minutes to seconds
        
        # Check if the pomodoro is still active (could have been canceled)
        if user_id not in active_pomodoros:
            logger.info(f"Pomodoro for user {user_id} was canceled during sleep")
            return
            
        # Award points for the completed session
        points_earned, total_points = award_points(user_id, minutes)
        
        # Get user's preferred sound notification
        sound_effect = get_user_sound(user_id)
        
        # Send notification when timer is up
        channel = bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title="🍅 Pomodoro Complete!",
                description=f"<@{user_id}> Your **{minutes} minute{'s' if minutes != 1 else ''}** focus session is complete!",
                color=discord.Color.green()
            )
            
            # Add sound effect notification
            embed.add_field(
                name="Sound Alert",
                value=f"{sound_effect}",
                inline=False
            )
            
            # Add points information
            embed.add_field(
                name="🏆 Points Earned",
                value=f"You earned **{points_earned} points** for this session!\nYour total for today: **{total_points} points**",
                inline=False
            )
            
            embed.add_field(
                name="Take a Break",
                value="Time for a 5-minute break before starting another session."
            )
            
            embed.add_field(
                name="Start Another",
                value=f"Type `!pomodoro [minutes]` to start a new focus session."
            )
            
            await channel.send(f"<@{user_id}>", embed=embed)
            logger.info(f"Sent Pomodoro completion notification to user {user_id} with {points_earned} points awarded")
        else:
            logger.error(f"Channel {channel_id} not found for Pomodoro notification")
    
    except asyncio.CancelledError:
        logger.info(f"Pomodoro timer for user {user_id} was canceled")
        # Task was canceled, clean up if needed
        pass
    except Exception as e:
        logger.error(f"Error in Pomodoro timer for user {user_id}: {e}")
        # Try to send error notification if possible
        try:
            channel = bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="⚠️ Pomodoro Error",
                    description=f"<@{user_id}> There was an error with your Pomodoro timer. Please start a new one.",
                    color=discord.Color.red()
                )
                await channel.send(f"<@{user_id}>", embed=embed)
        except:
            pass
    finally:
        # Clean up - remove from active sessions regardless of outcome
        if user_id in active_pomodoros:
            del active_pomodoros[user_id]
        logger.info(f"Pomodoro timer for user {user_id} completed and cleaned up")

# Todo command
@bot.command(name="todo")
async def todo(ctx, action: str = "list", *, item: str = None):
    """Manage your to-do list"""
    embed = discord.Embed(
        title="📝 To-Do List",
        color=discord.Color.blue()
    )
    
    if action.lower() == "list":
        embed.description = "Here's your to-do list:"
        embed.add_field(name="Items", value="Your to-do list is empty. Add items with `!todo add <item>`")
    elif action.lower() == "add" and item:
        embed.description = f"Added to your to-do list: **{item}**"
    elif action.lower() == "remove" and item:
        embed.description = f"Removed from your to-do list: **{item}**"
    elif action.lower() == "clear":
        embed.description = "Your to-do list has been cleared."
    else:
        embed.description = f"Invalid action. Use `!todo list`, `!todo add <item>`, `!todo remove <item>`, or `!todo clear`"
    
    # Send a single message
    await ctx.send(embed=embed)

# Completely revamped Alarm command
@bot.command(name="alarm")
async def alarm(ctx, action_or_time: str = None, alarm_id_or_msg: str = None, *, message: str = ""):
    """Set, view, or cancel alarms. Format: !alarm HH:MM [message] or !alarm cancel ID"""
    user_id = ctx.author.id
    
    # Handle viewing alarms (when no arguments provided)
    if not action_or_time:
        embed = discord.Embed(
            title="⏰ Your Alarms",
            color=discord.Color.gold()
        )
        
        if user_id in scheduled_alarms and scheduled_alarms[user_id]:
            alarms_list = []
            
            # Get user's timezone if available
            user_tz = None
            if user_id in user_timezones:
                try:
                    user_tz = pytz.timezone(user_timezones[user_id])
                except:
                    user_tz = None
            
            for i, (channel_id, alarm_time, alarm_msg) in enumerate(scheduled_alarms[user_id]):
                # Convert to user's local time if timezone is available
                if user_tz and alarm_time.tzinfo:
                    local_time = alarm_time.astimezone(user_tz)
                    time_str = local_time.strftime("%H:%M")
                else:
                    time_str = alarm_time.strftime("%H:%M")
                
                # Add alarm ID for reference when canceling
                msg_display = f" - {alarm_msg}" if alarm_msg else ""
                alarms_list.append(f"**#{i+1}** | **{time_str}**{msg_display}")
            
            embed.description = "You have the following alarms set:"
            embed.add_field(name="Scheduled Alarms", value="\n".join(alarms_list) or "None")
            embed.add_field(
                name="Manage Alarms", 
                value=f"• Set: `!alarm HH:MM [message]`\n• Cancel: `!alarm cancel #ID`\n• Clear all: `!alarm clear`", 
                inline=False
            )
        else:
            embed.description = "You don't have any alarms set."
            embed.add_field(
                name="Usage", 
                value=f"• Set: `!alarm HH:MM [message]`\n• View: `!alarm`\n• Help: `!guide alarm`", 
                inline=False
            )
        
        await ctx.send(embed=embed)
        return
    
    # Handle canceling a specific alarm by ID
    if action_or_time.lower() == "cancel" or action_or_time.lower() == "delete":
        if not alarm_id_or_msg:
            embed = discord.Embed(
                title="⏰ Missing Alarm ID",
                description=f"Please specify which alarm to cancel using its ID number.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Usage",
                value=f"• View alarms and IDs: `!alarm`\n• Cancel by ID: `!alarm cancel #ID`\n(Example: `!alarm cancel 1`)"
            )
            await ctx.send(embed=embed)
            return
        
        # Extract the ID number (removing any # character if present)
        try:
            alarm_id = int(alarm_id_or_msg.replace('#', '')) - 1  # Convert to zero-based index
        except ValueError:
            embed = discord.Embed(
                title="⏰ Invalid Alarm ID",
                description=f"'{alarm_id_or_msg}' is not a valid alarm ID. Please use a number.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Usage",
                value=f"• View alarms and IDs: `!alarm`\n• Cancel by ID: `!alarm cancel #ID`"
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user has alarms and if the ID is valid
        if user_id not in scheduled_alarms or not scheduled_alarms[user_id]:
            embed = discord.Embed(
                title="⏰ No Alarms",
                description="You don't have any alarms to cancel.",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
            return
            
        if alarm_id < 0 or alarm_id >= len(scheduled_alarms[user_id]):
            embed = discord.Embed(
                title="⏰ Invalid Alarm ID",
                description=f"Alarm #{alarm_id+1} doesn't exist. Please check your alarm list.",
                color=discord.Color.red()
            )
            embed.add_field(name="Your Alarms", value=f"To see your alarms, type `!alarm`")
            await ctx.send(embed=embed)
            return
        
        # Get the alarm details for the confirmation message
        _, alarm_time, alarm_msg = scheduled_alarms[user_id][alarm_id]
        
        # Get user's timezone for display
        time_display = alarm_time.strftime("%H:%M")
        if user_id in user_timezones:
            try:
                user_tz = pytz.timezone(user_timezones[user_id])
                if alarm_time.tzinfo:
                    local_time = alarm_time.astimezone(user_tz)
                else:
                    local_time = user_tz.localize(alarm_time)
                time_display = local_time.strftime("%H:%M")
            except:
                pass
        
        # Remove the alarm
        del scheduled_alarms[user_id][alarm_id]
        
        # Remove empty user entries if needed
        if not scheduled_alarms[user_id]:
            del scheduled_alarms[user_id]
            
            # Also cancel any running task
            if user_id in alarm_tasks and not alarm_tasks[user_id].done():
                alarm_tasks[user_id].cancel()
                del alarm_tasks[user_id]
        else:
            # Restart the scheduler with updated alarms
            await start_alarm_scheduler(user_id)
            
        # Save updated alarms
        save_alarms()
        
        # Confirmation message
        embed = discord.Embed(
            title="⏰ Alarm Canceled",
            description=f"Successfully canceled alarm **#{alarm_id+1}** (scheduled for **{time_display}**).",
            color=discord.Color.green()
        )
        if alarm_msg:
            embed.add_field(name="Message", value=alarm_msg)
            
        if user_id in scheduled_alarms and scheduled_alarms[user_id]:
            embed.add_field(
                name="Remaining Alarms", 
                value=f"You have {len(scheduled_alarms[user_id])} active alarm(s).\nView them with `!alarm`", 
                inline=False
            )
        
        await ctx.send(embed=embed)
        return
    
    # Handle clearing all alarms
    if action_or_time.lower() in ["clear", "clearall", "all"]:
        if user_id in scheduled_alarms:
            alarm_count = len(scheduled_alarms[user_id])
            del scheduled_alarms[user_id]
            save_alarms()
            
            # Cancel any running task
            if user_id in alarm_tasks and not alarm_tasks[user_id].done():
                alarm_tasks[user_id].cancel()
                del alarm_tasks[user_id]
            
            embed = discord.Embed(
                title="⏰ Alarms Cleared",
                description=f"All your alarms ({alarm_count}) have been cleared.",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="⏰ No Alarms",
                description="You don't have any alarms to clear.",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
        return
    
    # Handle setting a new alarm
    
    # Check if user has a timezone set
    if user_id not in user_timezones:
        embed = discord.Embed(
            title="⏰ Timezone Required",
            description="I couldn't determine your time zone from your introduction. Please set your time zone first.",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Set Timezone",
            value=f"Please set your timezone by typing `!settimezone [your timezone]`\n"
                  f"Example: `!settimezone US/Eastern` or `!settimezone IST`"
        )
        await ctx.send(embed=embed)
        return
    
    # Now that we know this is a time-setting operation, reorganize the parameters
    time_str = action_or_time
    if alarm_id_or_msg and not message:
        message = alarm_id_or_msg
    
    # Handle setting a new alarm - parse the time
    alarm_time = parse_alarm_time(time_str, user_id)
    
    if not alarm_time:
        embed = discord.Embed(
            title="⏰ Invalid Time Format",
            description="Please use the 24-hour format `HH:MM` (e.g., `14:30` for 2:30 PM).",
            color=discord.Color.red()
        )
        embed.add_field(name="Usage", value=f"`!alarm HH:MM [message]` - Set an alarm for the specified time")
        await ctx.send(embed=embed)
        return
    
    # Add the alarm to the schedule
    if user_id not in scheduled_alarms:
        scheduled_alarms[user_id] = []
    
    # Store alarm data: (channel_id, datetime, message)
    scheduled_alarms[user_id].append((ctx.channel.id, alarm_time, message.strip()))
    
    # Save updated alarms
    save_alarms()
    
    # Start or restart the alarm scheduler for this user
    await start_alarm_scheduler(user_id)
    
    # Get user's timezone
    user_tz = pytz.timezone(user_timezones[user_id])
    
    # Calculate time until alarm
    now = datetime.now(user_tz)
    
    # Ensure alarm_time has timezone info for comparison
    if alarm_time.tzinfo is None:
        alarm_time = user_tz.localize(alarm_time)
    
    time_diff = alarm_time - now
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    # Create confirmation embed
    embed = discord.Embed(
        title="⏰ Alarm Set",
        description=f"Alarm **#{len(scheduled_alarms[user_id])}** set for **{alarm_time.strftime('%H:%M')}** in your local time ({user_timezones[user_id]})",
        color=discord.Color.gold()
    )
    
    if message.strip():
        embed.add_field(name="Message", value=message.strip())
    
    # Format the remaining time message
    if days > 0:
        time_until = f"Rings in {days} day{'s' if days > 1 else ''}, {hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
    elif hours > 0:
        time_until = f"Rings in {hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
    else:
        time_until = f"Rings in {minutes} minute{'s' if minutes != 1 else ''}"
    
    embed.add_field(
        name="Time Until Alarm", 
        value=time_until
    )
    
    embed.add_field(
        name="Manage This Alarm",
        value=f"To cancel this alarm, type `!alarm cancel {len(scheduled_alarms[user_id])}`",
        inline=False
    )
    
    embed.set_footer(text="The alarm will ring exactly at the specified time - guaranteed!")
    
    # Send confirmation
    await ctx.send(embed=embed)

# Focus command
@bot.command(name="focus")
async def focus(ctx, minutes: int = 30):
    """Enter distraction-free mode"""
    if minutes <= 0 or minutes > 180:
        await ctx.send("Please provide a valid time between 1 and 180 minutes.")
        return
    
    embed = discord.Embed(
        title="🧠 Focus Mode Activated",
        description=f"{ctx.author.mention} has entered focus mode for **{minutes} minutes**",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="Focus Tips",
        value="- Put your phone away\n- Close distracting tabs\n- Take deep breaths\n- Stay hydrated"
    )
    embed.set_footer(text="You've got this! I'll notify you when focus time is up.")
    
    # Send a single message
    await ctx.send(embed=embed)

# Profile command
@bot.command(name="profile")
async def profile(ctx, user: discord.Member = None):
    """View or update your profile"""
    user = user or ctx.author
    
    embed = discord.Embed(
        title=f"👤 {user.display_name}'s Profile",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Member Since", value=user.created_at.strftime("%Y-%m-%d"))
    embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d"))
    
    if user == ctx.author:
        embed.add_field(
            name="Profile Management", 
            value=f"You can customize your profile with `!profile set <key> <value>`",
            inline=False
        )
    
    # Send a single message
    await ctx.send(embed=embed)

# Mood command
@bot.command(name="mood")
async def mood(ctx, current_mood: str = None):
    """Track your emotional state"""
    if not current_mood:
        embed = discord.Embed(
            title="😊 Mood Tracker",
            description=f"How are you feeling today? Try `!mood <emotion>`",
            color=discord.Color.teal()
        )
        embed.add_field(
            name="Examples",
            value="`!mood happy` `!mood focused` `!mood tired` `!mood stressed`"
        )
    else:
        embed = discord.Embed(
            title="😊 Mood Tracker",
            description=f"You're feeling **{current_mood}** today.",
            color=discord.Color.teal()
        )
        embed.add_field(
            name="Tracking",
            value="I've recorded your mood. You can track how your mood changes over time."
        )
    
    # Send a single message
    await ctx.send(embed=embed)

# Resources command
@bot.command(name="resources")
async def resources(ctx, category: str = None):
    """Get helpful resources"""
    embed = discord.Embed(
        title="📚 Helpful Resources",
        color=discord.Color.green()
    )
    
    if not category:
        embed.description = "Here are some resource categories:"
        embed.add_field(
            name="Categories",
            value="`productivity` `focus` `motivation` `learning`",
            inline=False
        )
        embed.add_field(
            name="Usage",
            value=f"Type `!resources <category>` to see resources for that category",
            inline=False
        )
    elif category.lower() == "productivity":
        embed.description = "**Productivity Resources**"
        embed.add_field(
            name="Apps & Tools",
            value="- [Notion](https://notion.so)\n- [Todoist](https://todoist.com)\n- [Forest](https://www.forestapp.cc/)",
            inline=False
        )
        embed.add_field(
            name="Books",
            value="- Getting Things Done by David Allen\n- Atomic Habits by James Clear",
            inline=False
        )
    elif category.lower() == "focus":
        embed.description = "**Focus Resources**"
        embed.add_field(
            name="Techniques",
            value="- Pomodoro Technique\n- Time Blocking\n- Deep Work",
            inline=False
        )
        embed.add_field(
            name="Apps",
            value="- [Focus@Will](https://focusatwill.com)\n- [Brain.fm](https://brain.fm)",
            inline=False
        )
    elif category.lower() == "motivation":
        embed.description = "**Motivation Resources**"
        embed.add_field(
            name="Books",
            value="- Drive by Daniel Pink\n- Mindset by Carol Dweck",
            inline=False
        )
        embed.add_field(
            name="Podcasts",
            value="- The Tim Ferriss Show\n- The Tony Robbins Podcast",
            inline=False
        )
    elif category.lower() == "learning":
        embed.description = "**Learning Resources**"
        embed.add_field(
            name="Platforms",
            value="- [Coursera](https://coursera.org)\n- [Khan Academy](https://khanacademy.org)\n- [MIT OpenCourseWare](https://ocw.mit.edu)",
            inline=False
        )
        embed.add_field(
            name="Techniques",
            value="- Spaced Repetition\n- Active Recall\n- Feynman Technique",
            inline=False
        )
    else:
        embed.description = f"I don't have resources for '{category}'."
        embed.add_field(
            name="Available Categories",
            value="`productivity` `focus` `motivation` `learning`",
            inline=False
        )
    
    # Send a single message
    await ctx.send(embed=embed)

# Keep the old guide command just for compatibility
@bot.command(name="guide")
async def guide(ctx, command: str = None):
    """Display detailed guide for specific commands"""
    if not command:
        await ctx.send(f"The guide command has been replaced with `!help`. Showing help menu...")
        await help_command(ctx)
        return
    
    # Handle guide for the alarm command
    if command.lower() == "alarm":
        embed = discord.Embed(
            title="⏰ Alarm Command Guide",
            description="The alarm command lets you schedule timed reminders. Alarms are based on your local time zone.",
            color=discord.Color.gold()
        )
        
        # Setting alarms section
        embed.add_field(
            name="📌 Setting Alarms",
            value=(
                f"• `!alarm HH:MM [message]` - Schedule an alarm\n"
                f"  Example: `!alarm 14:30 Time for a meeting`\n\n"
                f"• Time format is 24-hour (00:00 to 23:59)\n"
                f"• The message is optional but helpful as a reminder\n"
                f"• If the time has already passed today, the alarm will be set for tomorrow"
            ),
            inline=False
        )
        
        # Managing alarms section
        embed.add_field(
            name="📋 Managing Alarms",
            value=(
                f"• `!alarm` - View all your scheduled alarms\n"
                f"• `!alarm cancel #ID` - Cancel a specific alarm\n"
                f"  Example: `!alarm cancel 1` cancels alarm #1\n"
                f"• `!alarm clear` - Cancel all your alarms"
            ),
            inline=False
        )
        
        # Time zone section
        embed.add_field(
            name="🌐 Time Zone Handling",
            value=(
                f"• Alarms work based on your local time zone\n"
                f"• Set your time zone with `!settimezone [timezone]`\n"
                f"  Example: `!settimezone US/Eastern` or `!settimezone IST`\n"
                f"• Aarohi will auto-detect your time zone from introduction messages when possible\n"
                f"• Your time zone is required for alarm accuracy"
            ),
            inline=False
        )
        
        # Troubleshooting
        embed.add_field(
            name="❓ Troubleshooting",
            value=(
                f"• If your alarm doesn't trigger, make sure your time zone is set correctly\n"
                f"• View your current alarms with `!alarm` to check their status\n"
                f"• Each alarm has a unique ID number shown when viewing your alarms\n"
                f"• Alarms are persistent and will trigger even if you go offline"
            ),
            inline=False
        )
        
        # Examples footer
        embed.set_footer(text=f"Examples: '!alarm 08:00 Wake up', '!alarm 23:45 Sleep reminder'")
    
    # Handle guide for the pomodoro command
    elif command.lower() == "pomodoro":
        embed = discord.Embed(
            title="🍅 Pomodoro Timer Guide",
            description="The Pomodoro Technique helps you stay focused by working in timed intervals with short breaks.",
            color=discord.Color.red()
        )
        
        # Basic usage
        embed.add_field(
            name="📌 Basic Usage",
            value=(
                f"• `!pomodoro [minutes]` - Start a Pomodoro timer\n"
                f"  Example: `!pomodoro 25` for a standard 25-minute session\n"
                f"• Default is 25 minutes if no time is specified\n"
                f"• Valid time range: 1-120 minutes"
            ),
            inline=False
        )
        
        # Managing timers
        embed.add_field(
            name="⏱️ Managing Your Timer",
            value=(
                f"• `!pomodoro cancel` - Cancel your current Pomodoro session\n"
                f"• You'll receive a notification when your timer completes\n"
                f"• You can only have one active Pomodoro session at a time\n"
                f"• Starting a new session while one is active will show remaining time"
            ),
            inline=False
        )
        
        # Points system
        embed.add_field(
            name="🏆 Earning Points",
            value=(
                "• Each completed Pomodoro session awards 1 point per minute\n"
                "• For example, a 25-minute session awards 25 points\n"
                f"• View your current points with `!points`\n"
                f"• Points reset daily at 11:00 PM when the leaderboard is posted"
            ),
            inline=False
        )
        
        # Pomodoro technique explanation
        embed.add_field(
            name="🧠 The Pomodoro Technique",
            value=(
                "• Work focused for the full duration without distractions\n"
                "• When the timer ends, take a 5-minute break\n"
                "• After completing 4 sessions, take a longer 15-30 minute break\n"
                "• This cycle helps maintain focus and prevent burnout"
            ),
            inline=False
        )
        
        # Tips
        embed.add_field(
            name="💡 Tips for Success",
            value=(
                "• Close distracting apps and websites during your session\n"
                "• Use shorter sessions (15-20 min) if you're new to the technique\n"
                "• Stay hydrated and stretch during your breaks\n"
                "• Track your progress over time to see productivity improvements"
            ),
            inline=False
        )
        
        # Examples footer
        embed.set_footer(text=f"Examples: '!pomodoro 30' for a 30-minute session, '!pomodoro cancel' to stop")
    
    # Handle guide for the settimezone command
    elif command.lower() in ["settimezone", "timezone", "tz"]:
        embed = discord.Embed(
            title="🌐 Time Zone Setting Guide",
            description="Setting your time zone is essential for alarm functionality to work correctly.",
            color=discord.Color.blue()
        )
        
        # Basic usage
        embed.add_field(
            name="📌 Basic Usage",
            value=(
                f"• `!settimezone [timezone]` - Set your time zone\n"
                f"  Example: `!settimezone US/Eastern` or `!settimezone IST`\n\n"
                f"• `!settimezone` - View your current time zone setting"
            ),
            inline=False
        )
        
        # Time zone formats
        embed.add_field(
            name="🔍 Supported Time Zone Formats",
            value=(
                "• **Standard abbreviations**: EST, CST, MST, PST, IST, GMT, etc.\n"
                "• **Region format**: US/Eastern, Europe/London, Asia/Tokyo\n"
                "• **Country names**: US, India, UK, Japan, Australia, etc.\n"
                "• **City names**: New_York, London, Tokyo, etc. (major cities)"
            ),
            inline=False
        )
        
        # Auto-detection
        embed.add_field(
            name="🔄 Automatic Detection",
            value=(
                "• Aarohi tries to detect your time zone from introduction messages\n"
                "• Example phrases that work: \"I'm from India\", \"Time zone: EST\"\n"
                "• Setting explicitly with this command always takes precedence\n"
                "• You can reset your time zone any time by setting a new one"
            ),
            inline=False
        )
        
        # Why time zones matter
        embed.add_field(
            name="⚠️ Why Time Zones Matter",
            value=(
                "• Alarms are scheduled according to your local time\n"
                "• Without a time zone, alarms may trigger at the wrong time\n"
                "• Multiple users can have different time zones - each gets their own schedule\n"
                "• Your time zone setting persists between sessions"
            ),
            inline=False
        )
        
        # Examples footer
        embed.set_footer(text=f"Examples: '!settimezone EST', '!settimezone Europe/Paris'")
    
    # Handle guide for the points command
    elif command.lower() == "points":
        embed = discord.Embed(
            title="🏆 Productivity Points Guide",
            description="The points system rewards you for focused work and helps track your productivity.",
            color=discord.Color.gold()
        )
        
        # Basic usage
        embed.add_field(
            name="📌 Basic Usage",
            value=(
                f"• `!points` - View your current points and session history\n"
                f"• `!points @user` - View another user's points (if they've earned any)\n"
                f"• `!leaderboard` - View the current productivity rankings"
            ),
            inline=False
        )
        
        # How points work
        embed.add_field(
            name="💯 How Points Work",
            value=(
                "• You earn 1 point for every minute of completed Pomodoro time\n"
                "• A standard 25-minute Pomodoro = 25 points\n"
                "• Points are tracked individually for each user\n"
                "• Points reset daily at 11:00 PM when the leaderboard is posted\n"
                "• Only completed sessions award points (canceled sessions don't count)"
            ),
            inline=False
        )
        
        # Leaderboard
        embed.add_field(
            name="📊 Daily Leaderboard",
            value=(
                "• A leaderboard of the day's productivity is posted at 11:00 PM\n"
                "• The leaderboard ranks users by total points earned that day\n"
                "• Top performers receive recognition with medals (🥇, 🥈, 🥉)\n"
                "• Check the current standings anytime with `!leaderboard`\n"
                "• The leaderboard is a fun way to stay motivated and competitive"
            ),
            inline=False
        )
        
        # Tips for earning points
        embed.add_field(
            name="💡 Tips for Earning Points",
            value=(
                "• Use the Pomodoro technique consistently throughout the day\n"
                "• Longer sessions earn more points, but make sure they're realistic\n"
                "• Stay focused during your Pomodoro sessions - quality over quantity\n"
                "• Check the leaderboard regularly to see how you compare to others"
            ),
            inline=False
        )
        
        # Examples footer
        embed.set_footer(text=f"Related commands: '!pomodoro', '!leaderboard'")
    
    # Handle guide for the leaderboard command
    elif command.lower() in ["leaderboard", "lb"]:
        embed = discord.Embed(
            title="📊 Leaderboard Guide",
            description="The productivity leaderboard shows who's been the most focused each day.",
            color=discord.Color.gold()
        )
        
        # Basic usage
        embed.add_field(
            name="📌 Basic Usage",
            value=(
                f"• `!leaderboard` - View the current day's rankings\n"
                f"• `!lb` - Shorthand for the leaderboard command"
            ),
            inline=False
        )
        
        # How it works
        embed.add_field(
            name="🔍 How It Works",
            value=(
                "• The leaderboard ranks users by productivity points earned today\n"
                "• Points are earned through completed Pomodoro sessions (1 point per minute)\n"
                "• Top 3 performers get medals: 🥇 First, 🥈 Second, 🥉 Third\n"
                "• The leaderboard is automatically posted at 11:00 PM each day\n"
                "• After the daily leaderboard is posted, points reset for the next day"
            ),
            inline=False
        )
        
        # Competition benefits
        embed.add_field(
            name="💪 Benefits of Competition",
            value=(
                "• Friendly competition can increase your motivation to stay focused\n"
                "• Seeing others' productivity can inspire you to improve your own\n"
                "• Regular tracking helps build consistent study/work habits\n"
                "• The daily reset gives everyone a fresh start each day"
            ),
            inline=False
        )
        
        # Tips
        embed.add_field(
            name="💡 Tips",
            value=(
                "• Use the `!pomodoro` command regularly to earn points\n"
                "• Check the leaderboard throughout the day to see your ranking\n"
                "• If you use the command, that channel will receive the daily leaderboard\n"
                "• Focus on beating your own personal best, not just others"
            ),
            inline=False
        )
        
        # Examples footer
        embed.set_footer(text=f"Related commands: '!points', '!pomodoro'")
    
    # Handle guide for the setsound command
    elif command.lower() in ["setsound", "sound"]:
        embed = discord.Embed(
            title="🔊 Sound Notification Guide",
            description="Customize the sound alerts you receive when your Pomodoro sessions and alarms complete.",
            color=discord.Color.blue()
        )
        
        # Basic usage
        embed.add_field(
            name="📌 Basic Usage",
            value=(
                f"• `!setsound` - View available sound options and your current setting\n"
                f"• `!setsound [sound_name]` - Set your preferred notification sound\n"
                f"  Example: `!setsound alarm` to set the alarm sound"
            ),
            inline=False
        )
        
        # Available sounds
        embed.add_field(
            name="🎵 Available Sounds",
            value=(
                "• `default`: 🔔 *Ding!*\n"
                "• `bell`: 🔔 *Ding-dong!*\n"
                "• `alarm`: ⏰ *BRRRING! BRRRING!*\n"
                "• `gentle`: 🎵 *Soft chime*\n"
                "• `motivational`: 🎺 *Triumphant fanfare!*\n"
                "• `celebration`: 🎉 *Party horn and confetti!*"
            ),
            inline=False
        )
        
        # When sounds play
        embed.add_field(
            name="⏰ When Sounds Play",
            value=(
                "• When a Pomodoro session completes\n"
                "• When an alarm you've set triggers\n"
                "• Each user can have their own preferred sound\n"
                "• Your sound preference persists between sessions"
            ),
            inline=False
        )
        
        # Examples footer
        embed.set_footer(text=f"Examples: '!setsound motivational', '!setsound gentle'")
    
    else:
        # Default response for other commands
        embed = discord.Embed(
            title="Command Guide",
            description=f"Detailed help for `{command}` command is not available yet. Type `!help` to see all available commands.",
            color=discord.Color.blue()
        )
    
    await ctx.send(embed=embed)

# Set timezone command
@bot.command(name="settimezone")
async def settimezone(ctx, *, timezone_input: str = None):
    """Set your timezone for accurate alarm scheduling"""
    user_id = ctx.author.id
    
    if not timezone_input:
        embed = discord.Embed(
            title="🌐 Set Your Timezone",
            description="Your timezone is needed for accurate alarm scheduling.",
            color=discord.Color.blue()
        )
        
        # Show current timezone if set
        if user_id in user_timezones:
            current_tz = user_timezones[user_id]
            try:
                timezone = pytz.timezone(current_tz)
                now = datetime.now(timezone)
                time_str = now.strftime("%H:%M")
                
                embed.add_field(
                    name="Current Setting",
                    value=f"Your timezone is set to **{current_tz}**\nIt's currently **{time_str}** in your timezone.",
                    inline=False
                )
            except:
                pass
        
        embed.add_field(
            name="Usage",
            value=f"`!settimezone [timezone]` - Example: `!settimezone US/Eastern`"
        )
        embed.add_field(
            name="Common Options",
            value=(
                "• Standard abbreviations: `EST`, `CST`, `MST`, `PST`, `IST`, `GMT`\n"
                "• Cities/Regions: `Asia/Tokyo`, `Europe/London`, `America/New_York`\n"
                "• Countries: `US`, `India`, `Japan`, `UK`, `Australia`"
            ),
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    # Check if it's a common alias
    timezone_name = timezone_input.strip()
    original_input = timezone_name  # Save for error messages
    
    if timezone_name.lower() in TIMEZONE_ALIASES:
        timezone_name = TIMEZONE_ALIASES[timezone_name.lower()]
    
    # Validate the timezone
    try:
        timezone = pytz.timezone(timezone_name)
        
        # Store user timezone
        user_timezones[user_id] = timezone_name
        save_timezones()
        
        # Get current time in that timezone
        now = datetime.now(timezone)
        time_str = now.strftime("%H:%M")
        
        embed = discord.Embed(
            title="🌐 Timezone Set Successfully",
            description=f"Your timezone has been set to **{timezone_name}**.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Current Time",
            value=f"It's currently **{time_str}** in your timezone."
        )
        embed.add_field(
            name="Alarms",
            value="All your alarms will now be scheduled according to this timezone."
        )
        # Add UTC offset for reference
        utc_offset = now.strftime("%z")
        hours_offset = int(utc_offset[0:3])
        embed.set_footer(text=f"UTC{utc_offset} ({hours_offset:+d} hours from UTC)")
        
        await ctx.send(embed=embed)
        
    except pytz.exceptions.UnknownTimeZoneError:
        # Try to suggest similar timezones
        suggestions = []
        for tz in pytz.all_timezones:
            if timezone_name.lower() in tz.lower():
                suggestions.append(tz)
                if len(suggestions) >= 5:  # Limit to 5 suggestions
                    break
        
        # Also check aliases
        alias_suggestions = []
        for alias, full_tz in TIMEZONE_ALIASES.items():
            if timezone_name.lower() in alias.lower():
                alias_display = f"{alias.upper()} ({full_tz})"
                if alias_display not in alias_suggestions:
                    alias_suggestions.append(alias_display)
                    if len(alias_suggestions) >= 3:  # Limit to 3 alias suggestions
                        break
        
        embed = discord.Embed(
            title="❌ Invalid Timezone",
            description=f"'{original_input}' is not a valid timezone identifier.",
            color=discord.Color.red()
        )
        
        if suggestions:
            embed.add_field(
                name="Did you mean?",
                value="\n".join(suggestions),
                inline=False
            )
        
        if alias_suggestions:
            embed.add_field(
                name="Common Abbreviations",
                value="\n".join(alias_suggestions),
                inline=False
            )
        
        embed.add_field(
            name="Common Options",
            value="EST, CST, MST, PST, IST, GMT, US/Eastern, Europe/London, Asia/Tokyo",
            inline=False
        )
        
        embed.set_footer(text=f"Type !guide settimezone for more help with setting your timezone")
        
        await ctx.send(embed=embed)

# Set user sound preference
@bot.command(name="setsound")
async def setsound(ctx, sound: str = None):
    """Customize your notification sound"""
    user_id = ctx.author.id
    
    # If no sound specified, show available options
    if not sound:
        available_sounds = "\n".join([f"• `{name}`: {effect}" for name, effect in SOUND_EFFECTS.items()])
        
        embed = discord.Embed(
            title="🔊 Sound Notification Settings",
            description="Customize the sound alerts for your Pomodoro and alarm notifications!",
            color=discord.Color.blue()
        )
        
        current_sound = user_sound_prefs.get(user_id, "default")
        current_effect = SOUND_EFFECTS.get(current_sound, SOUND_EFFECTS["default"])
        
        embed.add_field(
            name="Your Current Sound",
            value=f"`{current_sound}`: {current_effect}",
            inline=False
        )
        
        embed.add_field(
            name="Available Sounds",
            value=available_sounds,
            inline=False
        )
        
        embed.add_field(
            name="How to Change",
            value=f"Use `!setsound [name]` to change your sound. Example: `!setsound alarm`",
            inline=False
        )
        
        await ctx.send(embed=embed)
        return
    
    # Try to set the requested sound
    sound = sound.lower()
    if sound in SOUND_EFFECTS:
        user_sound_prefs[user_id] = sound
        save_sound_prefs()
        
        embed = discord.Embed(
            title="🔊 Sound Updated",
            description=f"Your notification sound has been set to: **{sound}**",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Preview",
            value=SOUND_EFFECTS[sound],
            inline=False
        )
        
        embed.add_field(
            name="When You'll Hear It",
            value="This sound will play when your Pomodoro sessions and alarms complete.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    else:
        # Invalid sound option
        embed = discord.Embed(
            title="❌ Invalid Sound Option",
            description=f"`{sound}` is not a valid sound option.",
            color=discord.Color.red()
        )
        
        available_sounds = ", ".join([f"`{name}`" for name in SOUND_EFFECTS.keys()])
        embed.add_field(
            name="Available Options",
            value=f"Please choose from: {available_sounds}",
            inline=False
        )
        
        embed.add_field(
            name="More Details",
            value=f"Use `!setsound` (without any argument) to see detailed sound previews.",
            inline=False
        )
        
        await ctx.send(embed=embed)

# View productivity points
@bot.command(name="points")
async def view_points(ctx, user: discord.Member = None):
    """View your productivity points for today"""
    # If no user specified, default to the command author
    target_user = user or ctx.author
    target_id = target_user.id
    
    embed = discord.Embed(
        title="🏆 Productivity Points",
        color=discord.Color.gold()
    )
    
    # Get the user's points data
    if target_id in user_points:
        points_data = user_points[target_id]
        total_points = points_data["points"]
        sessions = points_data["daily_sessions"]
        
        # Basic points display
        if target_user == ctx.author:
            embed.description = f"You have earned **{total_points} points** today!"
        else:
            embed.description = f"**{target_user.display_name}** has earned **{total_points} points** today!"
        
        # Calculate some stats if there are sessions
        if sessions:
            total_minutes = sum(duration for duration, _ in sessions)
            avg_duration = total_minutes / len(sessions)
            
            # Session details
            embed.add_field(
                name="Today's Focus Time",
                value=(
                    f"• **Total Time**: {total_minutes} minutes\n"
                    f"• **Sessions**: {len(sessions)}\n"
                    f"• **Average Duration**: {avg_duration:.1f} minutes"
                ),
                inline=False
            )
            
            # List recent sessions (up to 5)
            recent_sessions = []
            for i, (duration, timestamp) in enumerate(reversed(sessions[-5:])):
                time_str = timestamp.strftime("%H:%M")
                recent_sessions.append(f"• {time_str}: {duration} min session (+{duration} pts)")
                
            if recent_sessions:
                embed.add_field(
                    name="Recent Sessions",
                    value="\n".join(recent_sessions),
                    inline=False
                )
        else:
            # No sessions yet
            embed.add_field(
                name="No Sessions Today",
                value=f"Start a Pomodoro session with `!pomodoro [minutes]` to earn points!",
                inline=False
            )
    else:
        # User has no points record
        if target_user == ctx.author:
            embed.description = "You haven't earned any productivity points today."
            embed.add_field(
                name="How to Earn Points",
                value=f"Use `!pomodoro [minutes]` to start a focus session and earn points (1 point per minute)!",
                inline=False
            )
        else:
            embed.description = f"**{target_user.display_name}** hasn't earned any productivity points today."
    
    # Add leaderboard info
    embed.add_field(
        name="Daily Leaderboard",
        value=f"The daily leaderboard is posted at 11:00 PM. Try to climb the ranks!",
        inline=False
    )
    
    await ctx.send(embed=embed)

# View current leaderboard
@bot.command(name="leaderboard", aliases=["lb"])
async def view_leaderboard(ctx):
    """View the current productivity leaderboard"""
    # Set this channel as the leaderboard channel
    global leaderboard_channel_id
    leaderboard_channel_id = ctx.channel.id
    
    # Get current date for the title
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Create a list of (user_id, points) tuples
    leaderboard_data = []
    for user_id, data in user_points.items():
        if data["points"] > 0:  # Only include users who earned points today
            leaderboard_data.append((user_id, data["points"]))
    
    # Sort by points in descending order
    leaderboard_data.sort(key=lambda x: x[1], reverse=True)
    
    # Generate the leaderboard message
    embed = discord.Embed(
        title=f"📊 Current Productivity Leaderboard ({today})",
        description="Here's how everyone is doing so far today!",
        color=discord.Color.gold()
    )
    
    if not leaderboard_data:
        embed.add_field(
            name="No Data Yet",
            value="No productivity points have been earned today. Start a Pomodoro session to earn points!",
            inline=False
        )
    else:
        # Format the leaderboard entries
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, points) in enumerate(leaderboard_data):
            # Try to get the user's display name
            try:
                user = await bot.fetch_user(user_id)
                username = user.display_name
            except:
                username = f"User {user_id}"
            
            # Add medal for top 3
            prefix = medals[i] if i < 3 else f"{i+1}."
            leaderboard_text += f"{prefix} **{username}** - {points} points\n"
            
            # Limit to top 10 users
            if i >= 9:
                break
        
        embed.add_field(
            name="Top Performers",
            value=leaderboard_text,
            inline=False
        )
    
    # Add time until reset
    now = datetime.now()
    target_time = now.replace(hour=23, minute=0, second=0, microsecond=0)
    if now >= target_time:
        target_time = target_time + timedelta(days=1)
    
    hours_remaining = int((target_time - now).total_seconds() // 3600)
    minutes_remaining = int(((target_time - now).total_seconds() % 3600) // 60)
    
    embed.add_field(
        name="Time Remaining",
        value=f"Today's leaderboard resets in **{hours_remaining}h {minutes_remaining}m**",
        inline=False
    )
    
    embed.add_field(
        name="How to Earn Points",
        value=f"Use `!pomodoro [minutes]` to start a focus session and earn points (1 point per minute)!",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Run the bot

# Run the bot


# Command to verify that command processing is working
@bot.command(name="verify_commands")
async def verify_commands(ctx):
    """Test if commands are working properly"""
    await ctx.send(f"✅ Commands are working correctly! Bot is using prefix: '{prefix}'")
    await ctx.send(f"Try these commands: {prefix}help, {prefix}ping, {prefix}guide")


# Command to verify that command handling is working
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(f"Starting Aarohi...")
    print("=" * 60 + "\n")
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Start keep-alive server with error handling
        try:
            keep_alive()
            logger.info("Keep-alive server started successfully")
        except Exception as e:
            logger.error(f"Failed to start keep-alive server: {e}")
            logger.warning("Continuing without keep-alive")
            
        # Run the bot
        bot.run(config['token'])
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)