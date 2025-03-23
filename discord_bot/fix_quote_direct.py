import os

# Let's add the quote command directly to the standalone_bot.py
standalone_bot_path = "standalone_bot.py"

# First, make a backup
with open(standalone_bot_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
# Make a backup
backup_path = standalone_bot_path + ".bak"
if not os.path.exists(backup_path):
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup at {backup_path}")

# Find where to insert the quote command - before the "Run the bot" section
if "# Run the bot" in content:
    insert_position = content.find("# Run the bot")
    
    # Create the quote command
    quote_cmd = '''
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
        
    # Send a single consolidated response
    await ctx.send(embed=embed)
'''
    
    # Insert the quote command
    new_content = content[:insert_position] + quote_cmd + content[insert_position:]
    
    # Write the updated content
    with open(standalone_bot_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("\nSuccessfully added the quote command to standalone_bot.py!")
    print("The command now sends a single consolidated message response.")
else:
    print("Could not find the proper location to insert the quote command.")
    print("Please add the quote command manually.") 