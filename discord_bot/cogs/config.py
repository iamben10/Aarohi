import discord
from discord.ext import commands
import json
import os
import logging

logger = logging.getLogger("discord_bot.config")

class Config(commands.Cog):
    """Bot configuration commands and settings"""
    
    def __init__(self, bot):
        self.bot = bot
        self.settings = {}
        self.load_settings()
    
    def cog_unload(self):
        self.save_settings()
    
    def load_settings(self):
        """Load settings from JSON file"""
        try:
            if os.path.exists("data/settings.json"):
                with open("data/settings.json", "r") as f:
                    self.settings = json.load(f)
            else:
                # Default settings
                self.settings = {
                    "conversation_cooldown": 1,  # seconds
                    "respond_chance": 10,  # percentage
                    "dm_respond_chance": 100,  # percentage
                    "mention_respond_chance": 100,  # percentage
                }
                self.save_settings()
            logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            # Set defaults if loading fails
            self.settings = {
                "conversation_cooldown": 1,
                "respond_chance": 10,
                "dm_respond_chance": 100,
                "mention_respond_chance": 100,
            }
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get_setting(self, key, default=None):
        """Get a setting value with optional default"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """Set a setting value"""
        self.settings[key] = value
        self.save_settings()
    
    @commands.group(name="config", aliases=["settings"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        """View or change bot configuration"""
        embed = discord.Embed(
            title="Bot Configuration",
            description="Use `!config set <key> <value>` to change settings.",
            color=discord.Color.blue()
        )
        
        for key, value in self.settings.items():
            embed.add_field(name=key, value=str(value), inline=True)
        
        await ctx.send(embed=embed)
    
    @config.command(name="set")
    @commands.has_permissions(administrator=True)
    async def set_config(self, ctx, key: str, *, value: str):
        """Set a configuration value"""
        if key not in self.settings:
            await ctx.send(f"Unknown setting: {key}")
            return
        
        # Convert value to appropriate type
        try:
            # Try to convert to number if it's numeric
            if value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") < 2:
                value = float(value)
            # Convert boolean strings
            elif value.lower() in ["true", "yes", "on"]:
                value = True
            elif value.lower() in ["false", "no", "off"]:
                value = False
        except ValueError:
            # Keep as string if conversion fails
            pass
        
        self.set_setting(key, value)
        await ctx.send(f"Setting `{key}` updated to `{value}`")
        logger.info(f"Setting {key} updated to {value} by {ctx.author}")
    
    @config.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_config(self, ctx, key: str = None):
        """Reset configuration to defaults"""
        default_settings = {
            "conversation_cooldown": 1,
            "respond_chance": 10,
            "dm_respond_chance": 100,
            "mention_respond_chance": 100,
        }
        
        if key:
            if key not in default_settings:
                await ctx.send(f"Unknown setting: {key}")
                return
            
            self.set_setting(key, default_settings[key])
            await ctx.send(f"Reset `{key}` to default value: `{default_settings[key]}`")
        else:
            self.settings = default_settings.copy()
            self.save_settings()
            await ctx.send("All settings reset to default values.")
        
        logger.info(f"Settings reset by {ctx.author}")

async def setup(bot):
    await bot.add_cog(Config(bot)) 