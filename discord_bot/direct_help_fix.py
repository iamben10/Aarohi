"""
AAROHI BOT - DIRECT HELP COMMAND FIX
------------------------------------

This script will directly patch main.py to fix the help command,
ensuring that only the clean Aarohi Commands section is displayed.

To use: Simply run this script with Python 3.
"""

import re
import sys
import os
import time

print("=" * 50)
print("AAROHI BOT - DIRECT HELP COMMAND FIX")
print("=" * 50)
print()

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"Working directory: {os.getcwd()}")

# Create backup
try:
    backup_file = "main.py.direct_fix_backup"
    print(f"Creating backup of main.py to {backup_file}...")
    with open("main.py", "r", encoding="utf-8") as src:
        with open(backup_file, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    print("✅ Backup created successfully")
except Exception as e:
    print(f"❌ ERROR creating backup: {e}")
    sys.exit(1)

# Read main.py
try:
    print("Reading main.py...")
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    print("✅ File read successfully")
except Exception as e:
    print(f"❌ ERROR reading main.py: {e}")
    sys.exit(1)

print("\nApplying fixes...\n")

# Fix 1: Ensure help_command=None in bot initialization
print("Fix 1: Setting help_command=None in bot initialization...")
if "help_command=None" in content:
    print("✅ help_command=None already set")
else:
    content = re.sub(
        r'bot\s*=\s*commands\.Bot\(command_prefix=config\[.prefix.\],\s*intents=intents(,|\))',
        r'bot = commands.Bot(command_prefix=config["prefix"], intents=intents, help_command=None\1',
        content
    )
    print("✅ help_command=None added")

# Fix 2: Remove any existing @bot.command(name="help")
print("Fix 2: Removing any existing @bot.command(name=\"help\")...")
help_pattern = r'@bot\.command\(name="help"\).*?async def help\(ctx,.*?return'
help_cmd = re.search(help_pattern, content, re.DOTALL)
if help_cmd:
    content = re.sub(help_pattern, "", content, flags=re.DOTALL)
    print("✅ Existing help command removed")
else:
    print("✅ No existing help command found (already removed)")

# Fix 3: Replace on_message to intercept help commands
print("Fix 3: Adding help interception to on_message...")
on_message_pattern = r'@bot\.event\s*\nasync\s+def\s+on_message\s*\(\s*message\s*\)\s*:'
on_message = re.search(on_message_pattern, content)

help_intercept = """@bot.event
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
                f"`{config['prefix']}ping` - Check if I'm online\\n"
                f"`{config['prefix']}help` - Display this help message"
            ),
            inline=False
        )

        # Productivity Tools
        embed.add_field(
            name="⏱️ Productivity Tools",
            value=(
                f"`{config['prefix']}pomodoro` - Start a focus session\\n"
                f"`{config['prefix']}todo` - Manage your to-do list\\n"
                f"`{config['prefix']}alarm` - Set or view alarms\\n"
                f"`{config['prefix']}focus` - Enter distraction-free mode"
            ),
            inline=False
        )

        # Personalization
        embed.add_field(
            name="✨ Personalization",
            value=(
                f"`{config['prefix']}profile` - View or update your profile\\n"
                f"`{config['prefix']}mood` - Track your emotional state\\n"
                f"`{config['prefix']}resources` - Get helpful resources\\n"
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
    await bot.process_commands(message)"""

if on_message:
    content = re.sub(
        r'@bot\.event\s*\nasync\s+def\s+on_message\s*\(\s*message\s*\)\s*:.*?await bot\.process_commands\(message\)',
        help_intercept,
        content,
        flags=re.DOTALL
    )
    print("✅ on_message handler updated with help interception")
else:
    print("❌ ERROR: on_message handler not found. Please run the RUN_CLEAN_BOT.bat file instead.")
    sys.exit(1)

# Write the modified content back to main.py
try:
    print("\nWriting changes to main.py...")
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main.py updated successfully")
except Exception as e:
    print(f"❌ ERROR writing to main.py: {e}")
    print(f"A backup was created at: {backup_file}")
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ HELP COMMAND FIXED SUCCESSFULLY")
print("=" * 50)
print("\nYour bot's help command is now fixed! When you run the bot,")
print("typing !help will ONLY show the clean Aarohi Commands section.")
print("\nTo run the bot, type: py -3 main.py")
print("\nIf you have any issues, you can restore the backup:")
print(f"copy {backup_file} main.py")
print("\nPress Enter to exit...")
input() 