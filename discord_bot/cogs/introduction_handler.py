import discord
from discord.ext import commands
import re
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger("discord_bot.introduction_handler")

class IntroductionHandler(commands.Cog):
    """Handles user introductions and starts DM conversations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_intros = {}
        self.load_intros()
        
        # Channel IDs - update these with your actual channel IDs
        self.intro_channel_id = 1353429400460198032  # Introduction channel
        self.aarohi_channel_id = None  # Update this with your "aarohi" channel ID
        
    def cog_unload(self):
        self.save_intros()
    
    def load_intros(self):
        """Load saved user introductions"""
        try:
            if os.path.exists("data/user_intros.json"):
                with open("data/user_intros.json", "r") as f:
                    self.user_intros = json.load(f)
            logger.info("Loaded user introductions")
        except Exception as e:
            logger.error(f"Error loading user introductions: {e}")
            self.user_intros = {}
    
    def save_intros(self):
        """Save user introductions"""
        try:
            os.makedirs("data/", exist_ok=True)
            with open("data/user_intros.json", "w") as f:
                json.dump(self.user_intros, f, indent=4)
            logger.info("Saved user introductions")
        except Exception as e:
            logger.error(f"Error saving user introductions: {e}")
    
    def extract_intro_info(self, content):
        """Extract basic info from introduction message"""
        info = {}
        
        # Try to extract name
        name_match = re.search(r"name(?:'s|\sis)?[:\s]+([A-Za-z0-9_\s]+)", content, re.IGNORECASE)
        if name_match:
            info["name"] = name_match.group(1).strip()
        
        # Try to extract age
        age_match = re.search(r"(?:I'm|I am|age[:\s]+)(?:\s*)(\d+)(?:\s*years old|\s*yo|\s*y\.o\.)?", content, re.IGNORECASE)
        if age_match:
            info["age"] = age_match.group(1)
        
        # Try to extract interests/hobbies
        interests_match = re.search(r"(?:interests|hobbies|like|enjoy|love)[:\s]+(.+?)(?:\.|\n|$)", content, re.IGNORECASE)
        if interests_match:
            info["interests"] = interests_match.group(1).strip()
        
        return info
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages in the intro channel and "done" messages in aarohi channel"""
        # Ignore bot messages
        if message.author.bot:
            return
            
        # IMPORTANT: Skip processing for !help to prevent duplicate outputs
        if message.content.strip().lower() in [f"{self.bot.command_prefix}help", f"{self.bot.command_prefix}help "]:
            return
        
        # Handle intro channel messages
        if message.channel.id == self.intro_channel_id:
            user_id = str(message.author.id)
            intro_info = self.extract_intro_info(message.content)
            
            if intro_info:
                self.user_intros[user_id] = {
                    "content": message.content,
                    "info": intro_info,
                    "timestamp": datetime.now().isoformat()
                }
                self.save_intros()
                logger.info(f"Saved introduction for user {message.author.name}")
        
        # Handle "done" messages in aarohi channel
        if self.aarohi_channel_id and message.channel.id == self.aarohi_channel_id:
            if message.content.lower() == "done":
                user_id = str(message.author.id)
                
                # Check if we have an intro for this user
                if user_id in self.user_intros:
                    # Start a DM conversation
                    await self.start_dm_conversation(message.author)
    
    async def start_dm_conversation(self, user):
        """Start a DM conversation with the user based on their intro"""
        try:
            user_id = str(user.id)
            
            # Get user intro info
            intro_info = self.user_intros.get(user_id, {}).get("info", {})
            
            # Get conversation module for user data
            convo_cog = self.bot.get_cog("Conversation")
            if convo_cog:
                # Update user data with intro info
                if "name" in intro_info:
                    convo_cog.update_user_data(user_id, name=intro_info["name"])
                if "interests" in intro_info:
                    topics = intro_info["interests"].split(",")
                    topics = [topic.strip() for topic in topics]
                    convo_cog.update_user_data(user_id, topics=topics)
            
            # Craft a personalized greeting
            greeting = f"Hey there! I noticed you completed your introduction."
            
            if "name" in intro_info:
                greeting = f"Hey {intro_info['name']}! I noticed you completed your introduction."
            
            greeting += "\n\nI'm your friendly assistant bot! I can help you with:"
            greeting += "\n• Setting up Pomodoro timers for focused work/study"
            greeting += "\n• Managing your to-do lists"
            greeting += "\n• Setting reminders with alarms"
            greeting += "\n• Finding helpful resources on various topics"
            
            if "interests" in intro_info:
                greeting += f"\n\nI see you're interested in {intro_info['interests']}. That's cool! If you need any resources on those topics, just use the `!resources` command."
            
            greeting += "\n\nType `!help` anytime to see all my commands. What can I help you with today?"
            
            # Send the DM
            await user.send(greeting)
            logger.info(f"Started DM conversation with {user.name}")
            
        except discord.Forbidden:
            logger.error(f"Cannot send DM to {user.name} - user has DMs disabled")
        except Exception as e:
            logger.error(f"Error starting DM with {user.name}: {e}")
    
    @commands.command(name="scan_intros")
    @commands.has_permissions(administrator=True)
    async def scan_intros(self, ctx):
        """Admin command to scan introduction channel history"""
        try:
            intro_channel = self.bot.get_channel(self.intro_channel_id)
            if not intro_channel:
                return await ctx.send("Introduction channel not found. Please check the channel ID.")
            
            await ctx.send(f"Scanning message history in {intro_channel.mention}. This may take a while...")
            
            count = 0
            async for message in intro_channel.history(limit=500):  # Adjust limit as needed
                if not message.author.bot:
                    user_id = str(message.author.id)
                    intro_info = self.extract_intro_info(message.content)
                    
                    if intro_info:
                        self.user_intros[user_id] = {
                            "content": message.content,
                            "info": intro_info,
                            "timestamp": message.created_at.isoformat()
                        }
                        count += 1
            
            self.save_intros()
            await ctx.send(f"Scan complete! Processed {count} introductions.")
            
        except Exception as e:
            logger.error(f"Error scanning introductions: {e}")
            await ctx.send(f"Error scanning introductions: {e}")
    
    @commands.command(name="set_aarohi_channel")
    @commands.has_permissions(administrator=True)
    async def set_aarohi_channel(self, ctx, channel_id: int = None):
        """Set the aarohi channel ID"""
        if channel_id is None:
            if ctx.message.channel_mentions:
                channel_id = ctx.message.channel_mentions[0].id
            else:
                return await ctx.send("Please mention a channel or provide a channel ID.")
        
        self.aarohi_channel_id = channel_id
        
        # Save to config
        try:
            with open("data/settings.json", "r") as f:
                settings = json.load(f)
            
            settings["aarohi_channel_id"] = channel_id
            
            with open("data/settings.json", "w") as f:
                json.dump(settings, f, indent=4)
            
            await ctx.send(f"Aarohi channel ID set to {channel_id}")
        except Exception as e:
            logger.error(f"Error saving channel ID: {e}")
            await ctx.send(f"Channel ID set for this session, but couldn't save to settings: {e}")

async def setup(bot):
    await bot.add_cog(IntroductionHandler(bot)) 