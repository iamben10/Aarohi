import re
import os

# Path to the productivity.py file
productivity_path = os.path.join("cogs", "productivity.py")
fixed_file_path = os.path.join("cogs", "productivity_fixed.py")

# Read the original file
try:
    with open(productivity_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print("Successfully read the productivity.py file")
except Exception as e:
    with open(productivity_path, 'r', encoding='latin-1', errors='ignore') as f:
        content = f.read()
    print(f"Read file with latin-1 encoding: {e}")

# Find the quote command section
quote_cmd_match = re.search(r'@commands\.command\(name="quote"\).*?async\s+def\s+quote\(self,\s+ctx,.*?\).*?(?=@commands|def\s+\w+\(|\Z)', content, re.DOTALL)

if quote_cmd_match:
    quote_cmd = quote_cmd_match.group(0)
    print("Found the quote command section.")
    
    # Print the current implementation (for debugging)
    print("\nCurrent Implementation:")
    print("-" * 50)
    print(quote_cmd)
    print("-" * 50)
    
    # Create the fixed implementation
    fixed_quote_cmd = '''@commands.command(name="quote")
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
            description=f"**\"{quote_text}\"**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"— {author}")
        
        # Add available categories to the embed if no category was specified or an invalid one was given
        if not category or (category and category.lower() not in quotes):
            categories = ", ".join([f"`{cat}`" for cat in quotes.keys()])
            embed.add_field(name="Available Categories", value=f"Try: {categories}")
            
        # Send a single consolidated response
        await ctx.send(embed=embed)'''
    
    # Replace the old implementation with the new one
    new_content = content.replace(quote_cmd, fixed_quote_cmd)
    
    # Back up the original file
    backup_path = productivity_path + ".bak"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created backup at {backup_path}")
    
    # Write the fixed content
    with open(productivity_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("\nSuccessfully fixed the quote command!")
    print("The command now sends a single consolidated message response.")
else:
    print("Could not find the quote command section.")
    with open("quote_debug.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Saved content to quote_debug.txt for inspection") 