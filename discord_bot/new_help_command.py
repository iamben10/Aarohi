# Simple help command using the standard decorator
@bot.command(name="help")
async def help(ctx, command: str = None):
    """Display help for Aarohi's commands"""
    if command is None:
        # Display ONLY the minimal help message exactly as specified
        embed = discord.Embed(
            title="Aarohi Commands",
            description="Hey! I'm Aarohi, here to help you stay productive and have some fun.",
            color=discord.Color.purple()
        )

        # Basic Commands
        embed.add_field(
            name="📌 Basic Commands",
            value=(
                "`!ping` - Check if I'm online\n"
                "`!help` - Display this help message"
            ),
            inline=False
        )

        # Productivity Tools
        embed.add_field(
            name="⏱️ Productivity Tools",
            value=(
                "`!pomodoro` - Start a focus session\n"
                "`!todo` - Manage your to-do list\n"
                "`!alarm` - Set or view alarms\n"
                "`!focus` - Enter distraction-free mode"
            ),
            inline=False
        )

        # Personalization
        embed.add_field(
            name="✨ Personalization",
            value=(
                "`!profile` - View or update your profile\n"
                "`!mood` - Track your emotional state\n"
                "`!resources` - Get helpful resources\n"
                "`!quote` - Get an inspirational quote"
            ),
            inline=False
        )

        # Footer
        embed.set_footer(text="Type !help <command> for more details")

        # Send ONLY this embed, nothing else
        await ctx.send(embed=embed)
        return
    else:
        # Command-specific help (keep your existing code here)
        pass 