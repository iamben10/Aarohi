"""
Simplified robust command handler for Aarohi Discord bot
"""

import logging
import traceback
import sys
from discord.ext import commands

# Setup logger
logger = logging.getLogger(__name__)

def inject_robust_command_handling(bot):
    """Inject robust command handling into the bot"""
    logger.info("Registering robust command error handler")
    
    # Define error handler
    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors gracefully"""
        command_name = ctx.command.name if ctx.command else "Unknown"
        
        # Log the error
        logger.error(f"Command '{command_name}' failed: {error}")
        
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Sorry, I don't recognize that command. Try `!help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}. Try `!help {command_name}` for usage information.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument provided. Try `!help {command_name}` for usage information.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I don't have the necessary permissions to execute this command.")
        else:
            # For other errors, provide a generic message
            await ctx.send("An error occurred while processing your command. The bot administrator has been notified.")
            
            # Print detailed error information to console
            print(f"Error in command {command_name}:", file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    
    # Ensure the bot processes commands
    @bot.event
    async def on_message(message):
        await bot.process_commands(message)
    
    # Return a dummy handler object for compatibility
    class DummyHandler:
        pass
    
    return DummyHandler()
