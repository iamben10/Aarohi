import discord
from discord.ext import commands
import random
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("discord_bot.conversation")

class Conversation(commands.Cog):
    """Handles natural conversation with users"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}
        self.load_responses()
        self.load_user_data()
        self.cooldowns = {}
    
    def cog_unload(self):
        self.save_user_data()
    
    def load_responses(self):
        """Load conversation responses from JSON files"""
        try:
            # Create responses directory if it doesn't exist
            os.makedirs("data/responses", exist_ok=True)
            
            # Default responses if files don't exist yet
            self.greetings = ["Hey there!", "Hi!", "Hello!", "What's up?", "How's it going?"]
            self.farewell = ["See you later!", "Bye!", "Take care!", "Catch you later!"]
            self.general_responses = ["Interesting!", "Tell me more.", "I see.", "That's cool!"]
            self.encouragement = ["You got this!", "Keep going!", "You're doing great!"]
            
            # Load responses from files if they exist
            response_files = {
                "greetings.json": "greetings",
                "farewell.json": "farewell",
                "general.json": "general_responses",
                "encouragement.json": "encouragement"
            }
            
            for filename, attr_name in response_files.items():
                file_path = f"data/responses/{filename}"
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        setattr(self, attr_name, json.load(f))
            
            logger.info("Loaded conversation responses")
        except Exception as e:
            logger.error(f"Error loading responses: {e}")
    
    def save_default_responses(self):
        """Save default responses to JSON files"""
        try:
            os.makedirs("data/responses", exist_ok=True)
            
            responses = {
                "greetings.json": self.greetings,
                "farewell.json": self.farewell,
                "general.json": self.general_responses,
                "encouragement.json": self.encouragement
            }
            
            for filename, data in responses.items():
                with open(f"data/responses/{filename}", "w") as f:
                    json.dump(data, f, indent=4)
            
            logger.info("Saved default responses")
        except Exception as e:
            logger.error(f"Error saving default responses: {e}")
    
    def load_user_data(self):
        """Load user interaction data"""
        try:
            if os.path.exists("data/user_data.json"):
                with open("data/user_data.json", "r") as f:
                    self.user_data = json.load(f)
            else:
                self.user_data = {}
            logger.info("Loaded user data")
        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            self.user_data = {}
    
    def save_user_data(self):
        """Save user interaction data"""
        try:
            with open("data/user_data.json", "w") as f:
                json.dump(self.user_data, f, indent=4)
            logger.info("Saved user data")
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
    
    def get_user_data(self, user_id):
        """Get user data, creating it if it doesn't exist"""
        user_id = str(user_id)
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "name": None,
                "mood": "neutral",
                "last_interaction": None,
                "interaction_count": 0,
                "topics": [],
                "relationship_status": None
            }
        return self.user_data[user_id]
    
    def update_user_data(self, user_id, **kwargs):
        """Update user data with new values"""
        user_id = str(user_id)
        user_data = self.get_user_data(user_id)
        
        for key, value in kwargs.items():
            if key in user_data:
                user_data[key] = value
        
        # Update last interaction time
        user_data["last_interaction"] = datetime.now().isoformat()
        user_data["interaction_count"] += 1
        
        self.save_user_data()
    
    def should_respond(self, message):
        """Determine whether to respond to a message"""
        # Always respond to mentions
        if self.bot.user.mentioned_in(message):
            return True
        
        # Check if this is a DM channel
        if isinstance(message.channel, discord.DMChannel):
            return True
        
        # Random chance to respond to messages in servers
        # Higher chance if the user interacts frequently
        user_data = self.get_user_data(message.author.id)
        interaction_bonus = min(0.2, user_data["interaction_count"] / 100)
        
        if random.random() < (0.1 + interaction_bonus):
            return True
        
        return False
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages that aren't commands"""
        # Ignore our own messages
        if message.author.bot or message.content.startswith(self.bot.command_prefix):
            # IMPORTANT: Skip processing for !help to prevent duplicate outputs
            if message.content.strip().lower() in [f"{self.bot.command_prefix}help", f"{self.bot.command_prefix}help "]:
                return
            return
        
        # Check if we should respond
        if not self.should_respond(message):
            return
        
        # Check cooldown
        user_id = message.author.id
        now = datetime.now().timestamp()
        cooldown = self.bot.get_cog('Config').get_setting('conversation_cooldown', 1)
        
        if user_id in self.cooldowns and now - self.cooldowns[user_id] < cooldown:
            return
        
        self.cooldowns[user_id] = now
        
        # Get user data
        user_data = self.get_user_data(user_id)
        
        # Process the message and generate a response
        await self.generate_response(message, user_data)
    
    async def generate_response(self, message, user_data):
        """Generate a response to a message based on its content and user data"""
        content = message.content.lower()
        
        # Check for greetings
        greeting_words = ["hi", "hello", "hey", "howdy", "sup", "what's up", "yo"]
        if any(word in content for word in greeting_words):
            response = random.choice(self.greetings)
            if user_data["name"]:
                response = f"{response} {user_data['name']}!"
            
            await message.channel.send(response)
            return
        
        # Check for farewells
        farewell_words = ["bye", "goodbye", "see ya", "cya", "gtg", "got to go", "later"]
        if any(word in content for word in farewell_words):
            response = random.choice(self.farewell)
            await message.channel.send(response)
            return
        
        # Check for personal questions
        if "who are you" in content or "what are you" in content:
            await message.channel.send(
                "I'm your friendly Discord assistant! I can help with Pomodoro timers, "
                "to-do lists, and keeping you company. What can I help you with today?"
            )
            return
        
        # Check for help words
        help_words = ["help", "can you help", "how do i", "how to"]
        if any(word in content for word in help_words):
            await message.channel.send(
                f"Need help? You can use `{self.bot.command_prefix}help` to see all my commands. "
                f"I can set timers, manage to-do lists, and chat with you!"
            )
            return
        
        # Check for mood indicators
        mood_indicators = {
            "happy": ["happy", "glad", "excited", "joy", "awesome", "great"],
            "sad": ["sad", "upset", "depressed", "unhappy", "miserable"],
            "angry": ["angry", "mad", "furious", "annoyed", "irritated"],
            "tired": ["tired", "exhausted", "sleepy", "fatigued"],
            "stressed": ["stressed", "anxious", "worried", "nervous"]
        }
        
        for mood, indicators in mood_indicators.items():
            if any(word in content for word in indicators):
                user_data["mood"] = mood
                self.update_user_data(message.author.id, mood=mood)
                
                if mood == "happy":
                    await message.channel.send(random.choice([
                        "Glad to hear you're doing well!",
                        "That's awesome! Keep that positive energy going!",
                        "Nice! Good vibes all around!"
                    ]))
                elif mood == "sad":
                    await message.channel.send(random.choice([
                        "Sorry to hear that. Things will get better soon.",
                        "It's okay to feel down sometimes. I'm here if you need someone to talk to.",
                        "Sending you good vibes. Hope you feel better soon!"
                    ]))
                elif mood == "angry":
                    await message.channel.send(random.choice([
                        "Take a deep breath. It helps sometimes.",
                        "I get it, that would frustrate me too.",
                        "Want to talk about what's bothering you?"
                    ]))
                elif mood == "tired":
                    await message.channel.send(random.choice([
                        "Maybe you need a break? A short nap can do wonders.",
                        "Don't forget to rest when you need to!",
                        "Take care of yourself, ok? Rest is important."
                    ]))
                elif mood == "stressed":
                    await message.channel.send(random.choice([
                        "Try some deep breathing exercises, they really help with stress.",
                        "One step at a time. You've got this!",
                        "Maybe a short break would help clear your mind?"
                    ]))
                return
        
        # If nothing specific was detected, send a general response
        await message.channel.send(random.choice(self.general_responses))
    
    @commands.group(name="profile", invoke_without_command=True)
    async def profile(self, ctx):
        """View or update your user profile"""
        user_data = self.get_user_data(ctx.author.id)
        
        embed = discord.Embed(
            title=f"Profile for {ctx.author.display_name}",
            color=discord.Color.blue()
        )
        
        status = user_data["relationship_status"] or "Not set"
        name = user_data["name"] or ctx.author.display_name
        mood = user_data["mood"].capitalize() if user_data["mood"] else "Neutral"
        
        embed.add_field(name="Preferred Name", value=name, inline=True)
        embed.add_field(name="Current Mood", value=mood, inline=True)
        embed.add_field(name="Relationship Status", value=status, inline=True)
        embed.add_field(name="Interactions", value=str(user_data["interaction_count"]), inline=True)
        
        await ctx.send(embed=embed)
    
    @profile.command(name="name")
    async def set_name(self, ctx, *, name: str):
        """Set your preferred name"""
        self.update_user_data(ctx.author.id, name=name)
        await ctx.send(f"I'll call you {name} from now on!")
    
    @profile.command(name="mood")
    async def set_mood(self, ctx, *, mood: str):
        """Set your current mood"""
        self.update_user_data(ctx.author.id, mood=mood.lower())
        await ctx.send(f"I've updated your mood to {mood}.")
    
    @profile.command(name="status")
    async def set_status(self, ctx, *, status: str):
        """Set your relationship status"""
        self.update_user_data(ctx.author.id, relationship_status=status)
        await ctx.send(f"I've updated your relationship status to {status}.")
    
    @commands.command(name="mood")
    async def mood_command(self, ctx, *, emotion: Optional[str] = None):
        """Track your emotional state with visual feedback"""
        user_data = self.get_user_data(ctx.author.id)
        
        # Mood emoji dictionary
        mood_emojis = {
            "happy": "😄",
            "excited": "🤩",
            "content": "😊",
            "grateful": "🙏",
            "calm": "😌",
            "relaxed": "😎",
            "proud": "😏",
            "confident": "💪",
            "loved": "❤️",
            "neutral": "😐",
            "sad": "😢",
            "depressed": "😞",
            "anxious": "😰",
            "stressed": "😫",
            "angry": "😠",
            "frustrated": "😤",
            "overwhelmed": "😩",
            "tired": "😴",
            "bored": "🥱",
            "confused": "🤔"
        }
        
        # Group moods into categories for suggestions
        mood_categories = {
            "positive": ["happy", "excited", "content", "grateful", "calm", "relaxed", "proud", "confident", "loved"],
            "neutral": ["neutral", "bored", "confused"],
            "negative": ["sad", "depressed", "anxious", "stressed", "angry", "frustrated", "overwhelmed", "tired"]
        }
        
        if emotion is None:
            # Display current mood and suggestions
            current_mood = user_data.get("mood", "neutral").lower()
            emoji = mood_emojis.get(current_mood, "😐")
            
            embed = discord.Embed(
                title="Your Current Mood",
                description=f"You're feeling **{current_mood}** {emoji}",
                color=discord.Color.blue()
            )
            
            # Add mood categories with example moods
            for category, moods in mood_categories.items():
                formatted_moods = []
                for m in moods[:5]:  # Limit to 5 examples per category
                    m_emoji = mood_emojis.get(m, "")
                    formatted_moods.append(f"{m_emoji} `{m}`")
                
                embed.add_field(
                    name=f"{category.capitalize()} Moods",
                    value=" ".join(formatted_moods),
                    inline=False
                )
            
            embed.set_footer(text="Usage: !mood <emotion>")
            await ctx.send(embed=embed)
            return
        
        # Setting a new mood
        emotion = emotion.lower()
        if emotion in mood_emojis:
            # Direct match to known emotion
            emoji = mood_emojis[emotion]
        else:
            # Try to find closest match
            closest_match = None
            for mood in mood_emojis.keys():
                if emotion in mood or mood in emotion:
                    closest_match = mood
                    break
            
            if closest_match:
                emotion = closest_match
                emoji = mood_emojis[closest_match]
            else:
                # No match found, use neutral
                emoji = "😐"
        
        # Update the user's mood
        self.update_user_data(ctx.author.id, mood=emotion)
        
        # Determine category for advice
        mood_category = None
        for category, moods in mood_categories.items():
            if emotion in moods:
                mood_category = category
                break
        
        # Create embed with appropriate colors and advice
        if mood_category == "positive":
            color = discord.Color.green()
            advice = [
                "That's wonderful to hear! Keep that positive energy flowing.",
                "Fantastic! Consider journaling about what's going well to reflect on later.",
                "Awesome! This is a great time to tackle challenging tasks while your energy is high.",
                "Great! Maybe share your positive vibes with someone who needs a boost today."
            ]
        elif mood_category == "negative":
            color = discord.Color.red()
            advice = [
                "I'm sorry you're feeling this way. Remember that emotions are temporary.",
                "It's okay to not be okay sometimes. Try some deep breathing exercises.",
                "Consider taking a short break to reset. A quick walk often helps.",
                "Have you tried talking to someone you trust about how you're feeling?",
                "Self-care is important - make sure you're getting enough rest, water, and nutritious food."
            ]
        else:  # neutral
            color = discord.Color.blue()
            advice = [
                "Sometimes a neutral state is the perfect time for reflection.",
                "This might be a good time to plan your next steps without emotional interference.",
                "Consider trying something new today to shift your energy.",
                "Neutral moods are great for focused work or decision-making."
            ]
        
        embed = discord.Embed(
            title="Mood Updated",
            description=f"I've set your mood to **{emotion}** {emoji}",
            color=color
        )
        
        embed.add_field(
            name="Reflection",
            value=random.choice(advice),
            inline=False
        )
        
        # Track mood history if it doesn't exist
        if "mood_history" not in user_data:
            user_data["mood_history"] = []
        
        # Add to mood history (keep last 10)
        mood_entry = {
            "mood": emotion,
            "timestamp": datetime.datetime.now().isoformat()
        }
        user_data["mood_history"].append(mood_entry)
        user_data["mood_history"] = user_data["mood_history"][-10:]  # Keep last 10
        
        # Save the updated user data
        self.update_user_data(ctx.author.id, mood_history=user_data["mood_history"])
        
        await ctx.send(embed=embed)
    
    @commands.command(name="resources")
    async def resources(self, ctx, *, topic: str = None):
        """Get helpful resources on a topic"""
        if not topic:
            await ctx.send("Please specify a topic to get resources for.")
            return
        
        # Store the topic in user data
        user_data = self.get_user_data(ctx.author.id)
        if "topics" not in user_data:
            user_data["topics"] = []
        
        if topic.lower() not in [t.lower() for t in user_data["topics"]]:
            user_data["topics"].append(topic)
            self.update_user_data(ctx.author.id, topics=user_data["topics"])
        
        # Simplified resources (placeholder - would be expanded in a real bot)
        resources = {
            "study": [
                "**Effective Study Techniques**: https://www.coursera.org/articles/study-skills",
                "**Pomodoro Method**: https://todoist.com/productivity-methods/pomodoro-technique"
            ],
            "productivity": [
                "**Getting Things Done (GTD)**: https://gettingthingsdone.com/",
                "**Time Blocking Method**: https://todoist.com/productivity-methods/time-blocking"
            ],
            "motivation": [
                "**Building Better Habits**: https://jamesclear.com/habits",
                "**Finding Motivation**: https://www.mindtools.com/motivation.htm"
            ]
        }
        
        # Find closest match
        topic_lower = topic.lower()
        found = False
        
        for key, links in resources.items():
            if key in topic_lower or topic_lower in key:
                embed = discord.Embed(
                    title=f"Resources for {key.capitalize()}",
                    description="Here are some helpful resources I found for you:",
                    color=discord.Color.green()
                )
                
                for link in links:
                    title, url = link.split(": ")
                    embed.add_field(name=title, value=url, inline=False)
                
                await ctx.send(embed=embed)
                found = True
                break
        
        if not found:
            await ctx.send(
                f"I don't have specific resources for '{topic}' yet. "
                f"I'll make a note of it and try to find some for next time!"
            )

    @commands.command(name="guide")
    async def guide_command(self, ctx, command: str = None):
        """Alternative detailed guide to Aarohi's commands"""
        if command is None:
            # Show message about using !help instead
            embed = discord.Embed(
                title="📚 Aarohi Guide",
                description="For a quick overview of commands, use `!help`.\nThis guide provides more detailed information about specific commands.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="How to use this guide",
                value="Type `!guide <command>` to get detailed help with any command.\nExample: `!guide todo`",
                inline=False
            )
            
            popular_commands = [
                "todo", "pomodoro", "alarm", "focus", 
                "profile", "mood", "resources", "quote"
            ]
            
            embed.add_field(
                name="Popular Commands",
                value=", ".join([f"`{cmd}`" for cmd in popular_commands]),
                inline=False
            )
            
            embed.set_footer(text="For basic help, use !help")
            
            await ctx.send(embed=embed)
        else:
            # Existing code for command-specific help
            cmd_lower = command.lower().strip("!")
            
            help_details = {
                "ping": {
                    "title": "!ping Command",
                    "description": "A simple command to check if Aarohi is online and responsive.",
                    "usage": "!ping",
                    "examples": ["!ping"],
                    "tips": "The response time indicates network latency."
                },
                "profile": {
                    "title": "!profile Command",
                    "description": "View and manage your personal profile settings.",
                    "usage": "!profile [subcommand] [value]",
                    "examples": [
                        "!profile - View your profile",
                        "!profile name John - Set your preferred name",
                        "!profile mood happy - Update your mood",
                        "!profile status busy - Set your status"
                    ],
                    "tips": "Your profile helps Aarohi personalize interactions with you."
                },
                "todo": {
                    "title": "!todo Command",
                    "description": "A personal task manager to keep track of your to-do list.",
                    "usage": "!todo [subcommand] [task]",
                    "examples": [
                        "!todo - View your current tasks",
                        "!todo add Buy groceries - Add a new task",
                        "!todo complete 1 - Mark task #1 as completed",
                        "!todo clear - Remove all completed tasks"
                    ],
                    "tips": "Stay organized by breaking down big tasks into smaller ones."
                },
                "pomodoro": {
                    "title": "!pomodoro Command",
                    "description": "Start a Pomodoro timer for focused work sessions.",
                    "usage": "!pomodoro [subcommand] [minutes]",
                    "examples": [
                        "!pomodoro - Start a 25-minute focus session",
                        "!pomodoro start 45 - Start a 45-minute session",
                        "!pomodoro check - See remaining time",
                        "!pomodoro cancel - Stop the current session"
                    ],
                    "tips": "The Pomodoro Technique suggests 25 min work periods followed by 5 min breaks."
                },
                "resources": {
                    "title": "!resources Command",
                    "description": "Get helpful links and information on various topics.",
                    "usage": "!resources <topic>",
                    "examples": [
                        "!resources study",
                        "!resources productivity",
                        "!resources motivation"
                    ],
                    "tips": "Aarohi remembers your interests and can suggest related resources."
                },
                "alarm": {
                    "title": "!alarm Command", 
                    "description": "Set alarms and reminders for important events.",
                    "usage": "!alarm [subcommand] [time] [message]",
                    "examples": [
                        "!alarm - List your current alarms",
                        "!alarm set 15:30 Team meeting - Set an alarm for 3:30 PM",
                        "!alarm clear - Remove all alarms"
                    ],
                    "tips": "Time should be in 24-hour format or include AM/PM."
                },
                "mood": {
                    "title": "!mood Command",
                    "description": "Track your emotional state over time.",
                    "usage": "!mood [emotion]",
                    "examples": [
                        "!mood happy", 
                        "!mood stressed",
                        "!mood tired"
                    ],
                    "tips": "Monitoring your mood patterns can help improve emotional awareness."
                },
                "focus": {
                    "title": "!focus Command",
                    "description": "Toggle do-not-disturb mode for deep work sessions.",
                    "usage": "!focus [minutes]",
                    "examples": [
                        "!focus - Toggle focus mode on/off",
                        "!focus 60 - Enable focus mode for 60 minutes"
                    ],
                    "tips": "Minimizing distractions can greatly improve your productivity."
                },
                "quote": {
                    "title": "!quote Command",
                    "description": "Get an inspirational quote to motivate you.",
                    "usage": "!quote [category]",
                    "examples": [
                        "!quote",
                        "!quote motivation",
                        "!quote success"
                    ],
                    "tips": "A positive quote can help shift your mindset when you're feeling stuck."
                }
            }
            
            if cmd_lower in help_details:
                details = help_details[cmd_lower]
                embed = discord.Embed(
                    title=details["title"],
                    description=details["description"],
                    color=discord.Color.blue()
                )
                
                embed.add_field(name="Usage", value=details["usage"], inline=False)
                
                examples = "\n".join(details["examples"])
                embed.add_field(name="Examples", value=examples, inline=False)
                
                embed.add_field(name="Pro Tip", value=details["tips"], inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"I don't have specific help for `{command}`. Try `!guide` to see all available commands.")

async def setup(bot):
    await bot.add_cog(Conversation(bot))
    
    # Create default response files if they don't exist
    convo_cog = bot.get_cog("Conversation")
    if convo_cog:
        convo_cog.save_default_responses() 