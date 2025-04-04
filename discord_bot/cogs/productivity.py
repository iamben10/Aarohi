import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import datetime
from typing import Dict, List, Optional
import logging
import random

logger = logging.getLogger("discord_bot.productivity")

class Productivity(commands.Cog):
    """Productivity tools including Pomodoro timer, alarms, and to-do lists"""
    
    def __init__(self, bot):
        self.bot = bot
        self.pomodoro_sessions = {}  # User ID: {end_time, channel_id, message}
        self.alarms = {}  # User ID: List of {time, message, channel_id}
        self.check_timers.start()
        self.load_todo_lists()
        
    def cog_unload(self):
        self.check_timers.cancel()
        self.save_todo_lists()
    
    # --- Pomodoro Commands ---
    
    @commands.group(name="pomodoro", aliases=["pomo"], invoke_without_command=True)
    async def pomodoro(self, ctx):
        """Start a Pomodoro session or check your current session"""
        # Default to 25 minutes if no subcommand provided
        await self.start_pomodoro(ctx, 25)
    
    @pomodoro.command(name="start")
    async def start_pomodoro(self, ctx, minutes: int = 25):
        """Start a Pomodoro timer for specified minutes (default: 25)"""
        if ctx.author.id in self.pomodoro_sessions:
            return await ctx.send("You already have a Pomodoro session running! Use `!pomodoro check` to see status.")
        
        if minutes <= 0 or minutes > 120:
            return await ctx.send("Please choose a time between 1 and 120 minutes.")
        
        end_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        
        # Create a motivational message
        message = await ctx.send(
            f"🍅 **Pomodoro started!** You're focusing for {minutes} minutes.\n"
            f"Keep working hard! I'll remind you when it's time for a break."
        )
        
        # Store the session
        self.pomodoro_sessions[ctx.author.id] = {
            "end_time": end_time,
            "channel_id": ctx.channel.id,
            "minutes": minutes,
            "message": message
        }
        logger.info(f"Started Pomodoro session for {ctx.author} ({minutes} minutes)")
    
    @pomodoro.command(name="check")
    async def check_pomodoro(self, ctx):
        """Check the status of your current Pomodoro session"""
        if ctx.author.id not in self.pomodoro_sessions:
            return await ctx.send("You don't have an active Pomodoro session. Start one with `!pomodoro start`!")
        
        session = self.pomodoro_sessions[ctx.author.id]
        time_left = session["end_time"] - datetime.datetime.now()
        minutes_left = max(0, int(time_left.total_seconds() // 60))
        seconds_left = max(0, int(time_left.total_seconds() % 60))
        
        await ctx.send(
            f"⏱️ You have {minutes_left}m {seconds_left}s left in your Pomodoro session.\n"
            f"Keep focusing! You're doing great!"
        )
    
    @pomodoro.command(name="cancel")
    async def cancel_pomodoro(self, ctx):
        """Cancel your current Pomodoro session"""
        if ctx.author.id not in self.pomodoro_sessions:
            return await ctx.send("You don't have an active Pomodoro session.")
        
        del self.pomodoro_sessions[ctx.author.id]
        await ctx.send("Pomodoro session canceled. Ready to start again when you are!")
        logger.info(f"Canceled Pomodoro session for {ctx.author}")

    # --- Alarm Commands ---
    
    @commands.group(name="alarm", invoke_without_command=True)
    async def alarm(self, ctx):
        """Set an alarm or view your current alarms"""
        # Default to listing alarms if no subcommand provided
        await self.list_alarms(ctx)
    
    @alarm.command(name="set")
    async def set_alarm(self, ctx, time_str: str, *, message: Optional[str] = "Your alarm is ringing!"):
        """Set an alarm - format: HH:MM or HH:MM AM/PM"""
        try:
            # Parse the time string
            if "am" in time_str.lower() or "pm" in time_str.lower():
                alarm_time = datetime.datetime.strptime(time_str, "%I:%M %p").time()
            else:
                alarm_time = datetime.datetime.strptime(time_str, "%H:%M").time()
            
            # Calculate when the alarm should go off
            now = datetime.datetime.now()
            alarm_datetime = datetime.datetime.combine(now.date(), alarm_time)
            
            # If the alarm time is earlier today, schedule it for tomorrow
            if alarm_datetime < now:
                alarm_datetime += datetime.timedelta(days=1)
            
            # Add the alarm to the user's alarms
            if ctx.author.id not in self.alarms:
                self.alarms[ctx.author.id] = []
            
            self.alarms[ctx.author.id].append({
                "time": alarm_datetime,
                "message": message,
                "channel_id": ctx.channel.id
            })
            
            # Format time for display
            formatted_time = alarm_datetime.strftime("%I:%M %p")
            time_until = alarm_datetime - now
            hours, remainder = divmod(int(time_until.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            await ctx.send(
                f"⏰ Alarm set for **{formatted_time}** ({hours}h {minutes}m from now).\n"
                f"I'll remind you with: \"{message}\""
            )
            logger.info(f"Set alarm for {ctx.author} at {formatted_time}")
            
        except ValueError:
            await ctx.send("Please use the format `HH:MM` or `HH:MM AM/PM` for the time.")
    
    @alarm.command(name="list")
    async def list_alarms(self, ctx):
        """List all your active alarms"""
        if ctx.author.id not in self.alarms or not self.alarms[ctx.author.id]:
            return await ctx.send("You don't have any active alarms.")
        
        embed = discord.Embed(
            title="Your Active Alarms",
            color=discord.Color.blue()
        )
        
        for i, alarm in enumerate(self.alarms[ctx.author.id], 1):
            time_str = alarm["time"].strftime("%I:%M %p")
            embed.add_field(
                name=f"Alarm #{i} - {time_str}",
                value=alarm["message"],
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @alarm.command(name="clear")
    async def clear_alarms(self, ctx, alarm_number: Optional[int] = None):
        """Clear all alarms or a specific one by number"""
        if ctx.author.id not in self.alarms or not self.alarms[ctx.author.id]:
            return await ctx.send("You don't have any active alarms.")
        
        if alarm_number is None:
            self.alarms[ctx.author.id] = []
            await ctx.send("All your alarms have been cleared.")
            logger.info(f"Cleared all alarms for {ctx.author}")
        else:
            try:
                if 1 <= alarm_number <= len(self.alarms[ctx.author.id]):
                    del self.alarms[ctx.author.id][alarm_number - 1]
                    await ctx.send(f"Alarm #{alarm_number} has been cleared.")
                    logger.info(f"Cleared alarm #{alarm_number} for {ctx.author}")
                else:
                    await ctx.send(f"Please specify a valid alarm number between 1 and {len(self.alarms[ctx.author.id])}.")
            except (ValueError, IndexError):
                await ctx.send("Please specify a valid alarm number.")
    
    # --- Todo List Commands ---
    
    def load_todo_lists(self):
        """Load todo lists from JSON file"""
        self.todo_lists = {}
        
        try:
            if os.path.exists("data/todo_lists.json"):
                with open("data/todo_lists.json", "r") as f:
                    self.todo_lists = json.load(f)
            logger.info("Todo lists loaded successfully")
        except Exception as e:
            logger.error(f"Error loading todo lists: {e}")
            self.todo_lists = {}
    
    def save_todo_lists(self):
        """Save todo lists to JSON file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/todo_lists.json", "w") as f:
                json.dump(self.todo_lists, f)
            logger.info("Todo lists saved successfully")
        except Exception as e:
            logger.error(f"Error saving todo lists: {e}")
    
    @commands.group(name="todo", invoke_without_command=True)
    async def todo(self, ctx):
        """Manage your to-do list"""
        await self.list_todos(ctx)
    
    @todo.command(name="add")
    async def add_todo(self, ctx, *, task: str):
        """Add a task to your to-do list"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.todo_lists:
            self.todo_lists[user_id] = []
        
        # Add the task with timestamp
        task_entry = {
            "task": task,
            "completed": False,
            "created_at": datetime.datetime.now().isoformat(),
            "completed_at": None
        }
        
        self.todo_lists[user_id].append(task_entry)
        self.save_todo_lists()
        
        await ctx.send(f"📝 Added to your to-do list: **{task}**")
        logger.info(f"Added todo item for {ctx.author}: {task}")
    
    @todo.command(name="list")
    async def list_todos(self, ctx):
        """List all tasks in your to-do list"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.todo_lists or not self.todo_lists[user_id]:
            return await ctx.send("Your to-do list is empty! Add tasks with `!todo add <task>`.")
        
        embed = discord.Embed(
            title="Your To-Do List",
            color=discord.Color.green()
        )
        
        incomplete_tasks = []
        completed_tasks = []
        
        for i, task in enumerate(self.todo_lists[user_id], 1):
            status = "✅" if task["completed"] else "⬜"
            task_text = f"{status} **{i}.** {task['task']}"
            
            if task["completed"]:
                completed_tasks.append(task_text)
            else:
                incomplete_tasks.append(task_text)
        
        if incomplete_tasks:
            embed.add_field(
                name="Tasks To Do",
                value="\n".join(incomplete_tasks),
                inline=False
            )
        
        if completed_tasks:
            embed.add_field(
                name="Completed Tasks",
                value="\n".join(completed_tasks),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @todo.command(name="complete")
    async def complete_todo(self, ctx, task_number: int):
        """Mark a task as completed"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.todo_lists or not self.todo_lists[user_id]:
            return await ctx.send("Your to-do list is empty!")
        
        # Check if task number is valid
        if task_number < 1 or task_number > len(self.todo_lists[user_id]):
            return await ctx.send(f"Invalid task number. You have {len(self.todo_lists[user_id])} tasks.")
        
        # Mark task as completed
        task = self.todo_lists[user_id][task_number - 1]
        
        # Remove task from the list
        self.todo_lists[user_id].pop(task_number - 1)
        self.save_todo_lists()
        
        await ctx.send(f"Task completed: {task}")
        
        # If this was the last task, congratulate the user
        if not self.todo_lists[user_id]:
            await ctx.send("🎉 All tasks completed! Great job! 🎉")
            
    @todo.command(name="delete")
    async def delete_todo(self, ctx, task_number: int):
        """Delete a task from your to-do list"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.todo_lists or not self.todo_lists[user_id]:
            return await ctx.send("Your to-do list is empty!")
        
        try:
            if 1 <= task_number <= len(self.todo_lists[user_id]):
                task = self.todo_lists[user_id][task_number - 1]["task"]
                del self.todo_lists[user_id][task_number - 1]
                self.save_todo_lists()
                await ctx.send(f"🗑️ Deleted task #{task_number}: **{task}**")
                logger.info(f"Deleted todo item #{task_number} for {ctx.author}")
            else:
                await ctx.send(f"Please specify a valid task number between 1 and {len(self.todo_lists[user_id])}.")
        except (ValueError, IndexError):
            await ctx.send("Please specify a valid task number.")
    
    @todo.command(name="clear")
    async def clear_todos(self, ctx, completed_only: bool = False):
        """Clear all tasks from your to-do list or just completed ones"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.todo_lists or not self.todo_lists[user_id]:
            return await ctx.send("Your to-do list is already empty!")
        
        if completed_only:
            original_length = len(self.todo_lists[user_id])
            self.todo_lists[user_id] = [task for task in self.todo_lists[user_id] if not task["completed"]]
            removed = original_length - len(self.todo_lists[user_id])
            await ctx.send(f"🧹 Cleared {removed} completed tasks from your to-do list.")
            logger.info(f"Cleared {removed} completed todo items for {ctx.author}")
        else:
            self.todo_lists[user_id] = []
            await ctx.send("🧹 Cleared all tasks from your to-do list.")
            logger.info(f"Cleared all todo items for {ctx.author}")
        
        self.save_todo_lists()
    
    # --- Timer Checking Task ---
    
    @tasks.loop(seconds=10)
    async def check_timers(self):
        """Check for completed Pomodoro sessions and alarms"""
        now = datetime.datetime.now()
        
        # Check Pomodoro sessions
        for user_id, session in list(self.pomodoro_sessions.items()):
            if now >= session["end_time"]:
                try:
                    channel = self.bot.get_channel(session["channel_id"])
                    if channel:
                        user = self.bot.get_user(user_id)
                        await channel.send(
                            f"🍅 **Time's up, {user.mention}!** Your {session['minutes']} minute Pomodoro session is complete.\n"
                            f"Good job! Take a short break and then start another session with `!pomodoro start`."
                        )
                    del self.pomodoro_sessions[user_id]
                    logger.info(f"Completed Pomodoro session for user {user_id}")
                except Exception as e:
                    logger.error(f"Error notifying Pomodoro completion: {e}")
                    continue
        
        # Check alarms
        for user_id, user_alarms in list(self.alarms.items()):
            for alarm in user_alarms[:]:
                if now >= alarm["time"]:
                    try:
                        channel = self.bot.get_channel(alarm["channel_id"])
                        if channel:
                            user = self.bot.get_user(int(user_id))
                            await channel.send(
                                f"⏰ **ALARM, {user.mention}!** {alarm['message']}"
                            )
                        self.alarms[user_id].remove(alarm)
                        logger.info(f"Triggered alarm for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error notifying alarm: {e}")
                        continue
    
    @check_timers.before_loop
    async def before_check_timers(self):
        await self.bot.wait_until_ready()

    @commands.group(name="focus", invoke_without_command=True)
    async def focus(self, ctx, minutes: Optional[int] = 0):
        """Enter focus mode to avoid distractions"""
        user_id = str(ctx.author.id)
        
        # If user has active focus session
        if hasattr(self, 'focus_sessions') and user_id in self.focus_sessions:
            # Check if session is still active
            end_time = self.focus_sessions[user_id]['end_time']
            if datetime.datetime.now() < end_time:
                time_left = end_time - datetime.datetime.now()
                minutes_left = int(time_left.total_seconds() / 60)
                seconds_left = int(time_left.total_seconds() % 60)
                
                embed = discord.Embed(
                    title="🧠 Focus Mode Active",
                    description="You're currently in focus mode!",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Time Remaining", 
                    value=f"{minutes_left}m {seconds_left}s", 
                    inline=False
                )
                embed.add_field(
                    name="To End Early", 
                    value="Use `!focus end` to end your focus session", 
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            else:
                # Session expired, remove it
                del self.focus_sessions[user_id]
        
        # Initialize focus_sessions if not exists
        if not hasattr(self, 'focus_sessions'):
            self.focus_sessions = {}
        
        # If minutes provided, start a timed focus session
        if minutes > 0:
            if minutes > 180:
                await ctx.send("Focus sessions can be at most 3 hours (180 minutes). Setting to 180 minutes.")
                minutes = 180
                
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            self.focus_sessions[user_id] = {
                'end_time': end_time,
                'channel_id': ctx.channel.id
            }
            
            # Create visually appealing embed
            embed = discord.Embed(
                title="🧠 Focus Mode Activated",
                description=f"You're now in focus mode for {minutes} minutes!",
                color=discord.Color.blue()
            )
            
            tips = [
                "Close all distracting apps and websites",
                "Put your phone on silent or in another room",
                "Stay hydrated - keep water nearby",
                "Have clear goals for this focus session",
                "Take deep breaths if you feel distracted"
            ]
            
            embed.add_field(
                name="Focus Tips", 
                value=random.choice(tips), 
                inline=False
            )
            
            embed.add_field(
                name="End Time", 
                value=f"<t:{int(end_time.timestamp())}:t>", 
                inline=True
            )
            
            embed.add_field(
                name="To End Early", 
                value="Use `!focus end` to end your focus session", 
                inline=True
            )
            
            await ctx.send(embed=embed)
            
            # Schedule task to notify when focus time ends
            self.bot.loop.create_task(self.focus_timer(ctx.author.id, ctx.channel.id, minutes))
        else:
            # Toggle focus mode on/off
            await ctx.send(
                "To enter focus mode, specify the number of minutes: `!focus 30`\n"
                "For suggestions on different focus durations:\n"
                "- Quick focus: `!focus 15`\n"
                "- Standard Pomodoro: `!focus 25`\n"
                "- Extended session: `!focus 45`\n"
                "- Deep work: `!focus 90`"
            )
    
    @focus.command(name="end")
    async def end_focus(self, ctx):
        """End a focus session early"""
        user_id = str(ctx.author.id)
        
        if not hasattr(self, 'focus_sessions') or user_id not in self.focus_sessions:
            await ctx.send("You don't have an active focus session.")
            return
            
        del self.focus_sessions[user_id]
        
        # Create embed for ending focus session
        embed = discord.Embed(
            title="Focus Session Ended",
            description="Your focus session has ended. Well done for the time you stayed focused!",
            color=discord.Color.green()
        )
        
        # Add a reflection prompt
        reflection_prompts = [
            "What did you accomplish during this session?",
            "Did you encounter any distractions? How did you handle them?",
            "What could help you stay more focused next time?",
            "How do you feel after this focused work time?"
        ]
        
        embed.add_field(
            name="Reflect on Your Session", 
            value=random.choice(reflection_prompts), 
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def focus_timer(self, user_id, channel_id, minutes):
        """Timer for focus sessions"""
        user_id = str(user_id)
        await asyncio.sleep(minutes * 60)
        
        # Check if session still exists (wasn't ended early)
        if hasattr(self, 'focus_sessions') and user_id in self.focus_sessions:
            del self.focus_sessions[user_id]
            
            channel = self.bot.get_channel(channel_id)
            if channel:
                user = await self.bot.fetch_user(int(user_id))
                
                embed = discord.Embed(
                    title="Focus Session Complete! 🎉",
                    description=f"{user.mention} Your {minutes}-minute focus session is complete!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="Time to Recharge", 
                    value="Take a 5-minute break before your next session. Stretch, grab water, or rest your eyes.", 
                    inline=False
                )
                
                await channel.send(embed=embed)
                
    @commands.command(name="quote")
    async def quote(self, ctx, category: Optional[str] = None):
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
            description=f"**"{quote_text}"**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"— {author}")
        
        # Add available categories to the embed if no category was specified or an invalid one was given
        if not category or (category and category.lower() not in quotes):
            categories = ", ".join([f"`{cat}`" for cat in quotes.keys()])
            embed.add_field(name="Available Categories", value=f"Try: {categories}")
            
        # Send a single consolidated response
        await ctx.send(embed=embed)def setup(bot):
    await bot.add_cog(Productivity(bot)) 